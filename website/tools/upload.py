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

    file.seek(0)    # if file was read before cursor isn't at the beginning -> data cannot be read correctly 
    hero = json.load(file)

    # convert version X.Y.Z to XY
    version = hero['clientVersion'].split('.')[:2]
    version = int(version[0])*10 + int(version[1])

    name = hero.get('name', None)
    attr = hero.get('attr', None)
    race = hero.get('r', None)
    acti = hero.get('activatable', None)
    belo = hero.get('belongings', None)
    
    return version > 10 and \
        name != "" and \
        name != None and \
        attr != None and \
        race != None and \
        acti != None and \
        belo != None


def save_hero(file):
    """Returns False if the file isn't a valid hero file"""
    if not is_valid_hero(file):
        return False

    file.seek(0)    # if file was read before cursor isn't at the beginning -> data cannot be read correctly 
    raw_hero = json.load(file)

    shortened_hero = Decode.decode_all(raw_hero)

    file_name = secure_filename(shortened_hero['name']).lower()
    file_path = os.path.join(current_user.heroes_path, file_name + '.json')
    
    while os.path.isfile(file_path):
        # when file exists handle it the same way as windows does -> file.json, file(1).json, file(2).json ...

        # check if there are brackets with a number between it at the end
        if '(' in file_name and ')' == file_name[-1]:
            content_between_brackets = file_name.rsplit('(', 1)[1][:-1]
            if content_between_brackets.isnumeric():
                file_number = int(content_between_brackets) + 1
                file_name = file_name.rsplit('(', 1)[0] + f'({file_number})'
            else:
                file_name += '(1)'
        else:
            file_name += '(1)'

        file_path = os.path.join(current_user.heroes_path, file_name + '.json')
    

    with open(file_path, 'w') as f:
        json.dump(shortened_hero, f)


    new_hero = Hero(name=shortened_hero['name'], path=file_path, user_id=current_user.id)
    db.session.add(new_hero)

    return True
