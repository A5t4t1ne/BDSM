import os
import yaml
import json


LITURGIES = dict()
BLESSINGS = dict()
ATTRIBUTES = dict()
SPELLS = dict()
SPELL_ENHANCEMENTS = dict()
SKILLS = dict()
SPECIAL_ABILITIES = dict()

DATA_PATH = os.path.dirname(os.path.abspath(__file__))


class DataPath:
    """
    Used for determing the relative file path in the local hero decoding database
    """
    DE_LITURGIES = os.path.join("de-DE", "LiturgicalChants.yaml")
    DE_ATTRIBUTES = os.path.join("de-DE", "Attributes.yaml")
    DE_SPELLS = os.path.join("de-DE", "Spells.yaml")
    DE_BLESSINGS = os.path.join("de-DE", "Blessings.yaml")
    DE_SKILLS = os.path.join("de-DE", "Skills.yaml")
    DE_SPECIAL_ABILITIES = os.path.join("de-DE", "SpecialAbilities.yaml")
    DE_SPELL_ENHANCEMENTS = os.path.join("de-DE", "SpellEnhancements.yaml")

    UNIV_LITURGIES = os.path.join("univ", "LiturgicalChants.yaml")
    UNIV_SPELLS = os.path.join("univ", "Spells.yaml")
    UNIV_SKILLS = os.path.join("univ", "Skills.yaml")
    UNIV_SPECIAL_ABILITIES = os.path.join("univ", "SpecialAbilities.yaml")


def get_yaml_data(file_path) -> list[dict]:
    """
    Get the yaml data of a file in the database folder ('Data')
    
    :param file_path: path to file in Data folder. Use class DataPath
    :return: a yaml-like dictionary"""
    path = os.path.join(DATA_PATH, file_path)
    with open(path, 'r', encoding='utf8') as f:
        return yaml.full_load(f)


def get_attr_data(*args):
    """
    Returns the information based on the attributes given
    
    :param *args: valid attribute id's
    :return: a list of the attribute-info dictionaries
    """
    attributes = []

    for attr_id in args:
        attr = ATTRIBUTES[attr_id]
        attr['ATTR_ID'] = attr_id    
        attributes.append(attr)

    return attributes


def load_attributes():
    """Load all attributes into the ATTRIBUTES constant"""
    for attr in get_yaml_data(DataPath.DE_ATTRIBUTES):
        key = attr['id']
        del attr['id']

        ATTRIBUTES[key] = attr


def load_liturgies():
    """Load all liturgies into the LITURGIES constant"""
    # get all liturgical (german) description
    for lit in get_yaml_data(DataPath.DE_LITURGIES):
        key = lit['id']
        del lit['id']

        LITURGIES[key] = lit

    # get universal data for liturgies
    for lit in get_yaml_data(DataPath.UNIV_LITURGIES):
        key = lit['id']
        del lit['id']
        
        # save detailed information about the check attributes
        lit['check1'], lit['check2'], lit['check3'] = get_attr_data(lit['check1'], lit['check2'], lit['check3'])

        LITURGIES[key]['univ'] = lit # combine general and descriptive data


def load_blessings():
    """Load all blessings into the BLESSING constant"""
    for bl in get_yaml_data(DataPath.DE_BLESSINGS):
        key = bl['id']
        del bl['id']

        BLESSINGS[key] = bl


def load_spells():
    """Load all spells into the SPELLS constant"""
    for spell in get_yaml_data(DataPath.DE_SPELLS):
        key = spell['id']
        del spell['id']

        SPELLS[key] = spell

    for spell in get_yaml_data(DataPath.UNIV_SPELLS):
        key = spell['id']
        del spell['id']

        # save detailed information about the check attributes
        spell['check1'], spell['check2'], spell['check3'] = get_attr_data(spell['check1'], spell['check2'], spell['check3'])

        SPELLS[key]['univ'] = spell # combine general and descriptive data


def load_spell_enhancements():
    for enhancement in get_yaml_data(DataPath.DE_SPELL_ENHANCEMENTS):
        for key in enhancement.keys():
            if key.startswith('level'):
                enh_id = enhancement[key]['id']
                del enhancement[key]['id']

                SPELL_ENHANCEMENTS[enh_id] = enhancement[key]
                SPELL_ENHANCEMENTS[enh_id]['target'] = enhancement['target']
                SPELL_ENHANCEMENTS[enh_id]['level'] = key


def load_skills():
    for skill in get_yaml_data(DataPath.DE_SKILLS):
        key = skill['id']
        del skill['id']

        # applications is a list of dictionaries defining the specific variation of the skill
        # convert the lists to dictionaries too, key is the id
        apps_dict = dict()
        for app in skill['applications']:
            app_id = app['id']
            del app['id']
            
            # not modifying skill['applications'] directly because whe're looping in it
            apps_dict[app_id] = app

        skill['applications'] = apps_dict

        SKILLS[key] = skill

    for skill in get_yaml_data(DataPath.UNIV_SKILLS):
        key = skill['id']
        del skill['id']

        # save detailed information about the check attributes
        skill['check1'], skill['check2'], skill['check3'] = get_attr_data(skill['check1'], skill['check2'], skill['check3'])

        SKILLS[key]['univ'] = skill # combine general and descriptive data


def load_special_abilities():
    """Load all special abilities into the SPECIAL_ABILITES constant"""
    for sa in get_yaml_data(DataPath.DE_SPECIAL_ABILITIES):
        key = sa['id']
        del sa['id']

        if 'selectOptions' in sa.keys():
            options = dict()
            for option in sa['selectOptions']:
                option_id = option['id']
                del option['id']

                options[option_id] = option
            
            sa['selectOptions'] = options

        SPECIAL_ABILITIES[key] = sa

    for sa in get_yaml_data(DataPath.UNIV_SPECIAL_ABILITIES):
        key = sa['id']
        del sa['id']

        SPECIAL_ABILITIES[key]['univ'] = sa



# load_attributes()
# load_liturgies()
# load_blessings()
# load_spells()
# load_skills()
# load_special_abilities()
# load_spell_enhancements()

# with open(os.path.join(DATA_PATH, '..', 'website', 'data', 'SpellEnhancements.json'), 'w', encoding="utf8") as f:
#     json.dump(SPELL_ENHANCEMENTS, f, ensure_ascii=False, sort_keys=True, indent=4)
