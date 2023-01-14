import yaml
import os

path = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(path, "..", "Data", "de-DE", "LiturgicalChants.yaml")
with open(path, 'r') as f:
    liturgies_lists = yaml.full_load(f)


LITURGIES = dict()
for i, l in enumerate(liturgies_lists):
    key = l['id']
    del l['id']

    LITURGIES[key] = l
