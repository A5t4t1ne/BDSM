import math
from copy import deepcopy
from typing import Any, Dict, List

from loguru import logger

from ..constants import BLESSINGS, LITURGIES, SKILLS, SPECIAL_ABILITIES, SPELLS
from ..datatypes import (
    Activatables,
    Attrs,
    Belongings,
    Blessing,
    HeroStats,
    Item,
    Liturgie,
    Purse,
    RawActivatableVal,
    RawOptolithHero,
    Spell,
)


class Decode:
    """Class to decode a DSA hero from the raw hero data.
    This class provides methods to extract important stats from the raw hero data."""

    @classmethod
    def from_upload(cls, raw: Dict[str, Any]) -> HeroStats:
        """Validate a raw Optolith export and decode it in one step.

        Args:
            raw (dict): the parsed contents of an Optolith hero .json

        Raises:
            pydantic.ValidationError: if the export is not a usable hero

        Returns:
            HeroStats: the decoded hero
        """
        return cls.decode_all(RawOptolithHero.model_validate(raw))

    @classmethod
    def decode_all(cls, hero: RawOptolithHero) -> HeroStats:
        """Assembles all stats of a hero from the raw hero data.

        Only the hero's own numbers are stored. Descriptive data (names, casting
        times, checks) is joined in on read from the reference tables, so that
        updating the reference data also updates already-uploaded heroes.

        Args:
            hero (RawOptolithHero): validated raw hero

        Returns:
            HeroStats: the hero's stats including name.
        """
        max_lep = cls.max_lep(hero=hero)
        max_asp = cls.max_asp(hero=hero)
        max_kap = cls.max_kap(hero=hero)

        return HeroStats(
            name=hero.name,
            lep_max=max_lep,
            lep_min=cls.min_lep(hero=hero),
            lep_current=max_lep,
            asp_max=max_asp,
            asp_current=max_asp,
            kap_max=max_kap,
            kap_current=max_kap,
            wealth=cls.wealth(hero=hero),
            armor=cls.armor(hero=hero),
            enc=cls.encumbrance(hero=hero),
            attr=cls.all_attributes(hero),
            liturgies=cls.liturgies(hero),
            spells=cls.spells(hero),
            talents=cls.talents(hero),
            blessings=cls.blessings(hero),
            activatables=cls.resolve_activatables(hero),
            ini=cls.initiative(hero),
            dodge=cls.dodge(hero),
            effects=dict(),
            schips=0,
        )

    @staticmethod
    def _tier(activatables: Dict[str, List[RawActivatableVal]], activatable_id: str) -> int:
        """Tier of an activatable the hero may or may not have.

        Optolith writes an empty list for activatables the hero does not
        possess, so presence of the key alone is not enough.
        """
        entries = activatables.get(activatable_id) or []
        if not entries:
            return 0
        return entries[0].tier or 0

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

        lep_max += cls._tier(activatables["ADV"], ActivatablesID.HIGH_LEP)
        lep_max -= cls._tier(activatables["DISADV"], ActivatablesID.LOW_LEP)

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

        asp_max += cls._tier(adv, ActivatablesID.HIGH_ASP)
        asp_max -= cls._tier(disadv, ActivatablesID.LOW_ASP)
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

        kap_max += cls._tier(adv, ActivatablesID.HIGH_KAP)
        kap_max -= cls._tier(disadv, ActivatablesID.LOW_KAP)
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
                    logger.warning(f"armor {item} has no encumbrance value, assuming 0")
                    lvl = 0
                enc = lvl

        special_abilities = cls.activatables(hero=hero)["SA"]
        reduction = cls._tier(special_abilities, ActivatablesID.REDUCE_ENC)
        if reduction:
            logger.trace(f"Found reduced encumbrance ({ActivatablesID.REDUCE_ENC}), tier {reduction}")
            enc -= 2 * reduction
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

        special_abilities = cls.activatables(hero=hero)["SA"]
        return base_dodge + cls._tier(special_abilities, ActivatablesID.IMPR_DODGE)

    @classmethod
    def resolve_activatables(cls, hero: RawOptolithHero) -> Activatables:
        """Gather the descriptive details for a hero's advantages, disadvantages
        and special abilities.

        Args:
            hero (RawOptolithHero): validated raw hero

        Returns:
            Activatables: adv/disadv kept as raw selections, SA enriched with
            names and rules text from the reference data.
        """
        adv: Dict[str, Any] = {}
        disadv: Dict[str, Any] = {}
        sa: Dict[str, Any] = {}

        for act_key, act_val in hero.activatables.items():
            if act_key.startswith("ADV_"):
                adv[act_key] = [v.model_dump() for v in act_val]
            elif act_key.startswith("DISADV_"):
                disadv[act_key] = [v.model_dump() for v in act_val]
            elif act_key.startswith("SA_"):
                # an empty list means the hero does not currently possess this SA
                if not act_val:
                    continue
                resolved = cls._resolve_special_ability(act_key, act_val, hero_name=hero.name)
                if resolved is not None:
                    sa[act_key] = resolved

        return Activatables(adv=adv, disadv=disadv, sa=sa)

    @classmethod
    def _resolve_special_ability(
        cls, act_key: str, variations: List[RawActivatableVal], hero_name: str
    ) -> Dict[str, Any] | None:
        """Build the detail record for a single special ability.

        One SA id can cover many variations -- every language shares SA_28, for
        example -- which is what ``sid``/``sid2`` select between.

        Everything returned is a fresh copy: the reference tables are shared
        across requests and workers and must never be mutated in place.
        """
        base = SPECIAL_ABILITIES.get(act_key)
        if base is None:
            logger.warning(f"unknown special ability {act_key} (hero={hero_name})")
            return None

        details: Dict[str, Any] = deepcopy(base)

        for variation in variations:
            if variation is None:
                continue
            try:
                if variation.tier is not None:
                    details["tier"] = variation.tier
                if variation.sid is None:
                    continue
                if isinstance(variation.sid, int):
                    cls._apply_select_option(details, base, act_key, str(variation.sid), hero_name)
                else:
                    cls._apply_referenced_entry(details, variation)
            except Exception as e:
                logger.error(f"failed to resolve {act_key} for hero={hero_name}: {e}")

        return details

    @staticmethod
    def _apply_select_option(
        details: Dict[str, Any], base: Dict[str, Any], act_key: str, sid: str, hero_name: str
    ) -> None:
        """A numeric sid indexes into the SA's own 'selectOptions'."""
        details["sid"] = sid

        # extensions carry their options at the top level instead
        if act_key in ("SA_663", "SA_414"):
            return

        option = (base.get("selectOptions") or {}).get(sid)
        if option is None:
            logger.debug(f"{act_key} has no selectOption {sid} (hero={hero_name})")
            return
        details.update(deepcopy(option))

    @classmethod
    def _apply_referenced_entry(cls, details: Dict[str, Any], variation: RawActivatableVal) -> None:
        """A string sid points at an entry in another reference table."""
        sid = str(variation.sid)
        category = sid.split("_")[0]
        if category == "TAL":
            details.update(deepcopy(SKILLS.get(sid, {"name": sid})))
        elif category == "LITURGY":
            details.update(cls._as_dict(LITURGIES.get(sid), sid))
        elif category == "SPELL":
            details.update(cls._as_dict(SPELLS.get(sid), sid))
        elif category == "SA":
            details.update(deepcopy(SPECIAL_ABILITIES.get(sid, {"name": sid})))
        else:
            details.update({"name": sid})

        if variation.sid2 is not None:
            applications = (SKILLS.get(sid) or {}).get("applications") or {}
            application = applications.get(str(variation.sid2))
            if application is not None:
                details["application"] = deepcopy(application)

    @staticmethod
    def _as_dict(entry: Any, fallback_id: str) -> Dict[str, Any]:
        """Reference entries are a mix of pydantic models and plain dicts."""
        if entry is None:
            return {"name": fallback_id}
        if hasattr(entry, "model_dump"):
            return entry.model_dump(by_alias=True, mode="json")
        return deepcopy(entry)

    @classmethod
    def resolve_liturgies(cls, hero: RawOptolithHero) -> Dict[str, Liturgie]:
        """Look up the hero's liturgies, carrying their skill level across.

        Returns copies -- the entries in LITURGIES are shared and must not be
        given a hero-specific skill level.
        """
        hero_liturgies: Dict[str, Liturgie] = {}
        for lit_id, skill_level in hero.liturgies.items():
            full_lit = LITURGIES.get(lit_id)
            if full_lit is None:
                logger.debug(f"unknown liturgy {lit_id} (hero={hero.name})")
                continue
            hero_liturgies[lit_id] = full_lit.model_copy(deep=True)
            hero_liturgies[lit_id].fw = skill_level

        return hero_liturgies

    @classmethod
    def resolve_blessings(cls, hero: RawOptolithHero) -> Dict[str, Blessing]:
        hero_blessings: Dict[str, Blessing] = {}
        for bl in hero.blessings:
            bl_desc = BLESSINGS.get(bl)
            if bl_desc is not None:
                hero_blessings[bl] = bl_desc.model_copy(deep=True)

        return hero_blessings

    @classmethod
    def resolve_spells(cls, hero: RawOptolithHero) -> Dict[str, Spell]:
        hero_spells: Dict[str, Spell] = {}
        for spell_id, skill_level in hero.spells.items():
            spell_desc = SPELLS.get(spell_id)
            if spell_desc is None:
                logger.debug(f"unknown spell {spell_id} (hero={hero.name})")
                continue
            hero_spells[spell_id] = spell_desc.model_copy(deep=True)
            hero_spells[spell_id].fw = skill_level

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
