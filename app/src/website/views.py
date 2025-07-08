from flask import Blueprint, flash, render_template, redirect, url_for, request
from flask_login import login_required, current_user
from flask_wtf.csrf import CSRFError
from . import app, db
from .models import User, Hero, Level
from .tools.upload import UploadFileForm, save_hero
from typing import List
from werkzeug import Response


views = Blueprint("views", __name__)


@views.route('/')
@views.route("/home")
def home() -> str:
    return render_template("home.html", user=current_user)


@views.route('/overview', methods=['GET', 'POST'])
@login_required
def overview() -> str:
    form = UploadFileForm()

    if form.validate_on_submit():
        # check if there is no real file uploaded
        if len(form.files.data) < 1 or (len(form.files.data) == 1 and form.files.data[0].filename == ''):
            flash("No file selected", category='error')
        else:
            invalid_files = []
            for file in form.files.data:
                if not save_hero(file):
                    invalid_files.append(file.filename)

            if len(invalid_files) > 0:
                invalid_file_names = ', '.join(invalid_files)
                flash(
                    f'These files are not valid: {invalid_file_names}', category='error')
            else:
                flash("Files uploaded successfully", category='success')

    return render_template('overview.html', user=current_user, form=form)


@views.route('/account')
@login_required
def account() -> str:
    return render_template('account.html', user=current_user)


@views.route('/play')
@login_required
def play() -> str:
    return render_template("play.html", user=current_user)


@views.route('/hero-display/<hero_name>')
def hero_display(hero_name) -> str:
    """Display hero page with option to edit base stats.

    Args:
        hero_name (str): secure name of the hero

    Returns:
        html-template: hero_display.html template
    """
    hero = db.session.execute(db.select(Hero).where(
        Hero.user_id == current_user.id,
        Hero.secure_name == hero_name)
    ).scalar()
    return render_template("hero_display.html", user=current_user, hero=hero)


@views.route('/admin-panel', methods=['GET', 'POST'])
@login_required
def admin_panel() -> Response | str:
    if current_user.access_lvl == Level.ADMIN:
        all_users = []
        if request.method == "GET":
            all_users: List[User] = User.query.all()
        return render_template("admin-panel.html", user=current_user, all_users=all_users)
    else:
        return redirect(url_for("views.home"))


@app.errorhandler(413)
def too_large(e):
    """Server request too large error handler.

    Args:
        e (_type_): error

    Returns:
        string: string with html code
    """
    flash("Upload size too large", category='error')
    return redirect(url_for("views.overview"))


@app.errorhandler(404)
def not_found_error(e):
    """Handle URL not found error

    Args:
        e (_type_): _description_

    Returns:
        string: string with html code
    """
    return "<h1>Page not found</h1>"


@app.errorhandler(500)
def internal_server_error(e):
    """Handle internal server errors.

    Args:
        e (_type_): _description_

    Returns:
        string: string with html code
    """
    return "<h1>Internal server error</h1><p>Please contact me with the steps you just made before this happened</p>"


@app.errorhandler(CSRFError)
def csrf_error(e):
    """Handle CSRF errors.

    Args:
        e (_type_): _description_

    Returns:
        string: string with html code
    """
    return "Sorry, this request could not be executed.\n"
