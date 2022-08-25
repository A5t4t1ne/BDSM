from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(10000))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Hero(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hero_name = db.Column(db.String(150))
    hero_path = db.Column(db.String(1000))
    hero_stats = db.Column()
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(150))
    access_lvl = db.Column(db.Integer)
    email = db.Column(db.String(150))   # not used yet
    heroes_path = db.Column(db.String(1000))

    # one to many -> relationship connects the "one" to another class of which it can possess multiples. 
    # heroes will be a list type variable with all Note-objects created by the indivial user 
    heroes = db.relationship('Hero')

    # will be removed later
    notes = db.relationship('Note')
