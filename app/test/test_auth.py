"""Tests for registration, login and the account rules around them."""

import pytest

from website.models import User


def signup(client, code, username="newuser", password="correcthorsebattery", confirm=None, access=None):
    return client.post(
        "/sign-up",
        data={
            "username": username,
            "password": password,
            "confPassword": password if confirm is None else confirm,
            "accessCode": code if access is None else access,
        },
        follow_redirects=True,
    )


def test_signup_and_login_roundtrip(client, access_code):
    assert b"proud owner" in signup(client, access_code).data
    client.get("/logout")

    r = client.post(
        "/login",
        data={"username": "newuser", "password": "correcthorsebattery"},
        follow_redirects=True,
    )
    assert r.status_code == 200
    assert client.get("/overview").status_code == 200


@pytest.mark.parametrize(
    "password,expected",
    [
        ("", b"at least 12"),
        ("short", b"at least 12"),
        ("elevenchars", b"at least 12"),
        ("x" * 101, b"too long"),
        ("has spaces in it here", b"only letters, numbers"),
    ],
)
def test_weak_passwords_are_rejected(client, access_code, password, expected):
    """Regression: an empty password used to satisfy every check."""
    assert expected in signup(client, access_code, password=password).data
    assert User.query.filter_by(username="newuser").first() is None


def test_password_confirmation_must_match(client, access_code):
    r = signup(client, access_code, password="correcthorsebattery", confirm="somethingelse")
    assert b"not matching" in r.data


def test_wrong_access_code_is_rejected(client, access_code):
    assert b"access code invalid" in signup(client, access_code, access="nope").data


@pytest.mark.parametrize("username", ["ab", "x" * 101, "admin1", "Admin", "hasümlaut", "has space"])
def test_invalid_usernames_are_rejected(client, access_code, username):
    signup(client, access_code, username=username)
    assert User.query.filter_by(username=username).first() is None


def test_usernames_are_case_insensitively_unique(client, access_code):
    """Regression: 'Dave' and 'dave' used to be two separate accounts."""
    signup(client, access_code, username="dave")
    client.get("/logout")
    assert b"already taken" in signup(client, access_code, username="DAVE").data
    assert User.query.count() == 2  # admin + dave


def test_login_does_not_reveal_whether_a_user_exists(client, access_code):
    signup(client, access_code, username="realuser")
    client.get("/logout")

    unknown = client.post("/login", data={"username": "ghost", "password": "whatever12345"})
    known = client.post("/login", data={"username": "realuser", "password": "wrongpassword1"})
    assert unknown.data == known.data


def test_login_is_rate_limited(app, client, access_code):
    """The limiter is disabled for the other tests, so enable it here."""
    app.config["RATELIMIT_ENABLED"] = True
    codes = [
        client.post("/login", data={"username": "x", "password": "y"}).status_code
        for _ in range(15)
    ]
    assert 429 in codes


def test_protected_pages_redirect_anonymous_users(client):
    for route in ("/overview", "/account", "/play", "/hero-display/whatever"):
        assert client.get(route).status_code == 302, route


def test_change_password(logged_in):
    r = logged_in.post(
        "/change-password",
        data={
            "currentPassword": "correcthorsebattery",
            "newPassword": "brandnewpassword",
            "confPassword": "brandnewpassword",
        },
        follow_redirects=True,
    )
    assert b"Password changed" in r.data

    logged_in.get("/logout")
    assert logged_in.post(
        "/login",
        data={"username": "testuser", "password": "brandnewpassword"},
        follow_redirects=True,
    ).status_code == 200
    assert logged_in.get("/overview").status_code == 200


@pytest.mark.parametrize(
    "current,new,confirm,expected",
    [
        ("wrongcurrent", "brandnewpassword", "brandnewpassword", b"not correct"),
        ("correcthorsebattery", "short", "short", b"at least 12"),
        ("correcthorsebattery", "brandnewpassword", "different12345", b"not matching"),
        ("correcthorsebattery", "correcthorsebattery", "correcthorsebattery", b"already your password"),
    ],
)
def test_change_password_rejections(logged_in, current, new, confirm, expected):
    r = logged_in.post(
        "/change-password",
        data={"currentPassword": current, "newPassword": new, "confPassword": confirm},
        follow_redirects=True,
    )
    assert expected in r.data

    # the old password must still work
    logged_in.get("/logout")
    logged_in.post("/login", data={"username": "testuser", "password": "correcthorsebattery"})
    assert logged_in.get("/overview").status_code == 200


def test_change_password_requires_login(client):
    assert client.post("/change-password", data={}).status_code == 302
