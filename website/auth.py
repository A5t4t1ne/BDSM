from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User, Note
from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_required, login_user, logout_user, current_user

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user:
            if check_password_hash(user.password, password):
                flash('You remembered your password. Not bad.', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash("Yikes. That password didn't work mate.", category='error')
        else:
            flash('Just guessing usernames or what?', category='error')
    return render_template("login.html", user=current_user)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    # POST-request is sent if the submit button gets pressed
    # GET-request is sent whenever the site gets loaded
    if request.method == "POST":
        username = request.form.get('username')  # id must match the 'name' attribute in the html file
        # email = request.form.get('email')     # -> for later use   
        password = request.form.get('password')
        confPassword = request.form.get('confPassword')

        user = User.query.filter_by(username=username).first()

        if user:
            flash("Be creative, man. Don't steal other people's username.", category='error')
        elif len(username) < 3:
            flash('Sorry bro, username must be at least 3 characters long.', category='error')
        elif password != confPassword:
            flash('Not even able to match your passwords? Maybe you should take some typing lessons...', category='error')
        else:
            new_user = User(username=username, password=generate_password_hash(password, method='sha256'))           # add E-Mail for later use
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('Congratulations, you are now the proud owner of a new account on this wonderful website!', category='success')
            return redirect(url_for('views.home'))

    return render_template("sign-up.html", user=current_user)