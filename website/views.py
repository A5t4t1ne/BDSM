from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required, current_user

views = Blueprint("views", __name__)

@views.route('/')
def redirect_to_home():
    return redirect(url_for('views.home'))

@views.route("/home", methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        note = request.form.get('note')
    return render_template("home.html", user=current_user)
