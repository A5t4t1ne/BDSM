import json
import os
import math


class Decode():
    @classmethod
    def decode_all(cls, hero:dict)     ->  dict:
        """calculates all possible stats from the hero and returns them in a dictionary

        :param hero     the DSA hero in a dict format
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
        match cls.race(hero):
            case Race.Human:
                lep_max += 5
            case Race.Elf:
                lep_max += 2
            case Race.Half_Elf:
                lep_max += 5
            case Race.Dwarf:
                lep_max += 8

        # advantage/disadvantage effect on LeP
        adv_disadv = cls.activatables(hero)

        # High LeP
        if ActivatablesID.HIGH_LEP in adv_disadv:  
            lep_max += adv_disadv[ActivatablesID.HIGH_LEP][0]['tier']
        # Low LeP
        elif ActivatablesID.LOW_LEP in adv_disadv:
            lep_max -= adv_disadv[ActivatablesID.LOW_LEP][0]['tier']

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

        # advantages and disadvantages
        activatables = cls.activatables(hero)
        for key in activatables:
            # if found property-list is empty adv/disadv isn't in effect
            property_list = activatables[key]
            if len(property_list) < 1:
                continue

            match key:
                case ActivatablesID.HIGH_ASP:
                    asp_max += property_list[0]['tier']

                case ActivatablesID.LOW_ASP:
                    asp_max -= property_list[0]['tier']

                case ActivatablesID.IS_MAGIC:
                    asp_max += 20

                # advantages that affect asp based on a character property
                # --- KL --- 
                case "SA_70" | "SA_346" | "SA_681":
                    asp_max += hero_KL

                # --- KL / 2, round up ---
                case "SA_750":
                    asp_max += math.ceil(hero_KL / 2)

                # --- IN --- 
                case "SA_345":
                    asp_max += hero_IN

                # --- CH --- 
                case "SA_255" | "SA_676":
                    asp_max += hero_CH

                # --- CH / 2, round up ---
                case "SA_677":
                    asp_max += math.ceil(hero_CH / 2)

        return asp_max

    @classmethod
    def max_kap(cls, hero:dict):
        kap_max = 0

        kap_max += cls.attributes(hero)['kp']
        

        hero_KL = cls.attributes(hero, search_for_attr=AttributeID.KL)
        hero_CH = cls.attributes(hero, search_for_attr=AttributeID.CH)
        hero_IN = cls.attributes(hero, search_for_attr=AttributeID.IN)
        hero_MU = cls.attributes(hero, search_for_attr=AttributeID.MU)

        # advantages and disadvantages
        activatables = cls.activatables(hero)
        for key in activatables:
            # if found property-list is empty adv/disadv isn't active
            property_list = activatables[key]
            if len(property_list) < 1:
                continue

            match key:
                case ActivatablesID.HIGH_KAP:
                    kap_max += property_list[0]['tier']

                case ActivatablesID.LOW_KAP:
                    kap_max -= property_list[0]['tier']

                case ActivatablesID.IS_HOLY:
                    kap_max += 20

                # advantages that affect kap based on a character property
                # --- MU --- 
                case "SA_682" | "SA_683" | "SA_689" | "SA_693" | "SA_696" | "SA_698":
                    kap_max += hero_MU

                # --- KL --- 
                case "SA_86" | "SA_684" | "SA_688" | "SA_697" | "SA_1049":
                    kap_max += hero_KL

                # --- IN --- 
                case "SA_685" | 'SA_686' | "SA_691" | 'SA_694':
                    kap_max += hero_IN

                # --- CH --- 
                case "SA_687" | "SA_692" | 'SA_695' | 'SA_690':
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
    def race(cls, hero:dict)    -> str:
        return hero['r']

    @classmethod
    def attributes(cls, hero:dict, search_for_attr=""):
        # if specific attribute isn't given, return all in list form, else return value
        if search_for_attr == "" or search_for_attr == 'all':
            return hero['attr']
        else:
            for attr in hero['attr']['values']:
                if attr['id'] == search_for_attr:
                    return attr['value']


    @classmethod
    def activatables(cls, hero:dict)    -> dict:
        return hero['activatable']

    @classmethod
    def belongings(cls, hero:dict)       -> dict:
        return hero['belongings']

    @classmethod
    def items(cls, hero:dict)       -> dict:
        return hero['belongings']['items']

    @classmethod
    def defence(cls, hero:dict):
        # TODO: implement defence value
        pass

    @classmethod
    def dodge(cls, hero:dict):
        # TODO: implement dodge value, mind improved dodge (test object: Ramon)
        pass


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


class ActivatablesID():
    # advantages
    HIGH_ASP = 'ADV_23'
    HIGH_KAP = 'ADV_24'
    HIGH_LEP = 'ADV_25'
    IS_MAGIC = 'ADV_50'
    IS_HOLY = 'ADV_12'
    
    # disadvantages
    LOW_ASP = 'DISADV_26'
    LOW_KAP = 'DISADV_27'
    LOW_LEP = 'DISADV_28'


class Race():
    Human       = 'R_1' 		# Lep Base Modifier = 5 //1
    Elf         = 'R_2'         # Lep Base Modifier = 2 //2
    Half_Elf    = 'R_3'         # Lep Base Modifier = 5 //3
    Dwarf       = 'R_4'         # Lep Base Modifier = 8 //4


