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


def is_valid_file_type(filename:str):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']


def secure_save(file):
    """Takes care of eventual dangerous file saving scenarios

    This function makes sure the file type is correct, the filename is not malicious 
    and checks if the uploaded file is a valid DSA hero file. 
    In the end the important data will be stored in a new file in another location together
    with a new entry in the database 
    
    file:     raw file
    """
    if not is_valid_file_type(file.filename):
        return False

    file_path = os.path.join(current_user.heroes_path, secure_filename(file.filename))

    file.save(file_path)

    with open(file_path, 'r') as f:
        hero = json.load(f)

    # print(f"\n\nHero data: {hero}\n\n")

    if not 'name' in hero:
        return False

    # hero_name = hero['name']
    # new_hero = Hero(hero_name=hero_name, hero_path=file_path, user_id=current_user.id)
    # db.session.add(new_hero)
    return True
