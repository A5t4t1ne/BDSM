import json
import os
import math


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
        stats['kap'] = cls.kap(hero=hero)
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
        
        print(f'1. current asp: {asp_max}')

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
                    print(f'2. current asp: {asp_max}')

                case ActivatablesID.LOW_ASP:
                    asp_max -= property_list[0]['tier']
                    print(f'3. current asp: {asp_max}')

                case ActivatablesID.IS_MAGIC:
                    asp_max += 20
                    print(f'4. current asp: {asp_max}')

                # advantages that affect asp based on a character property
                # --- KL --- 
                case "SA_70" | "SA_346" | "SA_681":
                    asp_max += hero_KL
                    print(f'5. current asp: {asp_max}')

                # --- KL / 2, round up ---
                case "SA_750":
                    asp_max += math.ceil(hero_KL / 2)
                    print(f'6. current asp: {asp_max}')

                # --- IN --- 
                case "SA_345":
                    asp_max += hero_IN
                    print(f'7. current asp: {asp_max}')

                # --- CH --- 
                case "SA_255" | "SA_676":
                    asp_max += hero_CH
                    print(f'8. current asp: {asp_max}')

                # --- CH / 2, round up ---
                case "SA_677":
                    asp_max += math.ceil(hero_CH / 2)
                    print(f'9. current asp: {asp_max}')
        print(f'10. current asp: {asp_max}')
        return asp_max


    @classmethod
    def kap(cls, hero:dict):
        kap_max = 0

        kap_max += cls.attributes(hero)['kp']
        
        # print(f'1. current asp: {kap}')

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
                    # print(f'2. current kap: {kap_max}')

                case ActivatablesID.LOW_KAP:
                    kap_max -= property_list[0]['tier']
                    # print(f'3. current kap: {kap_max}')

                case ActivatablesID.IS_HOLY:
                    kap_max += 20

                # advantages that affect kap based on a character property
                # --- MU --- 
                case "SA_682" | "SA_683" | "SA_689" | "SA_693" | "SA_696" | "SA_698":
                    kap_max += hero_MU
                    # print(f'5. current kap: {kap_max}')

                # --- KL --- 
                case "SA_86" | "SA_684" | "SA_688" | "SA_697" | "SA_1049":
                    kap_max += hero_KL
                    # print(f'5. current kap: {kap_max}')

                # --- IN --- 
                case "SA_685" | 'SA_686' | "SA_691" | 'SA_694':
                    kap_max += hero_IN
                    # print(f'7. current kap: {kap_max}')

                # --- CH --- 
                case "SA_687" | "SA_692" | 'SA_695' | 'SA_690':
                    kap_max += hero_CH
                    # print(f'8. current kap: {kap_max}')
        
        return kap_max

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
        # TODO: implement dodge value, mind improved dodge (test object: Ramon)
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


# only for testing purposes
# TODO: remove later
if __name__ == "__main__":
    peris_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', 'hero-examples', 'peris.json')
    beril_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', 'hero-examples', 'beril.json')
    aldarine_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', 'hero-examples', 'aldarine.json')
    patrizius_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', 'hero-examples', 'patrizius.json')
    
    with open(peris_path, 'r') as f:
        peris = json.load(f)

    with open(beril_path, 'r') as f:
        beril = json.load(f)

    with open(aldarine_path, 'r') as f:
        aldarine = json.load(f)

    with open(patrizius_path, 'r') as f:
        patrizius = json.load(f)


    stats = HeroDecoder.decode_all(aldarine)

    for s in stats:
        print(f'{s}: {stats[s]}')

