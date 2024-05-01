from app import db
from datetime import datetime
from flask_login import UserMixin

class User(UserMixin, db.Model):
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)
    password = db.Column(db.Text, nullable=False)
    created_on = db.Column(db.DateTime, nullable=False)
    is_confirmed = db.Column(db.Boolean, nullable=False, default=False)
    confirmed_on = db.Column(db.DateTime, nullable=True)

    def __init__(
            self, name, email, password, is_confirmed=False, confirmed_on=None
    ):
        self.name = name
        self.email = email
        self.password = password
        self.created_on = datetime.now()
        self.is_confirmed = is_confirmed
        self.confirmed_on = confirmed_on