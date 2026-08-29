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
