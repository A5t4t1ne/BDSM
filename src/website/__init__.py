from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
import json
import os

db = SQLAlchemy()
app = Flask(__name__)
csrf = CSRFProtect()


def create_database(app, db_dir):
    if not os.path.exists(db_dir):
        db.create_all(app=app)
        print('Created database')


def create_admin():
    from website.models import User, Level
    from werkzeug.security import generate_password_hash
    from pathlib import Path

    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            heroes_path = os.path.join(app.config['UPLOAD_FOLDER'], 'admin')
            Path(heroes_path).mkdir(parents=True, exist_ok=True)
            admin_pw = generate_password_hash(app.config['ADMIN_PW'], method='sha256')
            new_admin = User(username='admin', password=admin_pw, heroes_path=heroes_path, access_lvl=Level.ADMIN)
            db.session.add(new_admin)
            db.session.commit()
        else:
            # reset admin
            heroes_path = os.path.join(app.config['UPLOAD_FOLDER'], 'admin')
            Path(heroes_path).mkdir(parents=True, exist_ok=True)
            admin.heroes_path = heroes_path
            admin.password = generate_password_hash(os.environ['ADMIN_PW'], method='sha256')
            admin.access_lvl = Level.ADMIN
            admin.email = ""
            db.session.commit()


def create_app(db_name="database.db", upload_folder="heroes"):
    # get abs path starting from this file location
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_dir = os.path.join(basedir, db_name)
    config_dir = os.path.join(basedir, "..", "config.json")
    
    try:
        with open(config_dir, "r") as f:
            try:
                data = json.load(f)
                app.config['SECRET_KEY'] = data['SECRET_KEY']
                app.config['ACCESS_CODE'] = data['ACCESS_CODE']
                app.config['ADMIN_PW'] = data['ADMIN_PW']
            except KeyError:
                raise KeyError("Define the SECRET_KEY, ACCESS_CODE and ADMIN_PW in the config.json file")
            app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
    except FileNotFoundError:
        raise FileNotFoundError("Create a config.json file in the main directory")

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_dir
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
    # max incoming request size 16MB
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    # upload folder is [main.py-location]/[upload_folder]/
    app.config['UPLOAD_FOLDER'] = os.path.join(basedir, '..', upload_folder)
    app.config['ALLOWED_EXTENSIONS'] = {'json'}

    db.init_app(app)
    csrf.init_app(app)

    # include other flask routes and connect them
    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    from .models import User

    create_database(app, db_dir)

    create_admin()

    login_manager = LoginManager()
    # default page to call if user isn't logged in
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app=app)
    login_manager.login_message = ""

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app
