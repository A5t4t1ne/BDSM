import yaml
import os

CURRENT_FILE_PATH = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(CURRENT_FILE_PATH, "..", "Data")

# create dict out of the lists for faster access. Key is the individual id
LITURGIES = dict()
ATTRIBUTES = dict()

class DataFilePath:
    """Use with get_data()"""
    DE_LITURGIES = os.path.join("de-DE", "LiturgicalChants.yaml")
    DE_ATTRIBUTES = os.path.join("de-DE", "Attributes.yaml")

    UNIV_LITURGIES = os.path.join("univ", "LiturgicalChants.yaml")


def get_data(file_path):
    """Use class FilePath as parameter"""
    path = os.path.join(DATA_PATH, file_path)
    with open(path, 'r', encoding='utf8') as f:
        return yaml.full_load(f)


def update_attributes():
    for attr in get_data(DataFilePath.DE_ATTRIBUTES):
        key = attr['id']
        del attr['id']

        ATTRIBUTES[key] = attr


def update_liturgies():
    for lit in get_data(DataFilePath.DE_LITURGIES):
        key = lit['id']
        del lit['id']

        LITURGIES[key] = lit

    for lit in get_data(DataFilePath.UNIV_LITURGIES):
        key = lit['id']
        del lit['id']
        if "check1" in lit.keys():
            attr_id1, attr_id2, attr_id3 = lit['check1'], lit['check2'], lit['check3']
            lit['check1'] = ATTRIBUTES[lit['check1']]
            lit['check2'] = ATTRIBUTES[lit['check2']]
            lit['check3'] = ATTRIBUTES[lit['check3']]
            lit['check1']['ATTR_ID'] = attr_id1
            lit['check2']['ATTR_ID'] = attr_id2
            lit['check3']['ATTR_ID'] = attr_id3
        LITURGIES[key].update(lit)
        

update_attributes()
update_liturgies()