from flask import Blueprint, flash, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from . import db
from .models import Note
from .tools.upload import UploadFileForm, save_hero


views = Blueprint("views", __name__)


@views.route('/', methods=['GET', 'POST'])
@views.route("/home", methods=['GET', 'POST'])
@login_required
def home():
    upload_form = UploadFileForm()

    if request.method == 'POST':
        if 'add_note' in request.form:
            note_txt = request.form.get('note')

            if len(note_txt) < 1:
                flash('Msg too short', category='error')
            else:
                new_note = Note(data=note_txt, user_id= current_user.id)
                db.session.add(new_note)
                db.session.commit()

        if upload_form.validate_on_submit():
            save_hero(upload_form.file.data)


    return render_template("home.html", user=current_user, upload_form=upload_form)
