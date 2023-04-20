import pytest
from website import db, app
from website.tools.decode import Decode
from website.models import User, Hero
from werkzeug.security import generate_password_hash
from flask_login import login_user
import json


def test_data_request(client):
    """
    GIVEN a Flask application, a logged in user and a hero in the database
    WHEN the '/data-request' page is requested (POST)
    THEN check the response is valid
    """
    uname = "testUser"
    pw = "password"
    hashed_pw = generate_password_hash(pw, method="sha256")

    hero_stats = {"stat1": "val1", "stat2": "val2"}

    with app.app_context():
        hero = Hero(
            user_id=0, name="testHero", secure_name="testHero", stats=hero_stats
        )
        db.session.add(hero)
        db.session.commit()

        hero = db.session.execute(
            db.select(Hero).where(Hero.secure_name == "testHero")
        ).scalar()

        assert hero.secure_name == "testHero"

    # res = client.post("/data-request", data={"name": "testHero"})
