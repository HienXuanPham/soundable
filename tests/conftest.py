from flask import request_finished
import pytest
from app import create_app, db
from app.models.user import User
from werkzeug.security import generate_password_hash


@pytest.fixture
def app():
    app = create_app({"TESTING": True})

    @request_finished.connect_via(app)
    def expire_session(sender, response, **extra):
        db.session.remove()

    with app.app_context():
        db.create_all()
        yield app

    with app.app_context():
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def user_1(app):
    user = User(
        name="Test User",
        email="test@example.com",
        password=generate_password_hash("password"),
        verification_token=None,
        token_expiration=None,
        is_confirmed=True,
        confirmed_on="2024-05-27 15:03:19.679655+00:00"
    )

    db.session.add(user)
    db.session.commit()
