from pathlib import Path
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
import os

db = SQLAlchemy()
app = Flask(__name__)
csrf = CSRFProtect()


def create_admin() -> None:
    """Create an admin user if it does not exist.
    If the admin user exists, reset its password and heroes path.
    This function is called when the application starts up and ensures that
    there is always an admin user available for managing the application.
    """
    from website.models import User, Level
    from werkzeug.security import generate_password_hash
    from pathlib import Path

    with app.app_context():
        admin = None
        try:
            admin = User.query.filter_by(username="admin").first()
        except Exception:
            admin = None

        if admin is None:
            heroes_path = os.path.join(app.config["UPLOAD_FOLDER"], "admin")
            Path(heroes_path).mkdir(parents=True, exist_ok=True)
            admin_pw = generate_password_hash(app.config["ADMIN_PW"], method="pbkdf2:sha256")
            new_admin = User(
                username="admin",
                password=admin_pw,
                heroes_path=heroes_path,
                access_lvl=Level.ADMIN,
            )
            try:
                db.session.add(new_admin)
                db.session.commit()
            except Exception as e:
                print(f"Failed to commit: {e}")
        else:
            # reset admin
            heroes_path = os.path.join(app.config["UPLOAD_FOLDER"], "admin")
            Path(heroes_path).mkdir(parents=True, exist_ok=True)
            admin.heroes_path = heroes_path
            admin.password = generate_password_hash(app.config["ADMIN_PW"], method="pbkdf2:sha256")
            admin.access_lvl = Level.ADMIN
            admin.email = ""
            db.session.commit()


def create_app(db_name="database.db", upload_folder=Path("heroes")) -> Flask:
    """Create and configure the Flask application.
    This function initializes the Flask application, sets up the database, configures
    the secret key, access code, and upload folder. It also registers the blueprints for
    different parts of the application and creates the admin user if it does not exist.

    Args:
        db_name (str, optional): Name of the database file. Defaults to "database.db".
        upload_folder (str, optional): Name of the folder for uploading files. Defaults
        to "heroes".

    Raises:
        KeyError: If the config file does not contain the required keys.
        FileNotFoundError: If no config file is found.

    Returns:
        Flask: The configured Flask application instance.
    """
    # get abs path starting from this file location
    basedir = Path(__file__).absolute().parent
    db_dir = Path("/data")

    if not db_dir.exists():
        raise NotADirectoryError(f"{db_dir} does not exist")
    if not db_dir.is_dir():
        raise NotADirectoryError(f"{db_dir} is not a directory.")
    if not os.access(db_dir, os.W_OK) or not os.access(db_dir, os.R_OK) or not os.access(db_dir, os.X_OK):
        raise PermissionError(f"Not enough permissions on {db_dir} directory")

    p_secret = Path("/run/secrets/")
    p_secret_key = p_secret / Path("secret_key")
    p_acc_code = p_secret / Path("access_code")
    p_admin_pw = p_secret / Path("admin_pw")
    with open(p_secret_key, "r") as f:
        app.config["SECRET_KEY"] = f.read().strip()
    with open(p_acc_code, "r") as f:
        app.config["ACCESS_CODE"] = f.read().strip()
    with open(p_admin_pw, "r") as f:
        app.config["ADMIN_PW"] = f.read().strip()

    db_path = db_dir / db_name
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + str(db_path)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB
    app.config["UPLOAD_FOLDER"] = str(basedir.parent / upload_folder)
    app.config["ALLOWED_EXTENSIONS"] = {"json"}
    app.config["JSON_AS_ASCII"] = False

    db.init_app(app)
    csrf.init_app(app)

    # include other flask routes and connect them
    from .views import views
    from .auth import auth
    from .requests import req

    app.register_blueprint(views, url_prefix="/")
    app.register_blueprint(auth, url_prefix="/")
    app.register_blueprint(req, url_prefix="/")

    # importing models for database creation
    from .models import User

    if not os.path.exists(db_path):
        with app.app_context():
            db.create_all()

    create_admin()

    login_manager = LoginManager()
    # default page to call if user isn't logged in
    login_manager.login_view = "auth.login"
    login_manager.init_app(app=app)
    login_manager.login_message = ""

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app
