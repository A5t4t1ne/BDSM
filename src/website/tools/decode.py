import math
from ..constants import LITURGIES, BLESSINGS, SPELLS, SPECIAL_ABILITIES, SKILLS
import logging
import os
import json

log_path = os.path.join(os.getcwd(), "log", "log.txt")

logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', filename=log_path, level=logging.DEBUG, encoding='utf-8')


class Decode():
    @classmethod
    def decode_all(cls, hero:dict)     ->  dict:
        """Returns all important stats from the raw hero

        :param: hero (dict)    the DSA hero in a dict format   
        """
        stats = dict()
        stats['name'] = hero['name']
        stats['lep_max'] = cls.max_lep(hero=hero)
        stats['lep_min'] = cls.min_lep(hero=hero)
        stats['lep_current'] = stats['lep_max']
        stats['asp_max'] = cls.max_asp(hero=hero)
        stats['asp_current'] = stats['asp_max']
        stats['kap_max'] = cls.max_kap(hero=hero)
        stats['kap_current'] = stats['kap_max']
        stats['wealth'] = cls.wealth(hero=hero)
        stats['armor'], stats['enc'] = cls.armor(hero=hero, return_weight=True)
        stats['attributes'] = cls.attributes(hero)
        stats['liturgies'] = cls.liturgies(hero)
        stats['spells'] = cls.spells(hero)
        stats['talents'] = cls.talents(hero)
        stats['INI'] = cls.initiative(hero)
        stats['dodge'] = cls.dodge(hero)
        stats['blessings'] = cls.blessings(hero)
        stats['activatables'] = cls.activatables(hero)

        # initialize hero effects
        stats['desire'] = 0
        stats['intoxication'] = 0
        stats['anaesthesia'] = 0
        stats['fear'] = 0
        stats['paralysis'] = 0
        stats['pain'] = 0
        stats['confusion'] = 0
        stats['schips'] = 0

        return stats

    @classmethod
    def name(cls, hero:dict)    -> str:
        return str(hero['name'])

    @classmethod
    def max_lep(cls, hero:dict) -> tuple:
        lep_max = 0

        # life given from KO-value and additional bought life
        ko_value = cls.attributes(hero=hero, search_for_attr=AttributeID.KO)
        additional_life = cls.attributes(hero=hero)['lp']

        lep_max += ko_value * 2 + additional_life

        # determine race affect on LeP
        race = cls.race(hero)
        if race == Race.Human:
            lep_max += 5
        elif race == Race.Elf:
            lep_max += 2
        elif race == Race.Half_Elf:
            lep_max += 5
        elif race ==Race.Dwarf:
            lep_max += 8

        # advantage/disadvantage effect on LeP
        activatables = cls.activatables(hero)

        if ActivatablesID.HIGH_LEP in activatables['ADV']:  
            lep_max += activatables['ADV'][ActivatablesID.HIGH_LEP][0]['tier']
        elif ActivatablesID.LOW_LEP in activatables['DISADV']:
            lep_max -= activatables['DISADV'][ActivatablesID.LOW_LEP][0]['tier']

        return lep_max
    
    @classmethod
    def min_lep(cls, hero:dict):
        ko_value = cls.attributes(hero=hero, search_for_attr=AttributeID.KO)
        return -ko_value

    @classmethod
    def max_asp(cls, hero:dict):
        asp_max = 0

        asp_max += cls.attributes(hero)['ae']
        
        hero_KL = cls.attributes(hero, search_for_attr=AttributeID.KL)
        hero_CH = cls.attributes(hero, search_for_attr=AttributeID.CH)
        hero_IN = cls.attributes(hero, search_for_attr=AttributeID.IN)

        activatables = cls.activatables(hero)

        adv = activatables['ADV']
        disadv = activatables['DISADV']
        sa =  activatables['SA']
        
        if adv.get(ActivatablesID.HIGH_ASP):  
            asp_max += adv[ActivatablesID.HIGH_ASP][0]['tier']
        if disadv.get(ActivatablesID.LOW_ASP):
            asp_max -= disadv[ActivatablesID.LOW_ASP][0]['tier']
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
    def max_kap(cls, hero:dict):
        kap_max = cls.attributes(hero)['kp']
        

        hero_KL = cls.attributes(hero, search_for_attr=AttributeID.KL)
        hero_CH = cls.attributes(hero, search_for_attr=AttributeID.CH)
        hero_IN = cls.attributes(hero, search_for_attr=AttributeID.IN)
        hero_MU = cls.attributes(hero, search_for_attr=AttributeID.MU)

        # advantages and disadvantages
        activatables = cls.activatables(hero)
        
        adv = activatables['ADV']
        disadv = activatables['DISADV']
        sa =  activatables['SA']
        
        if adv.get(ActivatablesID.HIGH_KAP):
            kap_max += adv[ActivatablesID.HIGH_KAP][0]['tier']
        if disadv.get(ActivatablesID.LOW_KAP):
            kap_max -= disadv[ActivatablesID.LOW_KAP][0]['tier']
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
        if any(key in sa for key in ['SA_685', 'SA_686', 'SA_691', 'SA_694']):
            kap_max += hero_IN
            
            # --- CH --- 
        if any(key in sa for key in ['SA_687', 'SA_692', 'SA_695', 'SA_690']):
            kap_max += hero_CH
        
        return kap_max

    @classmethod
    def wealth(cls, hero:dict):
        return cls.belongings(hero=hero)['purse']

    @classmethod
    def armor(cls, hero:dict, return_weight=False)   -> int:
        items = cls.items(hero=hero)
        for item in items:
            if "armorType" in items[item]:
                return (items[item]['pro'], items[item]['enc']) if return_weight else items[item]['pro']
                    
        return (0, 0) if return_weight else 0

    @classmethod
    def encumrance(cls, hero:dict):
        items = cls.items(hero=hero)
        enc = 0
        for item in items:
            if "armorType" in items[item]:
                enc = items[item]['enc']
        
        if ActivatablesID.REDUCE_ENC in cls.activatables(hero=hero):
            enc -= cls.activatables(hero=hero)[ActivatablesID.REDUCE_ENC][0]['tier']

        enc = enc if enc >= 0 else 0 # reduce but not below zero

        return enc
  
    @classmethod
    def race(cls, hero:dict)    -> str:
        return hero['r']

    @classmethod
    def attributes(cls, hero:dict, search_for_attr=""):
        """Returns all attributes from the hero if search_for_attr is empty or 'all'.
        Specific attributes can be specified with 'AttributeID.<attr>' """

        if search_for_attr == "" or search_for_attr == 'all':
            return hero['attr']
        else:
            for attr in hero['attr']['values']:
                if attr['id'] == search_for_attr:
                    return attr['value']

    @classmethod
    def activatables(cls, hero:dict, detailed=False)    -> dict:
        activatables = {'ADV': dict(), 'DISADV': dict(), "SA": dict()}
        
        if not detailed:
            activatables['ADV'] = {key: val for key, val in hero['activatable'].items() if key.startswith('ADV_')}
            activatables['DISADV'] = {key: val for key, val in hero['activatable'].items() if key.startswith('DISADV_')}
            activatables['SA'] = {key: val for key, val in hero['activatable'].items() if key.startswith('SA_')}
            return activatables


        for act_key, act_val in hero['activatable'].items():
            if act_key.startswith('ADV_'):
                activatables['ADV'][act_key] = act_val
            elif act_key.startswith('DISADV_'):
                activatables['DISADV'][act_key] = act_val
            elif act_key.startswith('SA_'):
                # if value is empty, hero does curently not posess this SA
                if not act_val:
                    continue
                
                # one SA can have multiple variations 
                # e.g there are different languages though they are still the same SA 
                for sa_variation in act_val:
                    # if the length of the dictionary inside the list is > 0 it's an SA with different types (and levels)
                    # e.g. each individual language has a type (which language) and a tier/level
                    if len(sa_variation) > 0:
                        try:
                            sa_vari_keys = sa_variation.keys()
                            # possible keys in dictionary are sid, sid2, tier
                            if 'sid' in sa_vari_keys:
                                sid = sa_variation['sid']
                                if type(sid) == int:
                                    # if sid is numeric it is an option which can be found 
                                    # in the sub-dictionary 'selectOptions' from the special abilities
                                    sid = str(sid)
                                    activatables['SA'][act_key] = SPECIAL_ABILITIES[act_key]

                                    # extensions must be handled differently
                                    if act_key == 'SA_663' or act_key == 'SA_414':
                                        activatables['SA'][act_key].update(SPECIAL_ABILITIES[act_key])
                                        activatables['SA'][act_key]['sid'] = sid
                                    else:
                                        logging.debug(f"{act_key=}, {sa_variation=}, {act_val=}")
                                        activatables['SA'][act_key].update(SPECIAL_ABILITIES[act_key]['selectOptions'][sid])

                                else:
                                    activatable_data = dict()
                                    category = sid.split('_')[0]
                                    if category == "TAL":
                                        activatable_data = SKILLS[sid]
                                    elif category == "LITURGY":
                                        activatable_data = LITURGIES[sid]
                                    elif category == "SPELL":
                                        activatable_data = SPELLS[sid]
                                    elif category == "SA":
                                        activatable_data = SPECIAL_ABILITIES[sid]
                                    else:
                                        activatable_data = {'name': sid}

                                    activatables['SA'][act_key] = activatable_data

                                    if 'sid2' in sa_vari_keys:
                                        sid2 = str(sa_variation['sid2'])
                                        activatables['SA'][act_key]['application'] = SKILLS[sid]['applications'][sid2]
                        except Exception as e:
                            logging.error(f"{e=}, hero={cls.name(hero)}\n")

                        if 'tier' in sa_vari_keys:
                            activatables['SA'][act_key] = SPECIAL_ABILITIES[act_key]
                            activatables['SA'][act_key]['tier'] = sa_variation['tier']
                            
                    else:
                        activatables['SA'][act_key] = SPECIAL_ABILITIES[act_key]
        return activatables

    @classmethod
    def belongings(cls, hero:dict)       -> dict:
        return hero['belongings']

    @classmethod
    def items(cls, hero:dict)       -> dict:
        return hero['belongings']['items']

    @classmethod
    def liturgies(cls, hero:dict)       -> dict:
        hero_liturgies = dict()
        for l in hero['liturgies']:
            lit = LITURGIES.get(l, None)
            if lit is not None:
                lit['FW'] = hero['liturgies'][l]
                hero_liturgies[l] = lit
        return hero_liturgies

    @classmethod
    def blessings(cls, hero:dict) -> dict:
        hero_blessings = dict()
        for bl in hero['blessings']:
            bl_desc = BLESSINGS.get(bl, None)
            if bl_desc is not None:
                hero_blessings[bl] = bl_desc
                
        return hero_blessings

    @classmethod
    def spells(cls, hero:dict)       -> dict:
        hero_spells = dict()
        for spell in hero['spells']:
            spell_desc = SPELLS.get(spell, None)
            if spell_desc is not None:
                hero_spells[spell] = spell_desc
                
        return hero_spells

    @classmethod
    def talents(cls, hero:dict)       -> dict:
        return hero['talents']

    @classmethod
    def initiative(cls, hero:dict):
        mu = cls.attributes(hero=hero, search_for_attr=AttributeID.MU)
        ge = cls.attributes(hero=hero, search_for_attr=AttributeID.GE)
        base_ini = math.ceil((mu + ge) / 2)
        return base_ini - cls.encumrance(hero=hero)

    @classmethod
    def dodge(cls, hero:dict):
        base_dodge = cls.attributes(hero=hero, search_for_attr=AttributeID.GE) / 2
        base_dodge = math.ceil(base_dodge)

        activatables = cls.activatables(hero=hero)
        if ActivatablesID.IMPR_DODGE in activatables:
            impr_dodge = activatables[ActivatablesID.IMPR_DODGE][0]['tier']
        else:
            impr_dodge = 0

        return base_dodge + impr_dodge


