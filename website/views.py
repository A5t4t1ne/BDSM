from flask import Blueprint, flash, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from . import db
from . import app
from .models import Note
from .tools.upload import UploadFileForm, secure_save


views = Blueprint("views", __name__)


@views.route('/', methods=['GET', 'POST'])
@views.route("/home", methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        if 'add_note' in request.form:
            note_txt = request.form.get('note')

            if len(note_txt) < 1:
                flash('Msg too short', category='error')
            else:
                new_note = Note(data=note_txt, user_id= current_user.id)
                db.session.add(new_note)
                db.session.commit()

    return render_template("home.html", user=current_user)



@views.route('/overview', methods=['GET', 'POST'])
@login_required
def hero_overview():
    form = UploadFileForm()

    if form.validate_on_submit():
        invalid_files = []
        for file in form.files.data:
            if not secure_save(file):
                invalid_files.append(file.filename)
        
        if len(invalid_files) > 0:
            invalid_files_msg = ', '.join(invalid_files)
            flash(f'These files are not valid: {invalid_files_msg}')

    return render_template('overview.html', user=current_user, form=form)


@app.errorhandler(413)
def too_large(e):
    flash("File to large", category='error')
