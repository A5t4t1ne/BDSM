import json
from pathlib import Path
from typing import Tuple

from flask import current_app
from flask_login import current_user
from flask_wtf import FlaskForm
from loguru import logger
from pydantic import ValidationError
from werkzeug.utils import secure_filename
from wtforms import MultipleFileField, SubmitField

from .. import db
from ..datatypes import HeroStats
from ..models import Hero
from .decode import Decode

# Optolith exports before 1.0 use an incompatible layout.
MIN_CLIENT_VERSION = 1


class UploadFileForm(FlaskForm):
    files = MultipleFileField("File(s) upload")
    submit = SubmitField("Commit")


def _client_version_major(raw_version: str) -> int | None:
    """Major version of an Optolith 'X.Y.Z' client version string."""
    parts = raw_version.split(".")
    if not parts or not parts[0].isdigit():
        return None
    return int(parts[0])


def parse_hero(file) -> Tuple[HeroStats | None, str]:
    """Validate and decode one uploaded file.

    Args:
        file: a werkzeug FileStorage from the upload form

    Returns:
        Tuple[HeroStats | None, str]: the decoded hero, or None plus a reason
        that is safe to show to the user.
    """
    filename = file.filename or ""
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if extension not in current_app.config["ALLOWED_EXTENSIONS"]:
        return None, "not a .json file"

    # the file may already have been read, so rewind before parsing
    file.seek(0)
    try:
        raw = json.load(file)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None, "not valid JSON"

    if not isinstance(raw, dict):
        return None, "not an Optolith hero export"

    major = _client_version_major(str(raw.get("clientVersion", "")))
    if major is None:
        return None, "no Optolith version in the file"
    if major < MIN_CLIENT_VERSION:
        return None, f"exported by Optolith {raw['clientVersion']}, needs {MIN_CLIENT_VERSION}.0 or newer"

    try:
        return Decode.from_upload(raw), ""
    except ValidationError as e:
        # log the detail, show the user only the field names
        logger.warning(f"hero validation failed for {filename}: {e}")
        fields = sorted({".".join(str(p) for p in err["loc"]) for err in e.errors()})
        return None, "missing or invalid: " + ", ".join(fields[:5])
    except Exception as e:
        logger.exception(f"decoding {filename} failed: {e}")
        return None, "could not be decoded"


def _unique_hero_name(hero_name: str, heroes_dir: Path) -> str:
    """Find a free filename stem, appending (1), (2), ... on collision."""
    candidate = hero_name
    counter = 0
    while (heroes_dir / f"{candidate}.json").exists():
        counter += 1
        candidate = f"{hero_name}({counter})"
    return candidate


def save_hero(file) -> Tuple[bool, str]:
    """Validate an uploaded hero and store it for the current user.

    Returns:
        Tuple[bool, str]: success, and a reason when unsuccessful.
    """
    hero_stats, reason = parse_hero(file)
    if hero_stats is None:
        return False, reason

    heroes_dir = Path(current_user.heroes_path).resolve()
    heroes_dir.mkdir(parents=True, exist_ok=True)

    base_name = secure_filename(hero_stats.name).lower() or "hero"
    secure_name = _unique_hero_name(base_name, heroes_dir)
    file_path = heroes_dir / f"{secure_name}.json"

    # keep the displayed name in step with the deduplicated file name
    if secure_name != base_name:
        suffix = secure_name[len(base_name):]
        hero_stats.name += suffix

    hero_stats.secure_name = secure_name

    file.seek(0)
    hero_stats.avatar_img = json.load(file).get("avatar", "")

    stats = hero_stats.model_dump(by_alias=True, mode="json")

    with open(file_path, "w", encoding="utf8") as f:
        json.dump(stats, f)

    new_hero = Hero(
        name=hero_stats.name,
        secure_name=secure_name,
        path=str(file_path),
        stats=stats,
        user_id=current_user.id,
    )
    db.session.add(new_hero)
    db.session.commit()

    logger.info(f"saved hero '{hero_stats.name}' for user {current_user.id}")
    return True, ""
