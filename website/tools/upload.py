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
    if not is_valid_file_type(file.filename):
        return False

    file_path = os.path.join(current_user.heroes_path, secure_filename(file.filename))

    file.save(file_path)

    with open(file_path, 'w') as f:
        hero = json.load(f)

    if not 'name' in hero:
        return False

    hero_name = hero['name']
    new_hero = Hero(hero_name=hero_name, hero_path=file_path, user_id=current_user.id)
    db.session.add(new_hero)