class HealthState():
    Dying = 0
    Unconscious = 1
    PainLvl3 = 2
    PainLvl2 = 3
    PainLvl1 = 4
    Healthy = 5


class AttributeID():
    MU = 'ATTR_1'
    KL = 'ATTR_2'
    IN = 'ATTR_3'
    CH = 'ATTR_4'
    FF = 'ATTR_5'
    GE = 'ATTR_6'
    KO = 'ATTR_7'
    KK = 'ATTR_8'
    ALL = 'all'


class ActivatablesID():
    # advantages
    HIGH_ASP = 'ADV_23'
    HIGH_KAP = 'ADV_24'
    HIGH_LEP = 'ADV_25'
    MAGICIAN = 'ADV_50'
    PRIEST = 'ADV_12'
    
    # disadvantages
    LOW_ASP = 'DISADV_26'
    LOW_KAP = 'DISADV_27'
    LOW_LEP = 'DISADV_28'

    # special abilities (fight)
    REDUCE_ENC = 'SA_41'    # Belastungsgewöhnung
    IMPR_DODGE = 'SA_64'


class Race():
    Human       = 'R_1' 		# Lep Base Modifier = 5 //1
    Elf         = 'R_2'         # Lep Base Modifier = 2 //2
    Half_Elf    = 'R_3'         # Lep Base Modifier = 5 //3
    Dwarf       = 'R_4'         # Lep Base Modifier = 8 //4

