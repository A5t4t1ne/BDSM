import os
from contextlib import contextmanager
from pathlib import Path

from alembic.script import ScriptDirectory
from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_migrate import stamp as alembic_stamp
from flask_migrate import upgrade as alembic_upgrade
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from loguru import logger
from sqlalchemy import event, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from werkzeug.middleware.proxy_fix import ProxyFix

db = SQLAlchemy()
csrf = CSRFProtect()
migrate = Migrate()

# Throttles credential guessing and invite-code guessing. The default in-memory
# backend counts per worker process, so the effective limit is
# (workers x limit); set BDSM_RATELIMIT_STORAGE to a redis:// URI to share one
# counter across them.
limiter = Limiter(
    get_remote_address,
    storage_uri=os.environ.get("BDSM_RATELIMIT_STORAGE", "memory://"),
    default_limits=[],
)

MIGRATIONS_DIR = Path(__file__).absolute().parent.parent / "migrations"


@event.listens_for(Engine, "connect")
def _sqlite_pragmas(dbapi_connection, _connection_record):
    """Make SQLite survive several gunicorn workers writing at once.

    WAL lets readers work while a writer holds the database, and busy_timeout
    makes a blocked writer wait instead of failing outright with
    "database is locked".
    """
    if type(dbapi_connection).__module__.startswith("sqlite3"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=10000")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

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
        # the schema may not exist yet when this app instance was built purely
        # to serve a `flask db` command
        if not inspect(db.engine).has_table(User.__tablename__):
            logger.debug("user table does not exist yet, skipping admin bootstrap")
            return

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


@contextmanager
def _migration_lock():
    """Let only one process migrate at a time.

    Alembic does not lock across processes, so all four gunicorn workers used to
    read "no revision applied" together and then race to create the same tables;
    the losers died with "table ... already exists" and gunicorn gave up. An
    exclusive lock on a file next to the database serialises them, and every
    worker after the first finds the upgrade already done.
    """
    try:
        import fcntl
    except ImportError:  # pragma: no cover -- not POSIX
        logger.warning("no fcntl available, migrating without a lock")
        yield
        return

    lock_path = DATA_DIR / ".migrate.lock"
    with open(lock_path, "w") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file, fcntl.LOCK_UN)


def _apply_migrations(app: Flask) -> None:
    """Bring the database up to the latest revision."""
    with app.app_context(), _migration_lock():
        if not MIGRATIONS_DIR.is_dir():
            # no migration history available (e.g. a source checkout without
            # the directory); fall back to creating the tables directly
            logger.warning(f"{MIGRATIONS_DIR} missing, falling back to create_all()")
            db.create_all()
            return

        directory = str(MIGRATIONS_DIR)
        tables = set(inspect(db.engine).get_table_names())

        if tables and "alembic_version" not in tables:
            # A database created by the old create_all() bootstrap. Its schema
            # matches the first revision, so adopt it by stamping rather than
            # replaying a migration that would try to recreate its tables.
            script = ScriptDirectory.from_config(migrate.get_config(directory))
            base = script.get_bases()[0]
            logger.warning(f"adopting pre-migration database, stamping at {base}")
            alembic_stamp(directory=directory, revision=base)

        alembic_upgrade(directory=directory)


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
    # Uploaded hero files. In the container this is the /app/heroes volume;
    # BDSM_UPLOAD_DIR keeps a local run from writing into the source tree.
    app.config["UPLOAD_FOLDER"] = os.environ.get(
        "BDSM_UPLOAD_DIR", str(basedir.parent / upload_folder)
    )
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
    migrate.init_app(app, db, directory=str(MIGRATIONS_DIR))

    # include other flask routes and connect them
    from .auth import auth
    from .campaigns import campaigns
    from .friends import friends
    from .requests import req
    from .views import views

    limiter.init_app(app)

    app.register_blueprint(views, url_prefix="/")
    app.register_blueprint(auth, url_prefix="/")
    app.register_blueprint(req, url_prefix="/")
    app.register_blueprint(friends, url_prefix="/")
    app.register_blueprint(campaigns, url_prefix="/")

    # importing models so Alembic can see them
    from .models import User  # noqa: F401

    _apply_migrations(app)
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
