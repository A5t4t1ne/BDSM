from typing import List

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from flask_wtf.csrf import CSRFError
from werkzeug import Response

from . import db
from .models import Hero, Level, User
from .tools.upload import UploadFileForm, save_hero

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
            rejected = []
            saved = 0
            for file in form.files.data:
                ok, reason = save_hero(file)
                if ok:
                    saved += 1
                else:
                    rejected.append(f"{file.filename} ({reason})")

            if saved:
                flash(f"{saved} hero(es) uploaded successfully", category='success')
            for rejection in rejected:
                flash(f"Could not import {rejection}", category='error')

    return render_template('overview.html', user=current_user, form=form)


@views.route('/healthz')
def healthz() -> Response | str:
    """Liveness probe for the container healthcheck.

    Touches the database so a broken connection is reported as unhealthy.
    """
    db.session.execute(db.text("SELECT 1"))
    return "ok"


@views.route('/account')
@login_required
def account() -> str:
    return render_template('account.html', user=current_user)


@views.route('/play')
@login_required
def play() -> str:
    return render_template("play.html", user=current_user)


@views.route('/hero-display/<hero_name>')
@login_required
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
    if hero is None:
        abort(404)
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


@views.app_errorhandler(413)
def too_large(e):
    """Server request too large error handler.

    Args:
        e (_type_): error

    Returns:
        string: string with html code
    """
    flash("Upload size too large", category='error')
    return redirect(url_for("views.overview"))


@views.app_errorhandler(404)
def not_found_error(e):
    """Handle URL not found error

    Args:
        e (_type_): _description_

    Returns:
        string: string with html code
    """
    return render_template("error.html", user=current_user, code=404,
                           message="This page does not exist."), 404


@views.app_errorhandler(500)
def internal_server_error(e):
    """Handle internal server errors.

    Args:
        e (_type_): _description_

    Returns:
        string: string with html code
    """
    return render_template("error.html", user=current_user, code=500,
                           message="Something went wrong on our side. "
                                   "Please report what you did just before this happened."), 500


@views.app_errorhandler(CSRFError)
def csrf_error(e):
    """Handle CSRF errors.

    Args:
        e (_type_): _description_

    Returns:
        string: string with html code
    """
    return render_template("error.html", user=current_user, code=400,
                           message="Your session expired. Please reload the page and try again."), 400
