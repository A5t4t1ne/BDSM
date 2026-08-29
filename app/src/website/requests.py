import os
from typing import Any, Dict, Tuple

from flask import Blueprint, Response, jsonify, request
from flask_login import current_user, login_required
from loguru import logger
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from . import db
from .constants import BLESSINGS, LITURGIES, SPECIAL_ABILITIES, SPELLS
from .models import Hero

req = Blueprint("requests", __name__)


class HeroUpdate(BaseModel):
    """The stats a client is allowed to change.

    Anything else in the request body is ignored: the stored hero is otherwise
    derived from the Optolith export and must not be writable from the browser.
    """

    model_config = ConfigDict(extra="ignore")

    lep_max: int | None = Field(default=None, ge=0, le=999)
    asp_max: int | None = Field(default=None, ge=0, le=999)
    kap_max: int | None = Field(default=None, ge=0, le=999)
    lep_current: int | None = Field(default=None, ge=-999, le=999)
    asp_current: int | None = Field(default=None, ge=-999, le=999)
    kap_current: int | None = Field(default=None, ge=-999, le=999)
    schips: int | None = Field(default=None, ge=0, le=99)
    wealth: Dict[str, int] | None = None


def _load_hero(secure_name: Any) -> Hero | None:
    """Load one of the current user's heroes by its secure name."""
    if not isinstance(secure_name, str) or not secure_name:
        return None
    return db.session.execute(
        db.select(Hero).where(Hero.user_id == current_user.id, Hero.secure_name == secure_name)
    ).scalar()


def _liturgy_view(stored: Dict[str, int]) -> Dict[str, Any]:
    """Join the hero's liturgy levels against the reference data."""
    view: Dict[str, Any] = {}
    for lit_id, skill_level in stored.items():
        liturgy = LITURGIES.get(lit_id)
        if liturgy is None:
            logger.debug(f"skipping unknown liturgy {lit_id}")
            continue
        view[lit_id] = {
            "name": liturgy.name,
            "castingTime": liturgy.casting_time,
            "duration": liturgy.duration,
            "univ": {
                "check1": liturgy.univ.check1.model_dump(by_alias=True) if liturgy.univ.check1 else None,
                "check2": liturgy.univ.check2.model_dump(by_alias=True) if liturgy.univ.check2 else None,
                "check3": liturgy.univ.check3.model_dump(by_alias=True) if liturgy.univ.check3 else None,
            },
            "FW": skill_level,
        }
    return view


def _spell_view(stored: Dict[str, int]) -> Dict[str, Any]:
    view: Dict[str, Any] = {}
    for spell_id, skill_level in stored.items():
        spell = SPELLS.get(spell_id)
        if spell is None:
            logger.debug(f"skipping unknown spell {spell_id}")
            continue
        view[spell_id] = {
            "name": spell.name,
            "castingTime": spell.casting_time,
            "duration": spell.duration,
            "univ": {
                "check1": spell.univ.check1.model_dump(by_alias=True) if spell.univ.check1 else None,
                "check2": spell.univ.check2.model_dump(by_alias=True) if spell.univ.check2 else None,
                "check3": spell.univ.check3.model_dump(by_alias=True) if spell.univ.check3 else None,
            },
            "FW": skill_level,
        }
    return view


def _blessing_view(stored: Any) -> Dict[str, Any]:
    view: Dict[str, Any] = {}
    for ble_id in stored or []:
        blessing = BLESSINGS.get(ble_id)
        if blessing is None:
            logger.debug(f"skipping unknown blessing {ble_id}")
            continue
        view[ble_id] = {"name": blessing.name, "duration": blessing.duration}
    return view


def _special_ability_view(stored: Dict[str, Any]) -> Dict[str, Any]:
    view: Dict[str, Any] = {}
    for sa_id, details in (stored or {}).items():
        reference = SPECIAL_ABILITIES.get(sa_id)
        name = (details or {}).get("name") or (reference or {}).get("name") or sa_id
        view[sa_id] = {"name": name, "tier": (details or {}).get("tier")}
    return view


@req.route("/data-request", methods=["POST"])
@login_required
def data_request() -> Response | Tuple[Response, int]:
    """Return one hero's play-screen data.

    The response is assembled fresh; the stored hero is never modified here.

    Returns:
        Response: the hero's display data, or 404 if the user has no such hero.
    """
    request_data = request.get_json(silent=True) or {}
    hero = _load_hero(request_data.get("name"))
    if hero is None:
        return jsonify(error=-1, message="Hero not found"), 404

    stats: Dict[str, Any] = hero.stats or {}

    # only what the play screen renders -- keeps the response small and avoids
    # shipping the raw attribute block to the browser
    payload = {
        key: stats.get(key)
        for key in (
            "name",
            "secure_name",
            "lep_max",
            "lep_min",
            "lep_current",
            "asp_max",
            "asp_current",
            "kap_max",
            "kap_current",
            "wealth",
            "armor",
            "enc",
            "ini",
            "dodge",
            "talents",
            "effects",
            "schips",
        )
    }
    payload["liturgies"] = _liturgy_view(stats.get("liturgies") or {})
    payload["spells"] = _spell_view(stats.get("spells") or {})
    payload["blessings"] = _blessing_view(stats.get("blessings"))
    payload["activatables"] = {"SA": _special_ability_view((stats.get("activatables") or {}).get("sa") or {})}

    return jsonify(payload)


@req.route("/save-hero", methods=["POST"])
@login_required
def save_hero_from_request() -> Tuple[Response, int]:
    """Apply a client-side stat change to one of the user's heroes.

    Returns:
        Tuple[Response, int]: a JSON response and an HTTP status code.
    """
    request_data = request.get_json(silent=True) or {}
    hero = _load_hero(request_data.get("name"))
    if hero is None:
        return jsonify(error=-1, message="Hero not found"), 404

    try:
        update = HeroUpdate.model_validate(request_data)
    except ValidationError as e:
        logger.warning(f"rejected hero update for {hero.secure_name}: {e}")
        return jsonify(error=-1, message="Those values are out of range"), 400

    changes = update.model_dump(exclude_none=True)
    if not changes:
        return jsonify(error=0, message="Nothing to save"), 200

    # the JSON column is not tracked for in-place edits, so reassign a new dict
    new_stats = dict(hero.stats or {})
    new_stats.update(changes)
    hero.stats = new_stats
    db.session.commit()

    return jsonify(error=0, message="Saved successfully"), 200


@req.route("/delete-hero", methods=["POST"])
@login_required
def delete_hero() -> Tuple[Response, int]:
    """Delete one of the current user's heroes and its stored file.

    Returns:
        Tuple[Response, int]: a JSON response and an HTTP status code.
    """
    data = request.get_json(silent=True) or {}
    hero = _load_hero(data.get("name"))
    if hero is None:
        return jsonify(error=-1, message="Hero not found"), 404

    hero_path = hero.path
    if hero_path and os.path.isfile(hero_path):
        try:
            os.remove(hero_path)
        except OSError as e:
            # the database row is the source of truth; a stale file is not fatal
            logger.warning(f"could not remove hero file {hero_path}: {e}")

    db.session.delete(hero)
    db.session.commit()

    return jsonify(error=0, message="Deleted"), 200
