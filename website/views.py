from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, login_user, logout_user, current_user

views = Blueprint("views", __name__)

@views.route('/')
def redirect_to_home():
    return redirect(url_for('views.home'))

@views.route("/home")
@login_required
def home():
    return render_template("home.html")
