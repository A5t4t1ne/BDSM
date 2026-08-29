import os
from pathlib import Path

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from loguru import logger
from sqlalchemy.exc import IntegrityError
from werkzeug.middleware.proxy_fix import ProxyFix

db = SQLAlchemy()
csrf = CSRFProtect()

SECRETS_DIR = Path(os.environ.get("BDSM_SECRETS_DIR", "/run/secrets"))
DATA_DIR = Path(os.environ.get("BDSM_DATA_DIR", "/data"))


def _read_secret(name: str) -> str:
    """Read one Docker secret.

    A secret may also be supplied as ``BDSM_<NAME>`` for local development,
    where there is no /run/secrets mount.

    Args:
        name (str): secret file name, e.g. "secret_key"

    Raises:
        FileNotFoundError: if the secret is available from neither source.

    Returns:
        str: the secret value
    """
    from_env = os.environ.get(f"BDSM_{name.upper()}")
    if from_env:
        return from_env.strip()

    path = SECRETS_DIR / name
    if not path.is_file():
        raise FileNotFoundError(
            f"Secret '{name}' not found. Provide {path} or set BDSM_{name.upper()}."
        )
    value = path.read_text(encoding="utf8").strip()
    if not value:
        raise ValueError(f"Secret '{name}' is empty.")
    return value


def create_admin(app: Flask) -> None:
    """Ensure an admin user exists.

    The password is only written when the account is created, or when
    BDSM_RESET_ADMIN is set -- otherwise a restart would silently revert a
    password the operator changed. Safe to call from several workers at once.
    """
    from werkzeug.security import generate_password_hash

    from .models import Level, User

    with app.app_context():
        admin = User.query.filter_by(username="admin").first()
        heroes_path = os.path.join(app.config["UPLOAD_FOLDER"], "admin")
        Path(heroes_path).mkdir(parents=True, exist_ok=True)

        if admin is None:
            new_admin = User(
                username="admin",
                password=generate_password_hash(app.config["ADMIN_PW"], method="pbkdf2:sha256"),
                heroes_path=heroes_path,
                access_lvl=Level.ADMIN,
                email="",
            )
            try:
                db.session.add(new_admin)
                db.session.commit()
                logger.info("created admin user")
            except IntegrityError:
                # another worker won the race; that is fine
                db.session.rollback()
                logger.debug("admin user already created by another worker")
            return

        admin.heroes_path = heroes_path
        admin.access_lvl = Level.ADMIN
        if os.environ.get("BDSM_RESET_ADMIN"):
            admin.password = generate_password_hash(app.config["ADMIN_PW"], method="pbkdf2:sha256")
            logger.warning("admin password reset from secret (BDSM_RESET_ADMIN)")
        db.session.commit()


def create_app(db_name="database.db", upload_folder=Path("heroes")) -> Flask:
    """Create and configure the Flask application.

    Args:
        db_name (str, optional): Name of the database file. Defaults to "database.db".
        upload_folder (Path, optional): Folder for uploaded heroes. Defaults to "heroes".

    Raises:
        NotADirectoryError: If the data directory is missing.
        PermissionError: If the data directory is not readable/writable.
        FileNotFoundError: If a required secret is missing.

    Returns:
        Flask: The configured Flask application instance.
    """
    app = Flask(__name__)
    basedir = Path(__file__).absolute().parent

    if not DATA_DIR.is_dir():
        raise NotADirectoryError(f"{DATA_DIR} does not exist or is not a directory")
    if not os.access(DATA_DIR, os.W_OK | os.R_OK | os.X_OK):
        raise PermissionError(f"Not enough permissions on {DATA_DIR} directory")

    app.config["SECRET_KEY"] = _read_secret("secret_key")
    app.config["ACCESS_CODE"] = _read_secret("access_code")
    app.config["ADMIN_PW"] = _read_secret("admin_pw")

    db_path = DATA_DIR / db_name
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + str(db_path)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB
    app.config["UPLOAD_FOLDER"] = str(basedir.parent / upload_folder)
    app.config["ALLOWED_EXTENSIONS"] = {"json"}

    # Session/cookie hardening. Cookies are only marked Secure when the app is
    # actually served over TLS, so a plain-HTTP dev run still works.
    behind_tls = os.environ.get("BDSM_INSECURE_COOKIES") != "1"
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SECURE=behind_tls,
        SESSION_COOKIE_SAMESITE="Lax",
        REMEMBER_COOKIE_HTTPONLY=True,
        REMEMBER_COOKIE_SECURE=behind_tls,
        REMEMBER_COOKIE_SAMESITE="Lax",
        REMEMBER_COOKIE_DURATION=60 * 60 * 24 * 30,  # 30 days
        WTF_CSRF_TIME_LIMIT=None,  # tie CSRF token lifetime to the session
    )

    # nginx terminates TLS, so trust exactly one hop of X-Forwarded-* headers
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    db.init_app(app)
    csrf.init_app(app)

    # include other flask routes and connect them
    from .auth import auth, limiter
    from .requests import req
    from .views import views

    limiter.init_app(app)

    app.register_blueprint(views, url_prefix="/")
    app.register_blueprint(auth, url_prefix="/")
    app.register_blueprint(req, url_prefix="/")

    # importing models for database creation
    from .models import User

    # create_all only adds missing tables, so it is safe to run on every boot
    with app.app_context():
        db.create_all()

    create_admin(app)

    login_manager = LoginManager()
    # default page to call if user isn't logged in
    login_manager.login_view = "auth.login"
    login_manager.init_app(app=app)
    login_manager.login_message = ""

    @login_manager.user_loader
    def load_user(id):
        return db.session.get(User, int(id))

    return app
