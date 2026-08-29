"""Tests for campaigns and their membership rules."""

import pytest

from website.models import Campaign, CampaignMembership, CampaignRole, MembershipStatus


def signup(client, code, username, password="correcthorsebattery"):
    return client.post(
        "/sign-up",
        data={
            "username": username,
            "password": password,
            "confPassword": password,
            "accessCode": code,
        },
        follow_redirects=True,
    )


def login(client, username, password="correcthorsebattery"):
    return client.post(
        "/login", data={"username": username, "password": password}, follow_redirects=True
    )


def create_campaign(client, name="Borbarads Erben", description="A dark ritual"):
    return client.post(
        "/campaigns", data={"name": name, "description": description}, follow_redirects=True
    )


@pytest.fixture()
def gm_and_player(client, access_code):
    """bob exists; alice is logged in and owns one campaign."""
    signup(client, access_code, "bob")
    client.get("/logout")
    signup(client, access_code, "alice")
    create_campaign(client)
    return client


def test_campaigns_page_requires_login(client):
    assert client.get("/campaigns").status_code == 302


def test_create_makes_the_creator_game_master(client, access_code):
    signup(client, access_code, "alice")
    r = create_campaign(client)
    assert b"Borbarads Erben" in r.data

    campaign = Campaign.query.one()
    membership = campaign.membership_of(campaign.owner_id)
    assert membership.role == CampaignRole.GAME_MASTER
    assert membership.status == MembershipStatus.ACTIVE
    assert campaign.is_game_master(campaign.owner_id)


def test_create_requires_a_name(client, access_code):
    signup(client, access_code, "alice")
    r = client.post("/campaigns", data={"name": "  "}, follow_redirects=True)
    assert b"needs a name" in r.data
    assert Campaign.query.count() == 0


def test_create_rejects_an_overlong_name(client, access_code):
    signup(client, access_code, "alice")
    r = client.post("/campaigns", data={"name": "x" * 101}, follow_redirects=True)
    assert b"at most 100 characters" in r.data
    assert Campaign.query.count() == 0


def test_invite_accept_flow(gm_and_player, client):
    campaign = Campaign.query.one()
    r = client.post(
        f"/campaigns/{campaign.id}/invite", data={"username": "bob"}, follow_redirects=True
    )
    assert b"Invited bob" in r.data

    client.get("/logout")
    login(client, "bob")
    r = client.get("/campaigns")
    assert b"Invitations" in r.data and b"Borbarads Erben" in r.data

    r = client.post(f"/campaigns/{campaign.id}/accept", follow_redirects=True)
    assert b"You joined" in r.data

    membership = CampaignMembership.query.filter_by(campaign_id=campaign.id).all()
    assert len(membership) == 2
    assert all(m.status == MembershipStatus.ACTIVE for m in membership)


def test_invited_user_can_see_the_campaign_before_joining(gm_and_player, client):
    campaign = Campaign.query.one()
    client.post(f"/campaigns/{campaign.id}/invite", data={"username": "bob"})
    client.get("/logout")
    login(client, "bob")

    r = client.get(f"/campaigns/{campaign.id}")
    assert r.status_code == 200
    assert b"invited you to this campaign" in r.data


def test_outsiders_cannot_see_a_campaign(gm_and_player, client, access_code):
    campaign = Campaign.query.one()
    client.get("/logout")
    signup(client, access_code, "mallory")
    assert client.get(f"/campaigns/{campaign.id}").status_code == 404


def test_only_the_game_master_can_invite(gm_and_player, client):
    campaign = Campaign.query.one()
    client.post(f"/campaigns/{campaign.id}/invite", data={"username": "bob"})
    client.get("/logout")
    login(client, "bob")
    client.post(f"/campaigns/{campaign.id}/accept")

    r = client.post(f"/campaigns/{campaign.id}/invite", data={"username": "alice"})
    assert r.status_code == 403


