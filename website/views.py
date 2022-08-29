from flask import Blueprint, flash, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from . import app
from .models import Hero
from .tools.upload import UploadFileForm, save_hero
import os


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


@views.route('/play', methods=['GET', 'REQUEST'])
@login_required
def play():
    return render_template("play.html", user=current_user)

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