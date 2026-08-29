from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class _Model(BaseModel):
    """Base for every model in this module.

    ``populate_by_name`` lets us construct models with the pythonic field name
    while still accepting Optolith's camelCase keys, and ``extra="ignore"``
    keeps a new Optolith release from breaking uploads with unknown keys.
    """

    model_config = ConfigDict(populate_by_name=True, extra="ignore")


#################################################
# Raw optolith hero json parsing
#################################################
class PersonalTrait(_Model):
    family: str = ""
    placeofbirth: str = ""
    dateofbirth: str = ""
    age: Optional[int] = None
    haircolor: Optional[int] = None
    eyecolor: Optional[int] = None
    size: Optional[float] = None
    weight: Optional[float] = None
    title: str = ""
    socialstatus: Optional[int] = None
    culture_area_knowledge: str = Field(default="", alias="cultureAreaKnowledge")


class Attribute(_Model):
    id: str
    value: int


class Attrs(_Model):
    values: List[Attribute] = Field(default_factory=list)
    ae: int = 0
    kp: int = 0
    lp: int = 0
    permanent_AE: Dict[str, int] = Field(default_factory=dict, alias="permanentAE")
    permanent_KP: Dict[str, int] = Field(default_factory=dict, alias="permanentKP")
    permanent_LP: Dict[str, int] = Field(default_factory=dict, alias="permanentLP")


class RawActivatableVal(_Model):
    sid: Optional[str | int] = None
    sid2: Optional[str | int] = None
    tier: Optional[int] = None


class Item(_Model):
    id: str
    name: str = ""
    amount: int = 0
    price: Optional[float] = None
    gr: Optional[int] = None
    is_template_locked: Optional[bool] = Field(default=None, alias="isTemplateLocked")
    weight: Optional[float] = None
    template: Optional[str] = None
    enc: Optional[int] = None
    pro: Optional[int] = None
    armor_type: Optional[int] = Field(default=None, alias="ArmorType")


class Purse(_Model):
    d: int = 0
    s: int = 0
    h: int = 0
    k: int = 0


class ArmorZone(_Model):
    id: str
    name: str = ""
    head: Optional[str] = None
    left_arm: Optional[str] = Field(default=None, alias="leftArm")
    right_arm: Optional[str] = Field(default=None, alias="rightArm")
    torso: Optional[str] = None
    left_leg: Optional[str] = Field(default=None, alias="leftLeg")
    right_leg: Optional[str] = Field(default=None, alias="rightLeg")


class Belongings(_Model):
    items: Dict[str, Item] = Field(default_factory=dict)
    armor_zones: Dict[str, ArmorZone] = Field(default_factory=dict, alias="armorZones")
    purse: Purse = Field(default_factory=Purse)


class Pet(_Model):
    # Optolith stores every pet stat as free text, including the numeric ones.
    id: str
    name: str = ""
    size: str = ""
    type: str = ""
    attack: str = ""
    dp: str = ""
    reach: str = ""
    actions: str = ""
    talents: str = ""
    skills: str = ""
    notes: str = ""
    cou: str = ""
    sgc: str = ""
    # ``int`` and ``str`` would shadow the builtins used in our own annotations,
    # so they are exposed under safe names and mapped back via aliases.
    intuition: str = Field(default="", alias="int")
    cha: str = ""
    dex: str = ""
    agi: str = ""
    con: str = ""
    strength: str = Field(default="", alias="str")
    lp: str = ""
    ae: str = ""
    spi: str = ""
    tou: str = ""
    pro: str = ""
    ini: str = ""
    mov: str = ""
    at: str = ""
    pa: str = ""


class RawOptolithHero(_Model):
    date_created: Optional[datetime] = Field(default=None, alias="dateCreated")
    date_modified: Optional[datetime] = Field(default=None, alias="dateModified")
    id: str = ""
    client_version: str = Field(default="", alias="clientVersion")
    phase: int = 0
    ap: Dict[str, Any] = Field(default_factory=dict)
    el: str = ""
    r: str = ""
    rv: str = ""
    c: str = ""
    p: str = ""
    pers: PersonalTrait = Field(default_factory=PersonalTrait)
    name: str
    sex: str = ""
    attr: Attrs
    activatables: Dict[str, List[RawActivatableVal]] = Field(default_factory=dict, alias="activatable")
    talents: Dict[str, int] = Field(default_factory=dict)
    ct: Dict[str, int] = Field(default_factory=dict)
    spells: Dict[str, int] = Field(default_factory=dict)
    cantrips: List[str] = Field(default_factory=list)
    liturgies: Dict[str, int] = Field(default_factory=dict)
    blessings: List[str] = Field(default_factory=list)
    belongings: Belongings = Field(default_factory=Belongings)
    pets: Dict[str, Pet] = Field(default_factory=dict)


