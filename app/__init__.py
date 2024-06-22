from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import load_dotenv
from flask_mail import Mail
from flask_dramatiq import Dramatiq
from dramatiq.brokers.redis import RedisBroker
import dramatiq


db = SQLAlchemy()
migrate = Migrate()
load_dotenv()
login_manager = LoginManager()
mail = Mail()


def create_app(test_config=None):
    app = Flask(__name__)

    if not test_config:
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
            "SQLALCHEMY_DATABASE_URI")
    else:
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
            "SQLALCHEMY_TEST_DATABASE_URI")

    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")

    app.config["MAIL_SERVER"] = "smtp.gmail.com"
    app.config["MAIL_PORT"] = 587
    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")
    app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("MAIL_USERNAME")

    redis_broker = RedisBroker(url="redis://127.0.0.1:6379/0")
    dramatiq.set_broker(redis_broker)

    from app.models.user import User

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    dramatiq_extension = Dramatiq(app)

    from .routes import users_bp
    app.register_blueprint(users_bp)

    from .routes import page_bp
    app.register_blueprint(page_bp)

    return app
