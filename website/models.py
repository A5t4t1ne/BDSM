from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(10000))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))   # one to many -> ForeignKey binds the attribute to an object


class Hero(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hero_name = db.Column(db.String(150))
    hero_path = db.Column(db.String(1000))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(150))
    access_lvl = db.Column(db.String(50))
    email = db.Column(db.String(150))   # not used yet
    heroes_path = db.Column(db.String(1000))

    # one to many -> relationship connects the "one" to another class of which it can possess multiples. 
    # notes will be a list type variable with all Note-objects created by the indivial user 
    notes = db.relationship('Note')
    heroes = db.relationship('Hero')
