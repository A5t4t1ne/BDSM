import yaml
import os
import logging
import json
logging.basicConfig(level=logging.DEBUG)

CURRENT_FILE_PATH = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(CURRENT_FILE_PATH, "..", "Data")

# create dict out of the lists for faster access. Key is the id
LITURGIES = dict()
BLESSINGS = dict()
ATTRIBUTES = dict()
SPELLS = dict()
SKILLS = dict()
SPECIAL_ABILITIES = dict()


dir_name = os.path.dirname(os.path.abspath(__file__))
dir_name = os.path.join(dir_name, 'data')


with open(os.path.join(dir_name,'Liturgies.json'), 'r', encoding="utf8") as f:
    LITURGIES = json.load(f)    

with open(os.path.join(dir_name,'Blessings.json'), 'r', encoding="utf8") as f:
    BLESSINGS = json.load(f)    

with open(os.path.join(dir_name,'Attributes.json'), 'r', encoding="utf8") as f:
    ATTRIBUTES = json.load(f)    

with open(os.path.join(dir_name,'Spells.json'), 'r', encoding="utf8") as f:
    SPELLS = json.load(f)    

with open(os.path.join(dir_name,'Skills.json'), 'r', encoding="utf8") as f:
    SKILLS = json.load(f)    

with open(os.path.join(dir_name,'SpecialAbilities.json'), 'r', encoding="utf8") as f:
    SPECIAL_ABILITIES = json.load(f)    