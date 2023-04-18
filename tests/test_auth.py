import pytest
from website import db
from website.models import User
from werkzeug.security import generate_password_hash, check_password_hash
import re


LOGIN_REQUIRED_ROUTES = ["/overview", "/account", "/play", "logout"]
LOGIN_NOT_REQUIRED_ROUTES = ["/", "/login", "sign-up"]
ACODE = "asdf"


def test_login_required(client):
    """
    GIVEN a Flask application configured for testing
    WHEN a page request is made to pages which require a user to log in
    THEN check if the request is denied
    """
    for route in LOGIN_REQUIRED_ROUTES:
        response = client.get(route)
        assert response.status_code == 302


def test_always_accessable_routes(client):
    """
    GIVEN a Flask application configured for testing
    WHEN a page request is made to pages which don't require a user to log in
    THEN check if the pages are accessible
    """
    for route in LOGIN_NOT_REQUIRED_ROUTES:
        response = client.get(route)
        assert response.status_code == 200


def test_sign_up(client, app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/sign-up' page is requested (POST)
    THEN check that the response is valid and a new user is registered
    """

    uname = "testUser"
    pw = "password"

    response = client.post(
        "/sign-up",
        data={
            "username": uname,
            "password": pw,
            "confPassword": pw,
            "accessCode": ACODE,
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "<title>Home</title>" in response.data.decode("utf-8")

    with app.app_context():
        user = db.session.execute(
            db.select(User).where(
                User.username == uname,
            )
        ).scalar()

        assert user is not None
        assert user.is_authenticated
        assert user.username == uname
        assert user.password != pw

        db.session.delete(user)
        db.session.commit()


def test_valid_login(client, app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/login' page is requested (POST)
    THEN check that the response is valid and the user is logged in
    """

    uname = "testUser"
    pw = "password"
    hashed_pw = generate_password_hash(pw, method="sha256")

    with app.app_context():
        user = User(username=uname, password=hashed_pw)
        db.session.add(user)
        db.session.commit()

    response = client.post(
        "/login",
        data={
            "username": uname,
            "password": pw,
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "<title>Home</title>" in response.data.decode("utf-8")

    with app.app_context():
        user = db.session.execute(
            db.select(User).where(
                User.username == uname,
            )
        ).scalar()

        assert user is not None
        assert user.is_authenticated
        assert user.username == uname
        assert check_password_hash(user.password, pw) == True

        db.session.delete(user)
        db.session.commit()


def test_username_not_valid(client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/sign-up' page is requested (POST) with invalid username
    THEN check that the response is valid and the user is not registered
    """
    unames = [
        "",
        "a",
        "ab",
        "toolong" * 15,
        "admin",
        "123admin123",
        "#adsf",
        "../../",
        "..\\..\\",
    ]
    err_messages = [
        "Sorry bro, username must be at least 3 characters long" for _ in range(3)
    ]
    err_messages.append("too long my friend")
    err_messages.extend(["Nope not that one please" for _ in range(2)])
    err_messages.extend(
        ["For usernames only characters and numbers please" for _ in range(3)]
    )

    pw = "password"

    for uname, err_msg in zip(unames, err_messages):
        response = client.post(
            "/sign-up",
            data={
                "username": uname,
                "password": pw,
                "confPassword": pw,
                "accessCode": ACODE,
            },
            follow_redirects=True,
        )
        html_data = response.data.decode("utf-8")

        assert response.status_code == 200
        assert "<title>Sign up</title>" in html_data
        assert err_msg in html_data


def test_password_not_valid(client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/sign-up' page is requested (POST) with an invalid password
    THEN check that the response is valid and the user is not registered"""
    passwords = ["\0", "\n", "toolong" * 15]
    err_messages = ["For passwords only characters, numbers and" for _ in range(2)]
    err_messages.append("too long my friend")
    uname = "UserName"

    for pw, err_msg in zip(passwords, err_messages):
        response = client.post(
            "/sign-up",
            data={
                "username": uname,
                "password": pw,
                "confPassword": pw,
                "accessCode": ACODE,
            },
            follow_redirects=True,
        )
        html_data = response.data.decode("utf-8")
        title = re.search("<title>(.+?)</title>", html_data).group(1)
        displayed_err_msg = re.search(
            '<div class="alert alert-danger alert-dismissible fade show" role="alert">(.*)<button',
            html_data,
        ).group(1)

        assert response.status_code == 200
        assert "<title>Sign up</title>" == title
        assert err_msg in displayed_err_msg
