from typing import Tuple
from flask import Blueprint, Response, request, jsonify
from flask_login import login_required, current_user

from .constants import LITURGIES, SPELLS
from .models import Hero
from . import db
import os


req = Blueprint("requests", __name__)


@req.route("/data-request", methods=["POST"])
@login_required
def data_request() -> Response:
    """Handles a data request for a hero's stats.
    This endpoint retrieves the stats of a hero based on the user's request.

    Returns:
        Response: A JSON response containing the hero's stats or None if not found.
    """
    request_data = request.get_json()
    hero = db.session.execute(
        db.select(Hero).where(Hero.user_id == current_user.id, Hero.secure_name == request_data["name"])
    ).scalar()
    if not hero:
        return jsonify(None)

    full_data_liturgies = {}
    for lit_name, lit_skill_level in hero.stats['liturgies'].items():
        full_data_liturgies[lit_name] = LITURGIES[lit_name]
        full_data_liturgies[lit_name]["FW"] = lit_skill_level

    hero.stats['liturgies'] = full_data_liturgies

    full_data_spells = {}
    for spell_name, spell_skill_level in hero.stats['spells'].items():
        full_data_spells[spell_name] = SPELLS[spell_name]
        full_data_spells[spell_name]["FW"] = spell_skill_level

    hero.stats['spells'] = full_data_spells

    return hero.stats


@req.route("/save-hero", methods=["POST"])
@login_required
def save_hero_from_request() -> Tuple[Response, int]:
    """Handles a request to save hero data.
    This endpoint updates the hero's stats based on the provided data.

    Returns:
        Tuple[Response, int]: A tuple containing a JSON response and an HTTP status code.
    """
    request_data = request.get_json()
    print(f"{request_data=}")
    hero = db.session.execute(
        db.select(Hero).where(Hero.user_id == current_user.id, Hero.secure_name == request_data["name"])
    ).scalar()

    if hero:
        # need to make copy, otherwise change is not detected by db.session.commit()
        new = hero.stats.copy()
        new.update({key: val for key, val in request_data.items() if key != "name"})
        hero.stats = new

        db.session.commit()

        return jsonify(error=0, message="Saved successfully"), 200

    return jsonify(error=-1, message="Failed to save data"), 500


@req.route("/delete-hero", methods=["POST"])
@login_required
def delete_hero() -> Response:
    """Handles a request to delete a hero.

    Returns:
        Response: A JSON response indicating success or failure.
    """
    data = request.get_json()
    hero: Hero | None = db.session.execute(
        db.select(Hero).where(Hero.user_id == current_user.id, Hero.secure_name == data["name"])
    ).scalar()

    if not hero or not isinstance(hero, Hero):
        return jsonify(error=-1)

    hero_path = hero.path
    if not hero_path:
        return jsonify(error=-1)

    if os.path.isfile(hero_path):
        os.remove(hero_path)

    db.session.delete(hero)
    db.session.commit()

    return jsonify(error=0)