def test_cannot_invite_an_existing_member(gm_and_player, client):
    campaign = Campaign.query.one()
    client.post(f"/campaigns/{campaign.id}/invite", data={"username": "bob"})
    r = client.post(
        f"/campaigns/{campaign.id}/invite", data={"username": "bob"}, follow_redirects=True
    )
    assert b"already in this campaign" in r.data
    assert CampaignMembership.query.filter_by(campaign_id=campaign.id).count() == 2


def test_cannot_invite_an_unknown_user(gm_and_player, client):
    campaign = Campaign.query.one()
    r = client.post(
        f"/campaigns/{campaign.id}/invite", data={"username": "nobody"}, follow_redirects=True
    )
    assert b"No user called" in r.data


def test_player_can_leave(gm_and_player, client):
    campaign = Campaign.query.one()
    client.post(f"/campaigns/{campaign.id}/invite", data={"username": "bob"})
    client.get("/logout")
    login(client, "bob")
    client.post(f"/campaigns/{campaign.id}/accept")

    r = client.post(f"/campaigns/{campaign.id}/leave", follow_redirects=True)
    assert b"You left" in r.data
    assert client.get(f"/campaigns/{campaign.id}").status_code == 404
    assert CampaignMembership.query.filter_by(campaign_id=campaign.id).count() == 1


def test_owner_cannot_leave_their_own_campaign(gm_and_player, client):
    """Otherwise the campaign would be left with no game master."""
    campaign = Campaign.query.one()
    r = client.post(f"/campaigns/{campaign.id}/leave", follow_redirects=True)
    assert b"delete it instead" in r.data
    assert campaign.membership_of(campaign.owner_id) is not None


def test_game_master_can_remove_a_member(gm_and_player, client):
    campaign = Campaign.query.one()
    client.post(f"/campaigns/{campaign.id}/invite", data={"username": "bob"})
    bob_id = [m.user_id for m in campaign.memberships if m.user_id != campaign.owner_id][0]

    r = client.post(
        f"/campaigns/{campaign.id}/members/{bob_id}/remove", follow_redirects=True
    )
    assert b"Removed from the campaign" in r.data
    assert CampaignMembership.query.filter_by(campaign_id=campaign.id).count() == 1


def test_the_owner_cannot_be_removed(gm_and_player, client):
    campaign = Campaign.query.one()
    r = client.post(
        f"/campaigns/{campaign.id}/members/{campaign.owner_id}/remove", follow_redirects=True
    )
    assert b"owner cannot be removed" in r.data


def test_only_the_owner_can_delete(gm_and_player, client):
    campaign = Campaign.query.one()
    client.post(f"/campaigns/{campaign.id}/invite", data={"username": "bob"})
    client.get("/logout")
    login(client, "bob")
    client.post(f"/campaigns/{campaign.id}/accept")

    assert client.post(f"/campaigns/{campaign.id}/delete").status_code == 403
    assert Campaign.query.count() == 1


def test_delete_removes_memberships_too(gm_and_player, client):
    campaign = Campaign.query.one()
    client.post(f"/campaigns/{campaign.id}/invite", data={"username": "bob"})

    r = client.post(f"/campaigns/{campaign.id}/delete", follow_redirects=True)
    assert b"deleted" in r.data
    assert Campaign.query.count() == 0
    assert CampaignMembership.query.count() == 0


def test_accepting_an_invitation_you_do_not_have(gm_and_player, client, access_code):
    campaign = Campaign.query.one()
    client.get("/logout")
    signup(client, access_code, "mallory")
    r = client.post(f"/campaigns/{campaign.id}/accept", follow_redirects=True)
    assert b"no longer exists" in r.data
    assert CampaignMembership.query.filter_by(campaign_id=campaign.id).count() == 1


# --- inviting friends ------------------------------------------------------


