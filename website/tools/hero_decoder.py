import json
import os
from typing import overload


class HeroDecoder():
    @classmethod
    def is_valid_hero(cls, hero:dict):
        """checks if all the necessary attributes are present"""

        # convert version X.Y.Z to XY
        version = hero['clientVersion'].split('.')[:2]
        version = int(version[0])*10 + int(version[1])

        name = hero.get('name', None)
        attr = hero.get('attr', None)
        race = hero.get('r', None)
        acti = hero.get('activatable', None)
        
        return version > 10 and \
            name != "" and \
            name != None and \
            attr != None and \
            race != None and \
            acti != None

    @classmethod
    def decode_save(cls, hero:dict):
        hero_stats = cls.decode_all(hero)

        # TODO: implement save-process

    @classmethod
    def decode_all(cls, hero:dict)     ->  dict:
        """calculates all possible stats from the hero and returns them in a dictionary

        :param hero     the DSA hero in a dict format
        """
        stats = dict()
        stats['lp_max'], stats['lep_min'] = cls.lep(hero=hero)
        stats['asp'] = cls.asp(hero=hero)
        # stats['kap'] = cls.kap(hero=hero)
        # stats['wealth'] = cls.wealth(hero=hero)
        # stats['encumbrance'] = cls.encumbrance(hero=hero)
        # stats['armor'] = cls.armor(hero=hero)
        # stats['health_state'] = cls.health_state(hero=hero)

        return stats

    @classmethod
    def name(cls, hero:dict)    -> str:
        return str(hero['name'])

    @classmethod
    def lep(cls, hero:dict) -> tuple:
        """returns a tuple with the max and min LeP values"""
        lep_max = 0
        lep_min = 0

        # life given from KO-value and additional bought life
        ko_value = cls.attributes(hero=hero, search_for_attr=AttributeID.KO)
        additional_life = cls.attributes(hero=hero)['lp']

        lep_max += ko_value * 2 + additional_life
        lep_min -= ko_value


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

        return lep_max, lep_min
    
    @classmethod
    def asp(cls, hero:dict):
        asp_max = 0

        asp_max += cls.attributes(hero)['ae']
        
        # advantages and disadvantages
        adv_disadv = cls.activatables(hero)

        if ActivatablesID.HIGH_ASP in adv_disadv:
            asp_max += adv_disadv[ActivatablesID.HIGH_ASP][0]['tier']
        elif ActivatablesID.LOW_ASP in adv_disadv:
            asp_max -= adv_disadv[ActivatablesID.LOW_ASP][0]['tier']

        return asp_max


    @classmethod
    def kap(cls, hero:dict):
        pass

    @classmethod
    def wealth(cls, hero:dict):
        pass

    @classmethod
    def encumbrance(cls, hero:dict):
        pass

    @classmethod
    def armor(cls, hero:dict):
        pass

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
    def items(cls, hero:dict)       -> dict:
        return hero['belongings']

    @classmethod
    def defence(cls, hero:dict):
        # TODO: implement defence value
        pass

    @classmethod
    def dodge(cls, hero:dict):
        # TODO: implement dodge value, mind improved dodge (good source: Ramon)
        pass

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
    
    # disadvantages
    LOW_ASP = 'DISADV_26'
    LOW_KAP = 'DISADV_27'
    LOW_LEP = 'DISADV_28'


class Race():
    Human       = 'R_1' 		# Lep Base Modifier = 5 //1
    Elf         = 'R_2'         # Lep Base Modifier = 2 //2
    Half_Elf    = 'R_3'         # Lep Base Modifier = 5 //3
    Dwarf       = 'R_4'         # Lep Base Modifier = 8 //4


# only for testing purposes
# TODO: remove later
# if __name__ == "__main__":
#     abdul_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', 'hero-examples', 'abdul.json')
#     beril_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', 'hero-examples', 'beril.json')
#     kunhang_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', 'hero-examples', 'kunhang.json')
#     patrizius_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', 'hero-examples', 'patrizius.json')
    
#     with open(abdul_path, 'r') as f:
#         abdul = json.load(f)

#     with open(beril_path, 'r') as f:
#         beril = json.load(f)

#     with open(kunhang_path, 'r') as f:
#         kunhang = json.load(f)

#     with open(patrizius_path, 'r') as f:
#         patrizius = json.load(f)


#     stats = HeroDecoder.decode_all(patrizius)

#     for s in stats:
#         print(f'{s}: {stats[s]}')

