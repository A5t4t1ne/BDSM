"""Static DSA reference data, loaded once at import time.

Everything in here is read-only. Callers must never mutate the loaded objects:
they are shared across every request and worker, so an in-place edit would leak
one hero's data into the next one's response.
"""

import json
from pathlib import Path
from typing import Dict, Type, TypeVar

from pydantic import BaseModel

from .datatypes import Blessing, Liturgie, Spell

DATA_PATH = Path(__file__).absolute().parent / "data"

T = TypeVar("T", bound=BaseModel)


def _load_models(filename: str, model: Type[T]) -> Dict[str, T]:
    """Load ``{id: {...}}`` reference data into ``{id: model}``.

    The id is only present as the mapping key in the source files, so it is
    copied onto the model to keep entries self-describing.
    """
    with open(DATA_PATH / filename, "r", encoding="utf8") as f:
        raw: Dict[str, dict] = json.load(f)

    entries: Dict[str, T] = {}
    for key, val in raw.items():
        entry = model.model_validate(val)
        entry.id = key
        entries[key] = entry
    return entries


def _load_raw(filename: str) -> Dict[str, dict]:
    with open(DATA_PATH / filename, "r", encoding="utf8") as f:
        return json.load(f)


LITURGIES: Dict[str, Liturgie] = _load_models("Liturgies.json", Liturgie)
SPELLS: Dict[str, Spell] = _load_models("Spells.json", Spell)
BLESSINGS: Dict[str, Blessing] = _load_models("Blessings.json", Blessing)

# Not modelled yet -- these have heterogeneous shapes (see TODO in datatypes).
ATTRIBUTES: Dict[str, dict] = _load_raw("Attributes.json")
SKILLS: Dict[str, dict] = _load_raw("Skills.json")
SPECIAL_ABILITIES: Dict[str, dict] = _load_raw("SpecialAbilities.json")
