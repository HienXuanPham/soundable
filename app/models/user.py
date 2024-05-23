from app import db
from datetime import datetime
from flask_login import UserMixin


class User(UserMixin, db.Model):
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)
    password = db.Column(db.Text, nullable=False)
    created_on = db.Column(db.TIMESTAMP(timezone=True), nullable=False)
    is_confirmed = db.Column(db.Boolean, nullable=False, default=False)
    confirmed_on = db.Column(db.TIMESTAMP(timezone=True), nullable=True)
    verification_token = db.Column(db.String, nullable=True, unique=True)
    token_expiration = db.Column(db.TIMESTAMP(timezone=True), nullable=True)

    def __init__(
            self, name, email, password, verification_token,  token_expiration, is_confirmed=False, confirmed_on=None
    ):
        self.name = name
        self.email = email
        self.password = password
        self.verification_token = verification_token
        self.token_expiration = token_expiration
        self.created_on = datetime.now()
        self.is_confirmed = is_confirmed
        self.confirmed_on = confirmed_on

    def get_id(self):
        return self.user_id
