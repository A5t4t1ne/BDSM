from . import db
from flask_login import UserMixin


class Level:
    ADMIN = 0
    SYSADMIN = 1
    USER = 2
    GUEST = 3


class Hero(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    secure_name = db.Column(db.String(150))
    path = db.Column(db.String(1000))
    stats = db.Column(db.JSON)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(150))
    access_lvl = db.Column(db.Integer)
    email = db.Column(db.String(150))   # not used yet
    heroes_path = db.Column(db.String(1000))
    # one to many -> relationship connects the "one" to another class of which it can possess multiples.
    # heroes will be a list type variable with all Hero-objects created by the indivial user
    heroes = db.relationship('Hero')
