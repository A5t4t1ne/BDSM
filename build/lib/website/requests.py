from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from .models import Hero
from .tools.decode import Decode
from . import db
import json
import os
from website.constants import LITURGIES



req = Blueprint("requests", __name__)


@req.route("/data-request", methods=['GET', 'POST'])
@login_required
def data_request():
    request_data = request.get_json()
    hero = db.session.execute(db.select(Hero).where(
                                Hero.user_id == current_user.id, 
                                Hero.secure_name == request_data['name'])
                            ).scalar()
    sorted_hero_stats = json.dumps(hero.stats, sort_keys=True)
  
    if not hero:
        return jsonify(None)
    
    return sorted_hero_stats



@req.route('/save-hero', methods=['POST'])
@login_required
def save_hero_from_request():
    request_data = request.get_json()
    hero = db.session.execute(db.select(Hero).where(
                                Hero.user_id == current_user.id, 
                                Hero.secure_name == request_data['name'])
                            ).scalar()

    if hero:
        # need to make copy, otherwise change is not detected by db.session.commit()
        new = hero.stats.copy()
        new.update({key:val for key, val in request_data.items() if key != 'name'})
        hero.stats = new

        db.session.commit()

        return jsonify(error=0)
    
    return jsonify(error=-1)


@req.route('/delete-hero',methods=['POST'])
@login_required
def delete_hero():
    data = request.get_json()
    hero = db.session.execute(db.select(Hero).where(Hero.user_id == current_user.id, Hero.secure_name == data['name'])).scalar()
    
    hero_path = hero.path
    
    if not hero_path:
        # no valid hero
        return jsonify(error=-1)

    if os.path.isfile(hero_path):
        os.remove(hero_path)

    db.session.delete(hero)
    db.session.commit()

    return jsonify(error=0)