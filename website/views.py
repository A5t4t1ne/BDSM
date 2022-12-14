from flask import Blueprint, flash, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from . import app, db
from .models import Hero, User
from .tools.upload import UploadFileForm, save_hero
import os
import json


views = Blueprint("views", __name__)


@views.route('/')
@views.route("/home")
def home():
    return render_template("home.html", user=current_user)


@views.route('/overview', methods=['GET', 'POST'])
@login_required
def overview():
    form = UploadFileForm()

    if form.validate_on_submit():
        invalid_files = []
        for file in form.files.data:
            if not save_hero(file):
                invalid_files.append(file.filename)

        if len(invalid_files) > 0:
            invalid_file_names = ', '.join(invalid_files)
            flash(f'These files are not valid: {invalid_file_names}', category='error')
        else:
            flash("Files uploaded successfully", category='success')


    
    return render_template('overview.html', user=current_user, form=form)


@views.route('/account')
def account():
    return render_template('account.html', user=current_user)


@views.route('/play')
@login_required
def play():
    return render_template("play.html", user=current_user)


@views.route('data-request', methods=['POST'])
def data_request():
    data = request.get_json()
    hero = Hero.query.filter_by(user_id=current_user.id, secure_name=data['name']).first()
    if hero:
        return jsonify(hero.stats)
    else:
        return jsonify(None)


@views.route('save-hero', methods=['POST'])
def save_hero_from_request():
    request_data = request.get_json()
    hero = Hero.query.filter_by(user_id=current_user.id, secure_name=request_data['name']).first()
    if hero:
        with open(hero.path, 'r') as f:
            hero_data = json.load(f)

        for key, item in request_data.items():
            hero_data[key] = item
        
        with open(hero.path, 'w') as f:
            json.dump(hero_data, f)
        
        hero.stats = hero_data
        db.session.commit()

        return jsonify(error=0)
    
    return jsonify(error=-1)



@views.route('delete-hero',methods=['POST'])
def delete_hero():
    data = request.get_json()
    hero = Hero.query.filter_by(user_id=current_user.id, secure_name=data['name'])
    hero_path = hero.first().path
    
    if not hero_path:
        # no valid hero
        return jsonify(error=-1)

    if os.path.isfile(hero_path):
        os.remove(hero_path)

    # Hero.query.filter_by(id=data['id']).delete()
    hero.delete()
    db.session.commit()

    return jsonify(error=0)


# Server request size to large
@app.errorhandler(413)
def too_large(e):
    flash("Upload size too large", category='error')
    return redirect(url_for("views.overview"))

# wrong url
@app.errorhandler(404)
def page_not_found(e):
    return "<h1>Page not found</h1>"

#internal server error
@app.errorhandler(500)
def page_not_found(e):
    return "<h1>Internal server error</h1>"

