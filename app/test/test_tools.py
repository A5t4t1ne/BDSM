"""Tests for the hero decode pipeline."""

import copy
import io
import json

import pytest
from pydantic import ValidationError

from website.constants import BLESSINGS, LITURGIES, SPECIAL_ABILITIES, SPELLS
from website.datatypes import HeroStats, RawOptolithHero
from website.tools.decode import Decode
from website.tools.upload import parse_hero


def test_reference_data_loads():
    assert len(LITURGIES) == 227
    assert len(SPELLS) == 330
    assert len(BLESSINGS) == 12
    # the id is only a mapping key in the source file and must be copied on
    assert LITURGIES["LITURGY_1"].id == "LITURGY_1"
    assert LITURGIES["LITURGY_1"].univ.check1.short == "MU"


@pytest.mark.parametrize("fixture", ["priest_hero", "magician_hero"])
def test_decode_produces_serialisable_stats(request, fixture):
    raw = request.getfixturevalue(fixture)
    stats = Decode.from_upload(raw)

    assert isinstance(stats, HeroStats)
    assert stats.name
    # must survive the round trip into the JSON database column
    json.dumps(stats.model_dump(by_alias=True, mode="json"))


def test_decode_does_not_mutate_reference_data(priest_hero, magician_hero):
    """Regression: resolving abilities used to write into the shared tables,
    leaking one hero's skill level into every later request."""
    before_sa = copy.deepcopy(SPECIAL_ABILITIES)
    before_lit = {k: v.model_dump() for k, v in LITURGIES.items()}

    Decode.from_upload(priest_hero)
    Decode.from_upload(magician_hero)

    assert SPECIAL_ABILITIES == before_sa
    assert {k: v.model_dump() for k, v in LITURGIES.items()} == before_lit


def test_hero_without_improved_dodge_decodes(priest_hero):
    """Regression: dodge() looked SA_64 up unconditionally, and in the wrong
    category, so any hero without Improved Dodge raised KeyError."""
    priest_hero["activatable"].pop("SA_64", None)
    assert Decode.from_upload(priest_hero).dodge > 0


def test_empty_activatable_list_decodes(priest_hero):
    """Optolith writes an empty list for an activatable the hero lost."""
    priest_hero["activatable"]["ADV_25"] = []
    assert Decode.from_upload(priest_hero).lep_max > 0


def test_unknown_ability_ids_are_skipped(priest_hero):
    priest_hero["liturgies"]["LITURGY_DOES_NOT_EXIST"] = 5
    stats = Decode.from_upload(priest_hero)
    assert "LITURGY_DOES_NOT_EXIST" in stats.liturgies  # stored as-is
    # but resolving it against the reference data must not raise
    Decode.resolve_liturgies(RawOptolithHero.model_validate(priest_hero))


def test_missing_required_field_is_rejected(priest_hero):
    del priest_hero["attr"]
    with pytest.raises(ValidationError):
        Decode.from_upload(priest_hero)


class _FakeFile:
    def __init__(self, payload: bytes, filename: str):
        self._stream = io.BytesIO(payload)
        self.filename = filename

    def seek(self, pos):
        return self._stream.seek(pos)

    def read(self, *args):
        return self._stream.read(*args)


@pytest.mark.parametrize(
    "payload,filename,expected",
    [
        (b"{}", "hero.txt", "not a .json file"),
        (b"not json at all", "hero.json", "not valid JSON"),
        (b"[]", "hero.json", "not an Optolith hero export"),
        (b'{"name":"x"}', "hero.json", "no Optolith version"),
        (b'{"clientVersion":"0.9.0","name":"x"}', "hero.json", "needs 1.0 or newer"),
    ],
)
def test_parse_hero_rejects_with_a_reason(app, payload, filename, expected):
    hero, reason = parse_hero(_FakeFile(payload, filename))
    assert hero is None
    assert expected in reason