def befriend(client, a, b):
    """Make two existing users friends: a asks, b accepts."""
    from website.models import Friendship, User

    login(client, a)
    client.post("/friends/add", data={"username": b}, follow_redirects=True)
    client.get("/logout")

    login(client, b)
    friendship = Friendship.query.filter_by(
        requester_id=User.find_by_username(a).id,
        addressee_id=User.find_by_username(b).id,
    ).one()
    client.post(f"/friends/{friendship.id}/accept", follow_redirects=True)
    client.get("/logout")


def test_game_master_can_invite_a_friend(gm_and_player, client):
    campaign = Campaign.query.one()
    befriend(client, "alice", "bob")
    login(client, "alice")

    r = client.get(f"/campaigns/{campaign.id}")
    assert b"Invite a friend" in r.data and b"bob" in r.data

    from website.models import User

    bob_id = User.find_by_username("bob").id
    r = client.post(
        f"/campaigns/{campaign.id}/invite-friend",
        data={"user_id": bob_id},
        follow_redirects=True,
    )
    assert b"Invited bob" in r.data
    assert campaign.membership_of(bob_id).status == MembershipStatus.INVITED


def test_cannot_invite_a_stranger_through_the_friend_route(gm_and_player, client):
    """The friend route must not become a way to add arbitrary user ids."""
    campaign = Campaign.query.one()
    from website.models import User

    bob_id = User.find_by_username("bob").id  # exists, but is not a friend
    r = client.post(
        f"/campaigns/{campaign.id}/invite-friend",
        data={"user_id": bob_id},
        follow_redirects=True,
    )
    assert b"not on your friend list" in r.data
    assert campaign.membership_of(bob_id) is None


def test_a_player_cannot_invite_friends(gm_and_player, client):
    campaign = Campaign.query.one()
    client.post(f"/campaigns/{campaign.id}/invite", data={"username": "bob"})
    client.get("/logout")
    login(client, "bob")
    client.post(f"/campaigns/{campaign.id}/accept")

    assert client.post(
        f"/campaigns/{campaign.id}/invite-friend", data={"user_id": 1}
    ).status_code == 403


def test_friends_already_in_the_campaign_are_not_offered(gm_and_player, client):
    campaign = Campaign.query.one()
    befriend(client, "alice", "bob")
    login(client, "alice")

    assert b"Invite a friend" in client.get(f"/campaigns/{campaign.id}").data

    from website.models import User

    client.post(
        f"/campaigns/{campaign.id}/invite-friend",
        data={"user_id": User.find_by_username("bob").id},
    )
    # bob is the only friend, so the whole section disappears once he is invited
    assert b"Invite a friend" not in client.get(f"/campaigns/{campaign.id}").data


# --- invite codes ----------------------------------------------------------


def test_generate_and_join_with_an_invite_code(gm_and_player, client, access_code):
    campaign = Campaign.query.one()
    r = client.post(f"/campaigns/{campaign.id}/invite-code", follow_redirects=True)
    assert b"ready to share" in r.data

    code = Campaign.query.one().invite_code
    assert code and len(code) >= 12
    assert code.encode() in r.data  # the shareable link is shown

    client.get("/logout")
    login(client, "bob")
    # opening the link only previews; it must not join on GET
    r = client.get(f"/campaigns/join/{code}")
    assert r.status_code == 200 and b"Join this campaign" in r.data
    # a GET must not have joined anyone
    assert CampaignMembership.query.filter_by(campaign_id=campaign.id).count() == 1

    r = client.post("/campaigns/join", data={"code": code}, follow_redirects=True)
    assert b"You joined" in r.data
    members = CampaignMembership.query.filter_by(campaign_id=campaign.id).all()
    assert len(members) == 2
    assert all(m.status == MembershipStatus.ACTIVE for m in members)


def test_a_bad_code_does_nothing(gm_and_player, client):
    campaign = Campaign.query.one()
    r = client.post("/campaigns/join", data={"code": "not-a-real-code"}, follow_redirects=True)
    assert b"not valid" in r.data
    assert CampaignMembership.query.filter_by(campaign_id=campaign.id).count() == 1


