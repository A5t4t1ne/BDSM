from ..src.website.tools.decode import Decode
import os
import json
import logging

def test_decode():
    path = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(path, "..", "src", "heroes", "aldarine.json")
    with open(path) as f:
        hero = json.load(f)
    output = Decode.initiative(hero)
    logging.log(output)
    assert output != ""


if __name__ == "__main__":
    test_decode()