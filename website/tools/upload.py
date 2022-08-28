from fileinput import filename
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField, MultipleFileField
from werkzeug.utils import secure_filename
from .. import app, db
from ..models import Hero
import json
import os

class UploadFileForm(FlaskForm):
    files = MultipleFileField('File(s) upload')
    submit = SubmitField("Commit")


def is_valid_hero(file):
    filename = file.filename

    hero = json.load(file)

    if '.' not in filename or \
        filename.rsplit('.', 1)[1].lower() not in app.config['ALLOWED_EXTENSIONS']:
        return False

    print("2. Step")

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


def secure_save(file):
    """Takes care of eventual dangerous file saving scenarios

    This function makes sure the file type is correct, the filename is not malicious 
    and checks if the uploaded file is a valid DSA hero file. 
    In the end the important data will be stored in a new file in another location together
    with a new entry in the database.
    
    file:     raw file
    """
    if not is_valid_hero(file):
        return False

    # TODO: change to directly create new file and never save the given one

    # file_path = os.path.join(current_user.heroes_path, secure_filename(file.filename))

    # file.save(file_path)

    # with open(file_path, 'r') as f:
    #     hero = json.load(f)


    # hero_name = hero['name']
    # new_hero = Hero(hero_name=hero_name, hero_path=file_path, user_id=current_user.id)
    # db.session.add(new_hero)
    return True
