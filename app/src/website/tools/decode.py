import math
from dataclasses import dataclass
from typing import Dict, List

from src.website.datatypes import (
    Blessing,
    Liturgie,
    RawActivatableVal,
    Attrs,
    Belongings,
    Item,
    Purse,
    RawOptolithHero,
    Spell,
)
from website.constants import LITURGIES, BLESSINGS, SPELLS, SPECIAL_ABILITIES, SKILLS
from loguru import logger


@dataclass
class Activatables:
    adv: Dict[str, int]
    disadv: Dict[str, int]
    sa: Dict[str, int]


@dataclass
class HeroStats:
    name: str
    lep_max: int
    lep_min: int
    lep_current: int
    asp_max: int
    asp_current: int
    kap_max: int
    kap_current: int
    wealth: Purse
    armor: int
    enc: int
    attr: Attrs
    liturgies: Dict[str, Liturgie]
    spells: Dict[str, int]
    talents: Dict[str, int]
    ini: int
    dodge: int
    blessings: List[str]
    activatables: Activatables
    effects: Dict[str, int]
    schips: int


class Decode:
    """Class to decode a DSA hero from the raw hero data.
    This class provides methods to extract important stats from the raw hero data."""

    @classmethod
    def decode_all(cls, hero: RawOptolithHero) -> HeroStats:
        """Assembles all stats of a hero from the raw hero data.
        This method gathers all relevant information from the hero's raw data
        and returns a dictionary containing the hero's stats.

        Args:
            hero (RawOptolithHero): hero in the format of Decode.decode_all()

        Returns:
            dict: the hero's stats including name.
        """

        return HeroStats(
            hero.name,
            cls.max_lep(hero=hero),
            cls.min_lep(hero=hero),
            cls.max_lep(hero=hero),
            cls.max_asp(hero=hero),
            cls.max_asp(hero=hero),
            cls.max_kap(hero=hero),
            cls.max_kap(hero=hero),
            cls.wealth(hero=hero),
            0,  # TODO: armor
            0,  # TODO: enc - cls.armor_and_enc(hero=hero),
            cls.all_attributes(hero),
            cls.resolve_liturgies(hero),
            cls.spells(hero),
            cls.talents(hero),
            cls.initiative(hero),
            cls.dodge(hero),
            cls.blessings(hero),
            cls.resolve_activatables(hero),
            dict(),
            0,
        )

    @classmethod
    def max_lep(cls, hero: RawOptolithHero) -> int:
        """Calculates the maximum Lebensenergiepunkte (LeP) for a hero.

        Args:
            hero (RawOptolithHero): raw hero dictionary

        Raises:
            KeyError: If the hero does not have the required attributes or activatables.

        Returns:
            int: The maximum LeP for the hero.
        """
        lep_max = 0

        # life given from KO-value and additional bought life
        ko_value = cls.search_for_attr(hero=hero, search_for_attr=AttributeID.KO)
        additional_life = cls.all_attributes(hero=hero).lp

        lep_max += ko_value * 2 + additional_life

        # determine race affect on LeP
        race = cls.race(hero)
        if race == Race.Human:
            lep_max += 5
        elif race == Race.Elf:
            lep_max += 2
        elif race == Race.Half_Elf:
            lep_max += 5
        elif race == Race.Dwarf:
            lep_max += 8

        # advantage/disadvantage effect on LeP
        activatables = cls.activatables(hero)

        if ActivatablesID.HIGH_LEP in activatables["ADV"]:
            tier = activatables["ADV"][ActivatablesID.HIGH_LEP][0].tier
            lep_max += tier if tier else 0
        elif ActivatablesID.LOW_LEP in activatables["DISADV"]:
            tier = activatables["DISADV"][ActivatablesID.LOW_LEP][0].tier
            lep_max -= tier if tier else 0

        return lep_max

    @classmethod
    def min_lep(cls, hero: RawOptolithHero):
        ko_value = cls.search_for_attr(hero=hero, search_for_attr=AttributeID.KO)
        return -ko_value

    @classmethod
    def max_asp(cls, hero: RawOptolithHero):
        asp_max = 0

        asp_max += cls.all_attributes(hero).ae

        hero_KL = cls.search_for_attr(hero, search_for_attr=AttributeID.KL)
        hero_CH = cls.search_for_attr(hero, search_for_attr=AttributeID.CH)
        hero_IN = cls.search_for_attr(hero, search_for_attr=AttributeID.IN)

        activatables = cls.activatables(hero)

        adv = activatables["ADV"]
        disadv = activatables["DISADV"]
        sa = activatables["SA"]

        if adv.get(ActivatablesID.HIGH_ASP):
            tier = adv[ActivatablesID.HIGH_ASP][0].tier
            asp_max += tier if tier else 0
        if disadv.get(ActivatablesID.LOW_ASP):
            tier = disadv[ActivatablesID.LOW_ASP][0].tier
            asp_max -= tier if tier else 0
        if adv.get(ActivatablesID.MAGICIAN):
            asp_max += 20

        # advantages that affect asp based on a character property
        # --- KL ---
        if any(key in sa for key in ["SA_70", "SA_346", "SA_681"]):
            asp_max += hero_KL

            # --- KL / 2 ---
        if any(key in sa for key in ["SA_750"]):
            asp_max += math.ceil(hero_KL / 2)

            # --- IN ---
        if any(key in sa for key in ["SA:345"]):
            asp_max += hero_IN

            # --- CH ---
        if any(key in sa for key in ["SA_255", "SA_676"]):
            asp_max += hero_CH

            # --- CH / 2 ---
        if any(key in sa for key in ["SA_677"]):
            asp_max += math.ceil(hero_CH / 2)

        return asp_max

    @classmethod
    def max_kap(cls, hero: RawOptolithHero):
        kap_max = hero.attr.kp

        hero_KL = cls.search_for_attr(hero, AttributeID.KL)
        hero_CH = cls.search_for_attr(hero, AttributeID.CH)
        hero_IN = cls.search_for_attr(hero, AttributeID.IN)
        hero_MU = cls.search_for_attr(hero, AttributeID.MU)

        # advantages and disadvantages
        activatables = cls.activatables(hero)

        adv = activatables["ADV"]
        disadv = activatables["DISADV"]
        sa = activatables["SA"]

        if adv.get(ActivatablesID.HIGH_KAP):
            tier = adv[ActivatablesID.HIGH_KAP][0].tier or 0
            kap_max += tier
        if disadv.get(ActivatablesID.LOW_KAP):
            tier = disadv[ActivatablesID.LOW_KAP][0].tier or 0
            kap_max -= tier
        if adv.get(ActivatablesID.PRIEST):
            kap_max += 20

        # advantages that affect kap based on a character property
        # --- MU ---
        if any(key in sa for key in ["SA_682", "SA_683", "SA_689", "SA_693", "SA_696", "SA_698"]):
            kap_max += hero_MU

            # --- KL ---
        if any(key in sa for key in ["SA_86", "SA_684", "SA_688", "SA_697", "SA_1049"]):
            kap_max += hero_KL

            # --- IN ---
        if any(key in sa for key in ["SA_685", "SA_686", "SA_691", "SA_694"]):
            kap_max += hero_IN

            # --- CH ---
        if any(key in sa for key in ["SA_687", "SA_692", "SA_695", "SA_690"]):
            kap_max += hero_CH

        return kap_max

    @classmethod
    def wealth(cls, hero: RawOptolithHero) -> Purse:
        return cls.belongings(hero=hero).purse

    @classmethod
    def armor(cls, hero: RawOptolithHero) -> int:
        logger.trace("trying to fetch armor values")
        items = cls.items(hero=hero)
        for item in items:
            if items[item].armor_type:
                protection_lvl = items[item].pro
                logger.debug(f"Found armor with prot lvl: {protection_lvl}")

                return protection_lvl if protection_lvl else 0

        logger.debug("No armor found")
        return 0

    @classmethod
    def encumbrance(cls, hero: RawOptolithHero):
        logger.trace("trying to calculate encumbrance")
        items = cls.items(hero=hero)
        enc = 0
        for item in items:
            if items[item].armor_type is not None:
                lvl = items[item].enc
                if lvl is None:
                    raise Exception("armor found but no encumbrance.")
                enc = lvl

        if ActivatablesID.REDUCE_ENC in cls.activatables(hero=hero):
            logger.trace(f"Found reduced encumbrance ({ActivatablesID.REDUCE_ENC})")
            tier = cls.activatables(hero=hero)["SA"][ActivatablesID.REDUCE_ENC][0].tier
            if tier is None:
                raise Exception("Reduce encumbrance activatable has no tier.")

            enc -= 2 * tier
        else:
            logger.trace(f"No reduced encumbrance found (searched for {ActivatablesID.REDUCE_ENC})")

        enc = enc if enc >= 0 else 0
        logger.debug(f"Final encumbrance: {enc}")

        return enc

    @classmethod
    def race(cls, hero: RawOptolithHero) -> str:
        return hero.r

    @classmethod
    def all_attributes(cls, hero: RawOptolithHero) -> Attrs:
        """Returns all attributes from the hero"""
        return hero.attr

    @classmethod
    def search_for_attr(cls, hero: RawOptolithHero, search_for_attr: str) -> int:
        """Returns the tier of a specific attribute specified with 'AttributeID.<attr>'"""

        for attr in hero.attr.values:
            if attr.id == search_for_attr:
                return attr.value

        raise KeyError(f'attribute "{search_for_attr}" not found')

    @classmethod
    def activatables(cls, hero: RawOptolithHero) -> Dict[str, Dict[str, List[RawActivatableVal]]]:
        activatables: Dict[str, Dict[str, List[RawActivatableVal]]] = {"ADV": dict(), "DISADV": dict(), "SA": dict()}

        activatables["ADV"] = {key: val for key, val in hero.activatables.items() if key.startswith("ADV_")}
        activatables["DISADV"] = {key: val for key, val in hero.activatables.items() if key.startswith("DISADV_")}
        activatables["SA"] = {key: val for key, val in hero.activatables.items() if key.startswith("SA_")}
        return activatables

    @classmethod
    def belongings(cls, hero: RawOptolithHero) -> Belongings:
        return hero.belongings

    @classmethod
    def items(cls, hero: RawOptolithHero) -> Dict[str, Item]:
        return hero.belongings.items

    @classmethod
    def liturgies(cls, hero: RawOptolithHero) -> Dict[str, int]:
        return hero.liturgies

    @classmethod
    def blessings(cls, hero: RawOptolithHero) -> List[str]:
        return hero.blessings

    @classmethod
    def spells(cls, hero: RawOptolithHero) -> Dict[str, int]:
        return hero.spells

    @classmethod
    def talents(cls, hero: RawOptolithHero) -> Dict[str, int]:
        return hero.talents

    @classmethod
    def initiative(cls, hero: RawOptolithHero):
        mu = cls.search_for_attr(hero=hero, search_for_attr=AttributeID.MU)
        ge = cls.search_for_attr(hero=hero, search_for_attr=AttributeID.GE)
        base_ini = math.ceil((mu + ge) / 2)
        return base_ini - cls.encumbrance(hero=hero)

    @classmethod
    def dodge(cls, hero: RawOptolithHero):
        base_dodge = cls.search_for_attr(hero=hero, search_for_attr=AttributeID.GE) / 2
        base_dodge = math.ceil(base_dodge)

        activatables = cls.activatables(hero=hero)
        tier = activatables["ADV"][ActivatablesID.IMPR_DODGE][0].tier
        if tier:
            impr_dodge = tier
        else:
            impr_dodge = 0

        return base_dodge + impr_dodge

    @classmethod
    def resolve_activatables(cls, hero: RawOptolithHero) -> Activatables:
        """Gather all details of a hero's attributes, activatables, belongings, liturgies, blessings, spells and talents

        Args:
            hero (RawOptolithHero): hero in the format of Decode.decode_all()

        Returns:
            dict: the hero's complete stats including descriptive details
        """
        act = {"ADV": dict(), "DISADV": dict(), "SA": dict()}

        # ----------------- ADV, DISADV, SA -----------------
        for act_key, act_val in hero.activatables.items():
            if act_key.startswith("ADV_"):
                act["ADV"][act_key] = act_val
            elif act_key.startswith("DISADV_"):
                act["DISADV"][act_key] = act_val
            elif act_key.startswith("SA_"):
                # if value is empty, hero does curently not posess this SA
                if not act_val:
                    continue

                # one SA can have multiple variations
                # e.g there are different languages and yet they belong to the same SA number
                sa_vari_keys = []
                for sa_variation in act_val:
                    # if the length of the dictionary inside the list is > 0 it's an SA with different types
                    # (and levels) e.g. each individual language has a type (which language) and a tier/level
                    if sa_variation:
                        try:
                            if sa_vari_keys and sa_variation.sid:
                                sid = sa_variation.sid
                                if type(sid) is int:
                                    # if sid is numeric it is an option which can be found
                                    # in the sub-dictionary 'selectOptions' from the special abilities
                                    sid = str(sid)
                                    act["SA"][act_key] = SPECIAL_ABILITIES[act_key]

                                    # extensions must be handled differently
                                    if act_key == "SA_663" or act_key == "SA_414":
                                        act["SA"][act_key].update(SPECIAL_ABILITIES[act_key])
                                        act["SA"][act_key]["sid"] = sid
                                    else:
                                        logger.debug(f"{act_key=}, {sa_variation=}, {act_val=}")
                                        act["SA"][act_key].update(SPECIAL_ABILITIES[act_key]["selectOptions"][sid])

                                elif type(sid) is str:
                                    activatable_data = dict()
                                    category = sid.split("_")[0]
                                    if category == "TAL":
                                        activatable_data = SKILLS[sid]
                                    elif category == "LITURGY":
                                        activatable_data = LITURGIES[sid]
                                    elif category == "SPELL":
                                        activatable_data = SPELLS[sid]
                                    elif category == "SA":
                                        activatable_data = SPECIAL_ABILITIES[sid]
                                    else:
                                        activatable_data = {"name": sid}

                                    act["SA"][act_key] = activatable_data

                                    if "sid2" in sa_vari_keys:
                                        sid2 = str(sa_variation.sid2)
                                        act["SA"][act_key]["application"] = SKILLS[sid]["applications"][sid2]
                                elif "tier" in sa_vari_keys:
                                    act["SA"][act_key] = SPECIAL_ABILITIES[act_key]
                                    act["SA"][act_key]["tier"] = sa_variation.tier
                                else:
                                    pass
                        except Exception as e:
                            logger.error(f"{e=}, hero={hero.name}\n")

                    else:
                        act["SA"][act_key] = SPECIAL_ABILITIES[act_key]
        return Activatables(act["ADV"], act["DISADV"], act["SA"])

    @classmethod
    def resolve_liturgies(cls, hero: RawOptolithHero) -> Dict[str, Liturgie]:
        hero_liturgies = dict()
        for lit_id in hero.liturgies.keys():
            full_lit = LITURGIES.get(lit_id, None)
            if full_lit is not None:
                full_lit.fw = hero.liturgies[lit_id]
                hero_liturgies[lit_id] = full_lit

        return hero_liturgies

    @classmethod
    def resolve_blessings(cls, hero: RawOptolithHero) -> Dict[str, Blessing]:  # TODO: is it actually a list
        hero_blessings: Dict[str, Blessing] = dict()
        for bl in hero.blessings:
            bl_desc = BLESSINGS.get(bl, None)
            if bl_desc is not None:
                hero_blessings[bl] = bl_desc

        return hero_blessings

    @classmethod
    def resolve_spells(cls, hero: RawOptolithHero) -> Dict[str, Spell]:
        hero_spells: Dict[str, Spell] = dict()
        for spell in hero.spells:
            spell_desc = SPELLS.get(spell, None)
            if spell_desc is not None:
                hero_spells[spell] = spell_desc

        return hero_spells


