from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_session import Session

from config import config as Config
import os


db = SQLAlchemy()
csrf = CSRFProtect()
migrate = Migrate()
login_manager = LoginManager()
sess = Session()

def create_app():
    app = Flask(__name__)
    config_name = os.environ.get("FLASKENV")

    app.config.from_object(Config[config_name])

    Config[config_name].init_app(app)

    db.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db, render_as_batch=True)
    login_manager.login_view = "account.login"
    login_manager.init_app(app)
    app.config["SESSION_SQLALCHEMY"] = db
    sess.init_app(app)

    from .features.home.home import home_blueprint
    from .features.account.account import account_blueprint
    app.register_blueprint(home_blueprint, url_prefix="/")
    app.register_blueprint(account_blueprint, url_prefix="/account")

    from .api.api import api_blueprint
    csrf.exempt(api_blueprint)
    app.register_blueprint(api_blueprint)


    return app
    
