import yaml
import os

CURRENT_FILE_PATH = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(CURRENT_FILE_PATH, "..", "Data")

# create dict out of the lists for faster access. Key is the id
LITURGIES = dict()
BLESSINGS = dict()
ATTRIBUTES = dict()
SPELLS = dict()
SPECIAL_ABILITIES = dict()

class DataPath:
    """Use with get_data()"""
    DE_LITURGIES = os.path.join("de-DE", "LiturgicalChants.yaml")
    DE_ATTRIBUTES = os.path.join("de-DE", "Attributes.yaml")
    DE_SPELLS = os.path.join("de-DE", "Spells.yaml")
    DE_BLESSINGS = os.path.join("de-DE", "Blessings.yaml")

    UNIV_LITURGIES = os.path.join("univ", "LiturgicalChants.yaml")
    UNIV_SPELLS = os.path.join("univ", "Spells.yaml")

def get_data(file_path):
    """Returns a read yaml file. Use class 'DataPath' as parameter"""
    path = os.path.join(DATA_PATH, file_path)
    with open(path, 'r', encoding='utf8') as f:
        return yaml.full_load(f)


def update_attributes():
    for attr in get_data(DataPath.DE_ATTRIBUTES):
        key = attr['id']
        del attr['id']

        ATTRIBUTES[key] = attr


def update_liturgies():
    """update all liturgies"""
    # get all liturgical (german) description
    for lit in get_data(DataPath.DE_LITURGIES):
        key = lit['id']
        del lit['id']

        LITURGIES[key] = lit

    # get universal data for liturgies
    for lit in get_data(DataPath.UNIV_LITURGIES):
        key = lit['id']
        del lit['id']
        
        if "check1" in lit.keys(): # check if the current liturgy contains dice checks
            # save description of checks instead of just the id
            for i in range(1, 4):
                c = f"check{i}"
                attr_id = lit[c] # initial id of dice check
                lit[c] = ATTRIBUTES[attr_id] # extended information about the dice checks
                lit[c]['ATTR_ID'] = attr_id # still save the id number besides the other information

        LITURGIES[key]['univ'] = lit # combine general and descriptive data



def update_blessings():
    # add blessings
    for bl in get_data(DataPath.DE_BLESSINGS):
        key = bl['id']
        del bl['id']

        BLESSINGS[key] = bl


def update_spells():
    for spell in get_data(DataPath.DE_SPELLS):
        key = spell['id']
        del spell['id']

        SPELLS[key] = spell

    for spell in get_data(DataPath.UNIV_SPELLS):
        key = spell['id']
        del spell['id']

        SPELLS[key]['univ'] = spell # combine general and descriptive data

def update_special_abilities():
    pass



update_attributes()
update_liturgies()
update_blessings()
update_spells()