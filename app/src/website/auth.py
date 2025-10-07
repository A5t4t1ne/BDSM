from pathlib import Path
from typing import Tuple
from flask import Blueprint, render_template, request, flash, redirect, url_for
from werkzeug import Response
from .models import User, Level
from . import db
from . import app
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_required, login_user, logout_user, current_user
import os


auth = Blueprint("auth", __name__)

LOWER_CHARS = "abcdefghijklmnopqrstuvwxyzäöü"
UPPER_CHARS = LOWER_CHARS.upper()
NUMBERS = "1234567890"
ALLOWED_SPECIAL_CHARS = "&$?!-_"
PASSWD_CHARS = LOWER_CHARS + UPPER_CHARS + NUMBERS + ALLOWED_SPECIAL_CHARS
UNAME_CHARS = LOWER_CHARS + UPPER_CHARS + NUMBERS


def valid_char_set(string: str, allowed_charset: str) -> bool:
    """Check if the string contains only characters from the allowed charset.

    Args:
        string (str): string to check
        allowed_charset (str): string containing allowed characters
    Returns:
        bool: True if the string contains only allowed characters, False otherwise
    """
    uniq_chars = set(string)

    return uniq_chars.issubset(allowed_charset)


def username_valid(username: str) -> Tuple[bool, str]:
    """Check if the username is valid.
    This function checks if the username contains only valid characters,

    Args:
        username (str): username to check

    Returns:
        Tuple[bool, str]: A tuple consisting of (is_valid: bool, error_message: str)
    """
    secure_uname = secure_filename(username)

    if not valid_char_set(username, UNAME_CHARS):
        return False, "For usernames only characters and numbers please"
    elif len(username) < 3:
        return False, "Sorry bro, username must be at least 3 characters long"
    elif len(username) > 100:
        return False, "Nah that's too long my friend"
    elif "admin" in username.lower() or secure_uname != username:
        return False, "Nope not that one please"
    else:
        return True, ""


@auth.route("/login", methods=["GET", "POST"])
def login() -> str | Response:
    """Login route for the application.

    Returns:
        str | Response: If the request method is GET, it renders the login page.
        If the request method is POST, it processes the login form and redirects
    """
    if request.method == "POST":
        username = request.form.get("username") or ""
        password = request.form.get("password") or ""

        user = User.query.filter_by(username=username).first()

        if user:
            if check_password_hash(user.password, password):
                login_user(user, remember=True)
                return redirect(url_for("views.home"))
            else:
                flash("Wrong", category="error")
        else:
            flash("Wrong", category="error")
    return render_template("login.html", user=current_user)


@auth.route("/logout")
@login_required
def logout() -> Response:
    """Logout route for the application.

    Returns:
        Response: Redirects to the login page after logging out the user.
    """
    logout_user()
    return redirect(url_for("auth.login"))


@auth.route("/sign-up", methods=["GET", "POST"])
def sign_up() -> str | Response:
    """Sign-up route for the application.
    This route handles the user registration process. It validates the input,
    checks for existing usernames, and creates a new user account if all validations pass.
    If the request method is GET, it renders the sign-up page.
    If the request method is POST, it processes the sign-up form.

    Returns:
        str | Response: If the request method is GET, it renders the sign-up page.
        If the request method is POST, it processes the sign-up form and redirects
        to the home page upon successful registration.
    """
    if request.method == "POST":
        # id must match the 'name' attribute in the html file
        username = request.form.get("username") or ""
        # email = request.form.get('email')     # not used yet
        password = request.form.get("password") or ""
        confPassword = request.form.get("confPassword")
        access_code = request.form.get("accessCode") or ""
        access_code = access_code.strip()

        user = User.query.filter_by(username=username).first()

        uname_valid, username_error_msg = username_valid(str(username))
        passwd_valid = valid_char_set(password, PASSWD_CHARS)

        if user:
            if 'admin' in username:
                flash("Nope not that one please", category='error')
            else:
                flash("Username already taken", category='error')
        elif not uname_valid:
            flash(username_error_msg, category="error")
        elif len(password) > 100:
            flash("Password is too long", category='error')
        elif not passwd_valid:
            flash(
                f"For passwords only characters, numbers and {ALLOWED_SPECIAL_CHARS} please",
                category="error",
            )
        elif password != confPassword:
            flash("Passwords are not matching", category="error")
        elif access_code != app.config["ACCESS_CODE"]:
            flash("Alpha access code invalid", category="error")
        else:
            # personal files get stored in a folder named heroes/user_[username]
            heroes_path = os.path.join(app.config["UPLOAD_FOLDER"], "user_" + username)
            Path(heroes_path).mkdir(parents=True, exist_ok=True)
            new_user = User(
                username=username,
                password=generate_password_hash(password, method="pbkdf2:sha256"),
                heroes_path=heroes_path,
                access_lvl=Level.USER,
            )  # add e-mail for later use
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash(
                "Congratulations, you are now the proud owner, of a new account on this wonderful website!",
                category="success",
            )
            return redirect(url_for("views.home"))

    return render_template("sign-up.html", user=current_user)
