from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os


db = SQLAlchemy()
app = Flask(__name__)

def create_database(app, db_dir):
    if not os.path.exists(db_dir):
        db.create_all(app=app)
        print('Created database')


def create_app(db_path="", db_name="database.db", heroes_folder="heroes"):
    app.config['SECRET_KEY'] = "spotted-osmosis-overvalue"

    basedir = os.path.abspath(os.path.dirname(__file__))
    db_dir = os.path.join(basedir, db_path, db_name)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_dir       # dir to database
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
    app.config['MAX_CONTENT_PATH'] = 1_000_000
    app.config['UPLOAD_FOLDER'] = os.path.join(basedir, '../', heroes_folder)    # upload folder is [main.py-location]/heroes/
    app.config['ALLOWED_EXTENSIONS'] = {'json'}

    db.init_app(app)

    # include other flask routes and connect them
    from .views import views
    from .auth import auth
    # from .upload import upload

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    # app.register_blueprint(upload, url_prefix='/')

    from .models import Note, User

    create_database(app, db_dir)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'     # default page to call if user isn't logged in
    login_manager.init_app(app=app)
    login_manager.login_message = ""

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))
    
    return app