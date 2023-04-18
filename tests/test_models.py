import pytest
from website.models import User, Hero, Level


def test_user_creation():
    """
    GIVEN a user model
    WHEN a User is created
    THEN check if the individual fields are created correctly
    """
    pw = "ExamplePassword123#@#"
    uname = "ExampleUserName"
    lvl = Level.ADMIN
    email = "asdf@yeet.com"
    path = "./my_heroes"

    user = User(
        username=uname, password=pw, access_lvl=lvl, email=email, heroes_path=path
    )

    assert user.username == uname
    assert user.password == pw
    assert user.access_lvl == lvl
    assert user.email == email
    assert user.heroes_path == path


def test_hero_creation():
    """
    GIVEN a Hero model
    WHEN a Hero is created
    THEN check if the individual fields are created correctly
    """
    name = "ExampleHero"
    sname = "SecureHeroName"
    user_id = 5
    path = "./my_hero"
    stats = {"name": name, "sname": sname, "lep": 9001}

    hero = Hero(name=name, secure_name=sname, path=path, stats=stats, user_id=user_id)

    assert hero.name == name
    assert hero.secure_name == sname
    assert hero.path == path
    assert hero.stats == stats
    assert hero.user_id == user_id
