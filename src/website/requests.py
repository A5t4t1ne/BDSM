from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from .models import Hero
from .tools.decode import Decode
from . import db
import json
import os

req = Blueprint("requests", __name__)

@req.route("/data-request", methods=['GET', 'POST'])
@login_required
def data_request():
    data = request.get_json()
    hero = Hero.query.filter_by(user_id=current_user.id, secure_name=data['name']).first()
    description = dict()

    activatables = hero.stats.get('activatables', None)
    if activatables == None:
        with open(hero.path, 'r') as f:
            data = json.load(f)
            hero.stats = Decode.decode_all(data)
    # for act in hero.stats['activatables']:
    #     description[act] = LITURGIES[act]

    if hero:
        return jsonify(hero.stats)
    else:
        return jsonify(None)

@req.route('/save-hero', methods=['POST'])
@login_required
def save_hero_from_request():
    request_data = request.get_json()
    hero = Hero.query.filter_by(user_id=current_user.id, secure_name=request_data['name']).first()
    if hero:
        with open(hero.path, 'r') as f:
            hero_data = json.load(f)

        for key, item in request_data.items():
            hero_data[key] = item
        
        with open(hero.path, 'w') as f:
            json.dump(hero_data, f)
        
        hero.stats = hero_data
        db.session.commit()

        return jsonify(error=0)
    
    return jsonify(error=-1)


@req.route('/delete-hero',methods=['POST'])
@login_required
def delete_hero():
    data = request.get_json()
    hero = Hero.query.filter_by(user_id=current_user.id, secure_name=data['name'])
    hero_path = hero.first().path
    
    if not hero_path:
        # no valid hero
        return jsonify(error=-1)

    if os.path.isfile(hero_path):
        os.remove(hero_path)

    hero.delete()
    db.session.commit()

    return jsonify(error=0)