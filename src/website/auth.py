from pathlib import Path
from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User, Level
from . import db
from . import app
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_required, login_user, logout_user, current_user
import string
import os

auth = Blueprint('auth', __name__)

LOWER_CHARS = 'abcdefghijklmnopqrstuvwxyzäöü'
UPPER_CHARS = LOWER_CHARS.upper()
NUMBERS = '1234567890'
ALLOWED_SPECIAL_CHARS = '&$?!-_'
PASSWD_CHARS = LOWER_CHARS + UPPER_CHARS + NUMBERS + ALLOWED_SPECIAL_CHARS
UNAME_CHARS = LOWER_CHARS + UPPER_CHARS + NUMBERS


def valid_char_set(string: str, allowed_charset: set):
    string = set(string)

    return string.issubset(allowed_charset)


def username_valid(username:str):
    secure_uname = secure_filename(username)

    if not valid_char_set(username, UNAME_CHARS):
        return False, f"For usernames only characters and numbers please"
    elif len(username) < 3:
        return False, "Sorry bro, username must be at least 3 characters long"
    elif len(username) > 100:
        return False, "Nah that's too long my friend"
    elif 'admin' in username.lower() or secure_uname != username:
        return False, "Nope not that one please"
    else:
        return True, ""


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user:
            if check_password_hash(user.password, password):
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash("Wrong", category='error')
        else:
            flash('Wrong', category='error')
    return render_template("login.html", user=current_user)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == "POST":
        username = request.form.get('username')  # id must match the 'name' attribute in the html file
        # email = request.form.get('email')     # not used yet   
        password = request.form.get('password')
        confPassword = request.form.get('confPassword')
        acces_code = request.form.get('accessCode')

        user = User.query.filter_by(username=username).first()

        uname_valid, username_error_msg = username_valid(str(username))
        passwd_valid = valid_char_set(password, PASSWD_CHARS)

        if user:
            flash("Username already taken", category='error')
        elif not uname_valid:
            flash(username_error_msg, category="error")
        elif not passwd_valid:
            flash(f'For passwords only characters, numbers and {ALLOWED_SPECIAL_CHARS} please', category='error')
        elif password != confPassword:
            flash('Passwords are not matching', category='error')
        elif acces_code != app.config['ACCESS_CODE']:
            flash('Alpha access code invalid', category='error')
        else:
            # personal files get stored in a folder named heroes/user_[username]
            heroes_path = os.path.join(app.config['UPLOAD_FOLDER'], 'user_' + username)
            Path(heroes_path).mkdir(parents=True, exist_ok=True)
            new_user = User(username=username, password=generate_password_hash(password, method='sha256'), heroes_path=heroes_path, access_lvl=Level.USER) # add e-mail for later use
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('Congratulations, you are now the proud owner of a new account on this wonderful website!', category='success')
            return redirect(url_for('views.home'))

    return render_template("sign-up.html", user=current_user)

