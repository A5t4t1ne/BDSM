"""Tests for the friend list."""

import pytest

from website.models import Friendship, FriendshipStatus


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


@pytest.fixture()
def two_users(client, access_code):
    """alice is signed up and left logged in; bob exists too."""
    signup(client, access_code, "bob")
    client.get("/logout")
    signup(client, access_code, "alice")
    return client


def test_friends_page_requires_login(client):
    assert client.get("/friends").status_code == 302


def test_add_and_accept(two_users, client, access_code):
    r = client.post("/friends/add", data={"username": "bob"}, follow_redirects=True)
    assert b"Friend request sent to bob" in r.data
    assert b"Waiting for them" in r.data

    client.get("/logout")
    login(client, "bob")
    r = client.get("/friends")
    assert b"Requests to you" in r.data and b"alice" in r.data

    friendship = Friendship.query.one()
    r = client.post(f"/friends/{friendship.id}/accept", follow_redirects=True)
    assert b"now friends" in r.data

    # visible from both sides
    assert b"alice" in client.get("/friends").data
    client.get("/logout")
    login(client, "alice")
    assert b"bob" in client.get("/friends").data


def test_add_is_case_insensitive(two_users, client):
    r = client.post("/friends/add", data={"username": "BOB"}, follow_redirects=True)
    assert b"Friend request sent to bob" in r.data


def test_cannot_add_yourself(two_users, client):
    r = client.post("/friends/add", data={"username": "alice"}, follow_redirects=True)
    assert b"cannot add yourself" in r.data
    assert Friendship.query.count() == 0


def test_unknown_user(two_users, client):
    r = client.post("/friends/add", data={"username": "nobody"}, follow_redirects=True)
    assert b"No user called" in r.data
    assert Friendship.query.count() == 0


def test_duplicate_request_is_rejected(two_users, client):
    client.post("/friends/add", data={"username": "bob"}, follow_redirects=True)
    r = client.post("/friends/add", data={"username": "bob"}, follow_redirects=True)
    assert b"already asked bob" in r.data
    assert Friendship.query.count() == 1


def test_adding_back_accepts_the_pending_request(two_users, client):
    """bob asked alice; alice adding bob should just make them friends."""
    client.get("/logout")
    login(client, "bob")
    client.post("/friends/add", data={"username": "alice"}, follow_redirects=True)

    client.get("/logout")
    login(client, "alice")
    r = client.post("/friends/add", data={"username": "bob"}, follow_redirects=True)
    assert b"now friends" in r.data
    assert Friendship.query.count() == 1
    assert Friendship.query.one().status == FriendshipStatus.ACCEPTED


def test_only_the_addressee_can_accept(two_users, client):
    client.post("/friends/add", data={"username": "bob"}, follow_redirects=True)
    friendship = Friendship.query.one()

    # alice sent it, so she cannot accept it herself
    r = client.post(f"/friends/{friendship.id}/accept", follow_redirects=True)
    assert b"no longer exists" in r.data
    assert Friendship.query.one().status == FriendshipStatus.PENDING


def test_a_third_party_cannot_touch_a_friendship(two_users, client, access_code):
    client.post("/friends/add", data={"username": "bob"}, follow_redirects=True)
    friendship = Friendship.query.one()

    client.get("/logout")
    signup(client, access_code, "mallory")
    for route in ("accept", "remove"):
        r = client.post(f"/friends/{friendship.id}/{route}", follow_redirects=True)
        assert b"no longer exists" in r.data
    assert Friendship.query.count() == 1


def test_either_side_can_remove(two_users, client):
    client.post("/friends/add", data={"username": "bob"}, follow_redirects=True)
    friendship = Friendship.query.one()
    client.get("/logout")
    login(client, "bob")
    client.post(f"/friends/{friendship.id}/accept", follow_redirects=True)

    r = client.post(f"/friends/{friendship.id}/remove", follow_redirects=True)
    assert b"Removed" in r.data
    assert Friendship.query.count() == 0
