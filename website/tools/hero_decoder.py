class HeroDecoder():
    @classmethod
    def decode_all(hero:dict)     ->  dict:
        """calculates all possible stats from the hero and returns them in a dictionary

        :param hero     the DSA hero in a dict format
        """
        stats = dict()
        stats['lp'] = HeroDecoder.get_lp(hero=hero)
        stats['asp'] = HeroDecoder.get_asp(hero=hero)
        stats['kap'] = HeroDecoder.get_kap(hero=hero)
        stats['wealth'] = HeroDecoder.get_wealth(hero=hero)
        stats['encumbrance'] = HeroDecoder.get_encumbrance(hero=hero)
        stats['armor'] = HeroDecoder.get_armor(hero=hero)
        stats['health_state'] = HeroDecoder.get_health_state(hero=hero)

        return stats

    @classmethod
    def get_lp(hero:dict):
        pass
    
    @classmethod
    def get_asp(hero:dict):
        pass

    @classmethod
    def get_kap(hero:dict):
        pass

    @classmethod
    def get_wealth(hero:dict):
        pass

    @classmethod
    def get_encumbrance(hero:dict):
        pass

    @classmethod
    def get_armor(hero:dict):
        pass

    @classmethod
    def get_health_state(hero:dict):
        pass