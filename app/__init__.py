from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import Config


db = SQLAlchemy()
login = LoginManager()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address)

login.login_view = 'main.login'

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    csrf.init_app(app)
    login.init_app(app)
    limiter.init_app(app)

    login.login_view = 'main.login'
    login.session_protection = "strong"

    from .routes import main
    app.register_blueprint(main)

    from .models import User

    @login.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app