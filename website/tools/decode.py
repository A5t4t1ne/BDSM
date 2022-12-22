import json
import os
import math


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
        stats['ini'] = cls.initiative(hero)

        # initialize hero effects
        stats['desire'] = 0
        stats['intoxication'] = 0
        stats['anaesthesia'] = 0
        stats['fear'] = 0
        stats['paralysis'] = 0
        stats['pain'] = 0
        stats['confusion'] = 0

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

            if key == ActivatablesID.HIGH_ASP:
                asp_max += property_list[0]['tier']

            elif key == ActivatablesID.LOW_ASP:
                asp_max -= property_list[0]['tier']

            elif key == ActivatablesID.MAGICIAN:
                asp_max += 20

                # advantages that affect asp based on a character property
                # --- KL --- 
            elif key == "SA_70" or key == "SA_346" or key == "SA_681":
                asp_max += hero_KL

                # --- KL / 2, round up ---
            elif key == "SA_750":
                asp_max += math.ceil(hero_KL / 2)

                # --- IN --- 
            elif key == "SA_345":
                asp_max += hero_IN

                # --- CH --- 
            elif key == "SA_255" or key == "SA_676":
                asp_max += hero_CH

                # --- CH / 2, round up ---
            elif key == "SA_677":
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

            
            if key == ActivatablesID.HIGH_KAP:
                kap_max += property_list[0]['tier']

            elif key == ActivatablesID.LOW_KAP:
                kap_max -= property_list[0]['tier']

            elif key == ActivatablesID.PRIEST:
                kap_max += 20

                # advantages that affect kap based on a character property
                # --- MU --- 
            elif key == "SA_682" or key == "SA_683" or key == "SA_689" or key == "SA_693" or key == "SA_696" or key == "SA_698":
                kap_max += hero_MU

                # --- KL --- 
            elif key == "SA_86" or key == "SA_684" or key == "SA_688" or key == "SA_697" or key == "SA_1049":
                kap_max += hero_KL

                # --- IN --- 
            elif key == "SA_685" or key == 'SA_686' or key == "SA_691" or key == 'SA_694':
                kap_max += hero_IN

                # --- CH --- 
            elif key == "SA_687" or key == "SA_692" or key == 'SA_695' or key == 'SA_690':
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
        for item in items:
            if "armorType" in items[item]:
                return items[item]['enc']
                    
        return 0
  
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
    def activatables(cls, hero:dict)    -> dict:
        return hero['activatable']

    @classmethod
    def belongings(cls, hero:dict)       -> dict:
        return hero['belongings']

    @classmethod
    def items(cls, hero:dict)       -> dict:
        return hero['belongings']['items']

    @classmethod
    def liturgies(cls, hero:dict)       -> dict:
        return hero['liturgies']

    @classmethod
    def spells(cls, hero:dict)       -> dict:
        return hero['spells']

    @classmethod
    def talents(cls, hero:dict)       -> dict:
        return hero['talents']

    @classmethod
    def initiative(cls, hero:dict):
        mu = cls.attributes(hero=hero, search_for_attr=AttributeID.MU)
        ge = cls.attributes(hero=hero, search_for_attr=AttributeID.GE)
        base_ini = (mu + ge) / 2
        return base_ini - cls.encumrance(hero=hero)

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


class Race():
    Human       = 'R_1' 		# Lep Base Modifier = 5 //1
    Elf         = 'R_2'         # Lep Base Modifier = 2 //2
    Half_Elf    = 'R_3'         # Lep Base Modifier = 5 //3
    Dwarf       = 'R_4'         # Lep Base Modifier = 8 //4


if __name__ == "__main__":
    with open('heroes\\Torjin.json') as f:
        hero = json.load(f)
    print(Decode.armor(hero, True))
    print(Decode.encumrance(hero))