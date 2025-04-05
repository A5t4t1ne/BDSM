from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import SubmitField, MultipleFileField
from werkzeug.utils import secure_filename
from .decode import Decode
from .. import app, db
from ..models import Hero
import json
import os


class UploadFileForm(FlaskForm):
    files = MultipleFileField('File(s) upload')
    submit = SubmitField("Commit")


def is_valid_hero(file):
    filename = file.filename

    if '.' not in filename or \
            filename.rsplit('.', 1)[1].lower() not in app.config['ALLOWED_EXTENSIONS']:
        return False

    # if file was read before cursor isn't at the beginning -> data cannot be read correctly
    file.seek(0)
    hero = json.load(file)

    if not 'clientVersion' in hero:
        return False

    # convert version X.Y.Z to XY
    version_list = hero['clientVersion'].split('.')
    if len(version_list) < 2:
        return False
    elif len(version_list) == 2:
        version = Version(int(version_list[0]), int(version_list[1]), 0)
    elif len(version_list) >= 3:
        version = Version(int(version_list[0]), int(
            version_list[1]), int(version_list[2]))

    name = hero.get('name', None)
    attr = hero.get('attr', None)
    race = hero.get('r', None)
    acti = hero.get('activatable', None)
    belo = hero.get('belongings', None)

    return version.major >= 1 and \
        name != "" and \
        name != None and \
        attr != None and \
        race != None and \
        acti != None and \
        belo != None


def save_hero(file):
    """Checks if the file is a valid hero and saves it afterwards"""

    if not is_valid_hero(file):
        return False

    # if file was read before, cursor isn't at the beginning -> data cannot be read correctly
    file.seek(0)
    raw_hero: dict() = json.load(file)
    decoded_hero = Decode.decode_all(raw_hero)
    print(decoded_hero['name'])
    # user hero name for file name
    hero_name = secure_filename(decoded_hero['name']).lower()
    file_path = os.path.join(current_user.heroes_path, hero_name + '.json')

    while os.path.isfile(file_path):
        # if file exists handle it with incrementing numbers -> file.json, file(1).json, file(2).json ...

        # check if there are brackets with a number between it at the end of the filename
        if '(' in hero_name and ')' == hero_name[-1]:
            content_between_brackets = hero_name.rsplit('(', 1)[1][:-1]
            if content_between_brackets.isnumeric():
                file_number = int(content_between_brackets) + 1
                hero_name = hero_name.rsplit('(', 1)[0] + f'({file_number})'

                decoded_hero['name'] = decoded_hero['name'].rsplit(
                    '(', 1)[0] + f'({file_number})'
            else:
                hero_name += '(1)'
                decoded_hero['name'] += '(1)'
        else:
            hero_name += '(1)'
            decoded_hero['name'] += '(1)'

        file_path = os.path.join(current_user.heroes_path, hero_name + '.json')

    decoded_hero['secure_name'] = hero_name
    decoded_hero['avatar-img'] = raw_hero.get('avatar', '')

    # save shortened hero as new file on given path in initialization
    with open(file_path, 'w') as f:
        json.dump(decoded_hero, f)

    # add hero to database
    new_hero = Hero(name=decoded_hero['name'], secure_name=hero_name,
                    path=file_path, stats=decoded_hero, user_id=current_user.id)
    db.session.add(new_hero)
    db.session.commit()

    return True


class Version():
    major = 0
    minor = 0
    bugfix = 0

    def __init__(self, major, minor=0, bugfix=0) -> None:
        self.major = major
        self.minor = minor
        self.bugfix = bugfix