def test_an_empty_code_does_not_match_a_campaign_without_one(gm_and_player, client):
    """A campaign with no code stores NULL; an empty submission must not match."""
    assert Campaign.query.one().invite_code is None
    r = client.post("/campaigns/join", data={"code": ""}, follow_redirects=True)
    assert b"not valid" in r.data


def test_regenerating_invalidates_the_old_code(gm_and_player, client):
    campaign = Campaign.query.one()
    client.post(f"/campaigns/{campaign.id}/invite-code")
    old_code = Campaign.query.one().invite_code
    client.post(f"/campaigns/{campaign.id}/invite-code")
    new_code = Campaign.query.one().invite_code
    assert old_code != new_code

    client.get("/logout")
    login(client, "bob")
    r = client.post("/campaigns/join", data={"code": old_code}, follow_redirects=True)
    assert b"not valid" in r.data
    r = client.post("/campaigns/join", data={"code": new_code}, follow_redirects=True)
    assert b"You joined" in r.data


def test_revoking_stops_the_link_working(gm_and_player, client):
    campaign = Campaign.query.one()
    client.post(f"/campaigns/{campaign.id}/invite-code")
    code = Campaign.query.one().invite_code
    client.post(f"/campaigns/{campaign.id}/invite-code/revoke", follow_redirects=True)
    assert Campaign.query.one().invite_code is None

    client.get("/logout")
    login(client, "bob")
    assert b"not valid" in client.post(
        "/campaigns/join", data={"code": code}, follow_redirects=True
    ).data


def test_only_the_game_master_manages_the_invite_code(gm_and_player, client):
    campaign = Campaign.query.one()
    client.post(f"/campaigns/{campaign.id}/invite", data={"username": "bob"})
    client.get("/logout")
    login(client, "bob")
    client.post(f"/campaigns/{campaign.id}/accept")

    assert client.post(f"/campaigns/{campaign.id}/invite-code").status_code == 403
    assert client.post(f"/campaigns/{campaign.id}/invite-code/revoke").status_code == 403


def test_joining_with_a_code_accepts_a_pending_invitation(gm_and_player, client):
    campaign = Campaign.query.one()
    client.post(f"/campaigns/{campaign.id}/invite", data={"username": "bob"})
    client.post(f"/campaigns/{campaign.id}/invite-code")
    code = Campaign.query.one().invite_code

    client.get("/logout")
    login(client, "bob")
    r = client.post("/campaigns/join", data={"code": code}, follow_redirects=True)
    assert b"You joined" in r.data
    assert CampaignMembership.query.filter_by(campaign_id=campaign.id).count() == 2
    assert all(
        m.status == MembershipStatus.ACTIVE
        for m in CampaignMembership.query.filter_by(campaign_id=campaign.id)
    )


def test_joining_twice_is_harmless(gm_and_player, client):
    campaign = Campaign.query.one()
    client.post(f"/campaigns/{campaign.id}/invite-code")
    code = Campaign.query.one().invite_code
    client.get("/logout")
    login(client, "bob")
    client.post("/campaigns/join", data={"code": code}, follow_redirects=True)
    r = client.post("/campaigns/join", data={"code": code}, follow_redirects=True)
    assert b"already in" in r.data
    assert CampaignMembership.query.filter_by(campaign_id=campaign.id).count() == 2


def test_invite_code_routes_require_login(client, access_code):
    signup(client, access_code, "alice")
    create_campaign(client)
    campaign = Campaign.query.one()
    client.get("/logout")
    for route, method in (
        (f"/campaigns/{campaign.id}/invite-code", "post"),
        ("/campaigns/join", "post"),
        ("/campaigns/join/whatever", "get"),
    ):
        r = getattr(client, method)(route)
        assert r.status_code == 302, route