class HealthState:
    Dying = 0
    Unconscious = 1
    PainLvl3 = 2
    PainLvl2 = 3
    PainLvl1 = 4
    Healthy = 5


class AttributeID:
    MU = "ATTR_1"
    KL = "ATTR_2"
    IN = "ATTR_3"
    CH = "ATTR_4"
    FF = "ATTR_5"
    GE = "ATTR_6"
    KO = "ATTR_7"
    KK = "ATTR_8"
    ALL = "all"


class ActivatablesID:
    # advantages
    HIGH_ASP = "ADV_23"
    HIGH_KAP = "ADV_24"
    HIGH_LEP = "ADV_25"
    MAGICIAN = "ADV_50"
    PRIEST = "ADV_12"

    # disadvantages
    LOW_ASP = "DISADV_26"
    LOW_KAP = "DISADV_27"
    LOW_LEP = "DISADV_28"

    # special abilities (fight)
    REDUCE_ENC = "SA_41"  # Belastungsgewöhnung
    IMPR_DODGE = "SA_64"


class Race:
    Human = "R_1"  # Lep Base Modifier = 5 //1
    Elf = "R_2"  # Lep Base Modifier = 2 //2
    Half_Elf = "R_3"  # Lep Base Modifier = 5 //3
    Dwarf = "R_4"  # Lep Base Modifier = 8 //4
