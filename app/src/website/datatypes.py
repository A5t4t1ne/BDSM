from datetime import datetime
from typing import Any, Dict, List
from pydantic import BaseModel, Field


#################################################
# Raw optolith hero json parsing
#################################################
class PersonalTrait(BaseModel):
    family: str
    placeofbirth: str
    dateofbirth: str
    age: int
    haircolor: int
    eyecolor: int
    size: int
    weight: int
    title: str
    socialstatus: int
    cultureAreaKnowledge: str


class Attribute(BaseModel):
    id: str
    value: int


class Attrs(BaseModel):
    values: List[Attribute]
    ae: int
    kp: int
    lp: int
    permanent_AE: Dict[str, int] = Field(alias="permanentAE")
    permanent_KP: Dict[str, int] = Field(alias="permanentKP")
    permanent_LP: Dict[str, int] = Field(alias="permanentLP")


class RawActivatableVal(BaseModel):
    sid: str | int | None = None
    sid2: str | int | None = None
    tier: int | None = None


class Item(BaseModel):
    id: str
    name: str
    amount: int
    price: float | None = None
    gr: int | None = None
    is_template_locked: bool | None = Field(alias="isTemplateLocked")
    weight: float | None = None
    template: str | None = None
    enc: int | None = None
    pro: int | None = None
    armor_type: int | None = Field(alias="ArmorType")


class Purse(BaseModel):
    d: int
    s: int
    h: int
    k: int


class ArmorZone(BaseModel):
    id: str
    name: str
    head: str
    left_arm: str = Field(alias="leftArm")
    right_arm: str = Field(alias="rightArm")
    torso: str
    left_leg: str = Field(alias="leftLeg")
    right_leg: str = Field(alias="rightLeg")


class Belongings(BaseModel):
    items: Dict[str, Item]
    armor_zones: Dict[str, ArmorZone] = Field(alias="armorZones")
    purse: Purse


class Pet(BaseModel):
    id: str
    name: str
    size: float
    type: str
    attack: str
    dp: str
    reach: str
    actions: int
    talents: str
    skills: str
    notes: str
    cou: str
    sgc: str
    int: str
    cha: str
    dex: str
    agi: str
    con: str
    str: str
    lp: str
    ae: str
    spi: str
    tou: str
    pro: str
    ini: str
    mov: str
    at: str
    pa: str


class RawOptolithHero(BaseModel):
    date_created: datetime = Field(alias="dateCreated")
    date_modified: datetime = Field(alias="dateModified")
    id: str
    phase: int
    ap: Dict
    el: str
    r: str
    rv: str
    c: str
    p: str
    pers: PersonalTrait
    name: str
    sex: str
    attr: Attrs
    activatables: Dict[str, List[RawActivatableVal]] = Field(alias="activatable")
    talents: Dict[str, int]
    ct: Dict[str, int]
    spells: Dict[str, int]
    cantrips: List[str]
    liturgies: Dict[str, int]
    blessings: List[str]
    belongings: Belongings
    pets: Dict[str, Pet]


#################################################
# Detailed activatables data parsing
#################################################
class ActivatableSource(BaseModel):
    id: str
    first_page: int = Field(alias="firstPage")
    last_page: int | None = Field(alias="lastPage")



class Liturgie(BaseModel):
    id: str | None = None
    casting_time: str = Field(alias="castingTime")
    casting_time_short: str = Field(alias="castingTimeShort")
    duration: str
    duration_short: str = Field(alias="durationShort")
    effect: str
    kp_cost: str = Field(alias="kpCost")
    kp_cost_short: str = Field(alias="kpCostShort")
    name: str
    range: str
    range_short: str = Field(alias="rangeShort")
    src: List[ActivatableSource]
    target: str
    univ: Dict[str, Any]
    fw: int | None = None


class Spell(BaseModel):
    # TODO
    id: str | None = None
    casting_time: str = Field(alias="castingTime")
    casting_time_short: str = Field(alias="castingTimeShort")
    duration: str
    duration_short: str = Field(alias="durationShort")
    effect: str
    kp_cost: str = Field(alias="kpCost")
    kp_cost_short: str = Field(alias="kpCostShort")
    name: str
    range: str
    range_short: str = Field(alias="rangeShort")
    src: List[ActivatableSource]
    target: str
    univ: Dict[str, Any]

class Blessing(BaseModel):
    # TODO
    # TODO
    id: str | None = None
    casting_time: str = Field(alias="castingTime")
    casting_time_short: str = Field(alias="castingTimeShort")
    duration: str
    duration_short: str = Field(alias="durationShort")
    effect: str
    kp_cost: str = Field(alias="kpCost")
    kp_cost_short: str = Field(alias="kpCostShort")
    name: str
    range: str
    range_short: str = Field(alias="rangeShort")
    src: List[ActivatableSource]
    target: str
    univ: Dict[str, Any]
