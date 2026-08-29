import os
from pathlib import Path
from typing import Tuple

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import current_user, login_required, login_user, logout_user
from loguru import logger
from werkzeug import Response
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from . import db
from .models import Level, User

auth = Blueprint("auth", __name__)

# Throttles credential guessing. The default in-memory backend counts per
# worker process, so the effective limit is (workers x limit); set
# BDSM_RATELIMIT_STORAGE to a redis:// URI to share one counter.
limiter = Limiter(
    get_remote_address,
    storage_uri=os.environ.get("BDSM_RATELIMIT_STORAGE", "memory://"),
    default_limits=[],
)

LOWER_CHARS = "abcdefghijklmnopqrstuvwxyz"
UPPER_CHARS = LOWER_CHARS.upper()
NUMBERS = "1234567890"
ALLOWED_SPECIAL_CHARS = "&$?!-_"
PASSWD_CHARS = LOWER_CHARS + UPPER_CHARS + NUMBERS + ALLOWED_SPECIAL_CHARS
UNAME_CHARS = LOWER_CHARS + UPPER_CHARS + NUMBERS

MIN_PASSWORD_LENGTH = 12
MAX_PASSWORD_LENGTH = 100
MIN_USERNAME_LENGTH = 3
MAX_USERNAME_LENGTH = 100

# Comparing against a real hash keeps the response time for an unknown username
# in the same range as for a known one, so login cannot be used to enumerate
# accounts.
_DUMMY_HASH = generate_password_hash("not-a-real-password", method="pbkdf2:sha256")


def valid_char_set(string: str, allowed_charset: str) -> bool:
    """Check if the string contains only characters from the allowed charset.

    Args:
        string (str): string to check
        allowed_charset (str): string containing allowed characters
    Returns:
        bool: True if the string contains only allowed characters, False otherwise
    """
    return set(string).issubset(allowed_charset)


def username_valid(username: str) -> Tuple[bool, str]:
    """Check if the username is valid.

    Args:
        username (str): username to check

    Returns:
        Tuple[bool, str]: A tuple consisting of (is_valid: bool, error_message: str)
    """
    if not valid_char_set(username, UNAME_CHARS):
        return False, "Usernames may only contain the letters a-z and numbers"
    if len(username) < MIN_USERNAME_LENGTH:
        return False, f"Sorry bro, username must be at least {MIN_USERNAME_LENGTH} characters long"
    if len(username) > MAX_USERNAME_LENGTH:
        return False, "Nah that's too long my friend"
    if "admin" in username.lower() or secure_filename(username) != username:
        return False, "Nope not that one please"
    return True, ""


def password_valid(password: str) -> Tuple[bool, str]:
    """Check if the password meets the minimum policy.

    Args:
        password (str): password to check

    Returns:
        Tuple[bool, str]: A tuple consisting of (is_valid: bool, error_message: str)
    """
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters long"
    if len(password) > MAX_PASSWORD_LENGTH:
        return False, "Password is too long"
    if not valid_char_set(password, PASSWD_CHARS):
        return False, f"For passwords only letters, numbers and {ALLOWED_SPECIAL_CHARS} please"
    return True, ""


@auth.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute; 60 per hour", methods=["POST"])
def login() -> str | Response:
    """Login route for the application.

    Returns:
        str | Response: the login page, or a redirect home on success.
    """
    if request.method == "POST":
        username = request.form.get("username") or ""
        password = request.form.get("password") or ""

        user = User.find_by_username(username)
        stored_hash = user.password if user else _DUMMY_HASH

        if check_password_hash(stored_hash, password) and user is not None:
            login_user(user, remember=bool(request.form.get("remember")))
            logger.info(f"user {user.id} logged in")
            return redirect(url_for("views.home"))

        logger.info(f"failed login for '{username[:MAX_USERNAME_LENGTH]}'")
        flash("Username or password is incorrect", category="error")

    return render_template("login.html", user=current_user)


@auth.route("/change-password", methods=["POST"])
@login_required
@limiter.limit("10 per hour")
def change_password() -> Response:
    """Change the signed-in user's password.

    Requires the current password, so a borrowed session cannot be used to lock
    the real owner out of their account.
    """
    current = request.form.get("currentPassword") or ""
    new = request.form.get("newPassword") or ""
    confirm = request.form.get("confPassword") or ""

    new_valid, new_error_msg = password_valid(new)

    if not check_password_hash(current_user.password, current):
        flash("Your current password is not correct", category="error")
    elif not new_valid:
        flash(new_error_msg, category="error")
    elif new != confirm:
        flash("New passwords are not matching", category="error")
    elif new == current:
        flash("That is already your password", category="error")
    else:
        current_user.password = generate_password_hash(new, method="pbkdf2:sha256")
        db.session.commit()
        logger.info(f"user {current_user.id} changed their password")
        flash("Password changed", category="success")

    return redirect(url_for("views.account"))


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
@limiter.limit("5 per minute; 20 per hour", methods=["POST"])
def sign_up() -> str | Response:
    """Sign-up route for the application.

    Validates the input, checks for an existing username and creates the
    account if everything passes.

    Returns:
        str | Response: the sign-up page, or a redirect home on success.
    """
    if request.method == "POST":
        # id must match the 'name' attribute in the html file
        username = request.form.get("username") or ""
        password = request.form.get("password") or ""
        conf_password = request.form.get("confPassword") or ""
        access_code = (request.form.get("accessCode") or "").strip()

        uname_valid, username_error_msg = username_valid(username)
        passwd_valid, password_error_msg = password_valid(password)

        if not uname_valid:
            flash(username_error_msg, category="error")
        elif User.find_by_username(username):
            flash("Username already taken", category="error")
        elif not passwd_valid:
            flash(password_error_msg, category="error")
        elif password != conf_password:
            flash("Passwords are not matching", category="error")
        elif access_code != current_app.config["ACCESS_CODE"]:
            flash("Alpha access code invalid", category="error")
        else:
            # personal files get stored in a folder named heroes/user_[username]
            heroes_path = os.path.join(current_app.config["UPLOAD_FOLDER"], "user_" + username)
            Path(heroes_path).mkdir(parents=True, exist_ok=True)
            new_user = User(
                username=username,
                password=generate_password_hash(password, method="pbkdf2:sha256"),
                heroes_path=heroes_path,
                access_lvl=Level.USER,
                email="",
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            logger.info(f"created user {new_user.id}")
            flash(
                "Congratulations, you are now the proud owner, of a new account on this wonderful website!",
                category="success",
            )
            return redirect(url_for("views.home"))

    return render_template("sign-up.html", user=current_user)
