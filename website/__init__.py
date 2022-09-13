from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import json
import os

CONFIG_PATH = 'website/config.json'

db = SQLAlchemy()
app = Flask(__name__)


def create_database(app, db_dir):
    if not os.path.exists(db_dir):
        db.create_all(app=app)
        print('Created database')


def create_app(db_name="database.db", upload_folder="heroes"):
    if not os.path.isfile(CONFIG_PATH):
        raise AttributeError("Create a config.json file in website directory with a 'SECRET_KEY' and an 'ACCESS_CODE' property")

    with open(CONFIG_PATH, 'r') as f:
        config = json.load(f)
        if not 'SECRET_KEY' in config or 'ACCESS_CODE' not in config:
            raise AttributeError("You need to define the two configurations 'ACCESS_CODE' and 'SECRET_KEY in config.json'")
    
    app.config['SECRET_KEY'] = config['SECRET_KEY']
    app.config['ACCESS_CODE'] = config['ACCESS_CODE']

    # get abs path starting from this file location
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_dir = os.path.join(basedir, db_name)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_dir
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
    # max incoming request size 16MB
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    # upload folder is [main.py-location]/[upload_folder]/
    app.config['UPLOAD_FOLDER'] = os.path.join(basedir, '..', upload_folder)
    app.config['ALLOWED_EXTENSIONS'] = {'json'}

    db.init_app(app)

    # include other flask routes and connect them
    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    from .models import User

    create_database(app, db_dir)

    login_manager = LoginManager()
    # default page to call if user isn't logged in
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app=app)
    login_manager.login_message = ""

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app