#################################################
# Detailed activatables data parsing
#################################################
class ActivatableSource(_Model):
    id: str
    first_page: Optional[int] = Field(default=None, alias="firstPage")
    last_page: Optional[int] = Field(default=None, alias="lastPage")


class AttributeCheck(_Model):
    """One of the three attributes rolled for a skill check."""

    attr_id: str = Field(alias="ATTR_ID")
    name: str = ""
    short: str = ""


class SkillUniv(_Model):
    """The ``univ`` sub-object shared by liturgies and spells.

    Only the fields the UI needs are typed; the rest is kept verbatim so the
    reference data stays round-trippable.
    """

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    check1: Optional[AttributeCheck] = None
    check2: Optional[AttributeCheck] = None
    check3: Optional[AttributeCheck] = None
    gr: Optional[int] = None
    ic: Optional[str] = None


class Liturgie(_Model):
    id: Optional[str] = None
    casting_time: str = Field(default="", alias="castingTime")
    casting_time_short: str = Field(default="", alias="castingTimeShort")
    duration: str = ""
    duration_short: str = Field(default="", alias="durationShort")
    effect: str = ""
    kp_cost: str = Field(default="", alias="kpCost")
    kp_cost_short: str = Field(default="", alias="kpCostShort")
    name: str = ""
    name_short: Optional[str] = Field(default=None, alias="nameShort")
    range: str = ""
    range_short: str = Field(default="", alias="rangeShort")
    src: List[ActivatableSource] = Field(default_factory=list)
    target: str = ""
    univ: SkillUniv = Field(default_factory=SkillUniv)
    # the hero's skill level (Fertigkeitswert); only set on a hero's own copy
    fw: Optional[int] = None


class Spell(_Model):
    # Spells cost AsP (aeCost), not KaP -- this is the one field that differs
    # structurally from Liturgie.
    id: Optional[str] = None
    ae_cost: str = Field(default="", alias="aeCost")
    ae_cost_short: str = Field(default="", alias="aeCostShort")
    casting_time: str = Field(default="", alias="castingTime")
    casting_time_short: str = Field(default="", alias="castingTimeShort")
    duration: str = ""
    duration_short: str = Field(default="", alias="durationShort")
    effect: str = ""
    name: str = ""
    range: str = ""
    range_short: str = Field(default="", alias="rangeShort")
    src: List[ActivatableSource] = Field(default_factory=list)
    target: str = ""
    univ: SkillUniv = Field(default_factory=SkillUniv)
    # the hero's skill level (Fertigkeitswert); only set on a hero's own copy
    fw: Optional[int] = None


class Blessing(_Model):
    # Blessings are always instant and free -- no casting time, cost or check.
    id: Optional[str] = None
    duration: str = ""
    effect: str = ""
    name: str = ""
    range: str = ""
    src: List[ActivatableSource] = Field(default_factory=list)
    target: str = ""


#################################################
# Decoded hero, as persisted in the database
#################################################
class Activatables(_Model):
    adv: Dict[str, Any] = Field(default_factory=dict)
    disadv: Dict[str, Any] = Field(default_factory=dict)
    sa: Dict[str, Any] = Field(default_factory=dict)


class HeroStats(_Model):
    name: str
    secure_name: str = ""
    avatar_img: str = Field(default="", alias="avatar-img")
    lep_max: int = 0
    lep_min: int = 0
    lep_current: int = 0
    asp_max: int = 0
    asp_current: int = 0
    kap_max: int = 0
    kap_current: int = 0
    wealth: Purse = Field(default_factory=Purse)
    armor: int = 0
    enc: int = 0
    attr: Attrs = Field(default_factory=Attrs)
    # ability ids mapped to the hero's skill level; the descriptive data is
    # joined in on read so a reference-data update reaches existing heroes.
    liturgies: Dict[str, int] = Field(default_factory=dict)
    spells: Dict[str, int] = Field(default_factory=dict)
    talents: Dict[str, int] = Field(default_factory=dict)
    blessings: List[str] = Field(default_factory=list)
    activatables: Activatables = Field(default_factory=Activatables)
    ini: int = 0
    dodge: int = 0
    effects: Dict[str, int] = Field(default_factory=dict)
    schips: int = 0
