from datetime import datetime, timedelta, timezone
from flask_login import login_user, logout_user, login_required, current_user
from app import db, login_manager, mail
from flask import Blueprint, request, jsonify, url_for
from app.models.user import User
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import SQLAlchemyError
from flask_mail import Message
import secrets

users_bp = Blueprint("users", __name__, url_prefix="/users")
page_bp = Blueprint("", __name__, url_prefix="")


def validate_login_request(data):
    if "email" not in data or "password" not in data:
        return {"valid": False, "message": "Email and password are required"}
    elif not data["email"]:
        return {"valid": False, "message": "Email cannot be empty"}
    elif not data["password"]:
        return {"valid": False, "message": "Password cannot be empty"}
    else:
        return {"valid": True}


def validate_signup_request(data):
    required_fields = ["name", "email", "password", "confirm_password"]

    for field in required_fields:
        if field not in data:
            return {"valid": False, "message": f"{field.capitalize()} is required"}
        elif not data[field]:
            return {"valid": False, "message": f"{field.capitalize()} cannot be empty"}

    if data["password"] != data["confirm_password"]:
        return {"valid": False, "message": "Password and confirm password do not match"}

    return {"valid": True, "data": {field: data[field] for field in required_fields}}


def generate_verification_token():
    token = secrets.token_hex(16)
    expiration_time = datetime.now(timezone.utc) + timedelta(hours=1)
    return token, expiration_time


def send_verification_email(user):
    verification_link = url_for(
        'verify_email', token=user.verification_token, _external=True)
    msg = Message("Verify Your Email", recipients=[user.email])
    msg.body = f"Please click the following link to verify your email: {
        verification_link}"
    mail.send(msg)


@login_manager.user_loader
def load_user(user_id):
    return User.query.filter(User.user_id == int(user_id)).first()


@page_bp.route("/login", methods=["POST"])
def user_login():
    try:
        request_data = request.get_json()

        validation_result = validate_login_request(request_data)
        if not validation_result["valid"]:
            # 400 Bad Request: missing or invalid data
            return jsonify({"message": validation_result["message"]}), 400

        user_email = request_data.get("email")
        user_password = request_data.get("password")

        db_user = User.query.filter_by(email=user_email).first()

        if db_user and check_password_hash(db_user.password, user_password):
            login_user(db_user)  # initialize a user session
            return jsonify({
                "message": "success",
                "name": f"{db_user.name}"
            })

        # 401 Unauthorized
        return jsonify({"message": "Your email or password is incorrect"}), 401
    except SQLAlchemyError as e:
        # Handle database errors
        db.session.rollback()
        # 500 Internal Server Error: a server-side error occurred
        return jsonify({"message": "Database error occurred"}), 500
    except Exception as e:
        # Handle other unexpected errors
        return jsonify({"message": "An unexpected error occurred"}), 500


@page_bp.errorhandler(401)
def unauthorized_access(error):
    return jsonify({"message": "Unauthorized access. Please log in."}), 401


@page_bp.route("/logout")
@login_required
def user_logout():
    logout_user()
    return jsonify({"message": "Logged out successfully"}), 200


@page_bp.route("/signup", methods=["POST"])
def user_signup():
    try:
        request_data = request.get_json()

        validation_result = validate_signup_request(request_data)
        if not validation_result["valid"]:
            return jsonify({"message": validation_result["message"]}), 400

        data = validation_result["data"]
        db_user = User.query.filter_by(email=data["email"]).first()

        if db_user:
            # 409 Conflict
            return jsonify({"message": f"{data['email']} already existed"}), 409

        token, expiration_time = generate_verification_token()

        new_user = User(
            name=data["name"],
            email=data["email"],
            password=generate_password_hash(data["password"]),
            verification_token=token,
            token_expiration=expiration_time
        )

        db.session.add(new_user)
        db.session.commit()

        send_verification_email(new_user)

        # 201 Created: successfully create a new resource
        return jsonify({"message": "Successfully created an account"}), 201
    except SQLAlchemyError as e:
        db.session.rollback()  # Rollback the session to prevent partial changes
        return jsonify({"message": "Database error occurred"}), 500
    except Exception as e:
        return jsonify({"message": "An unexpected error occurred"}), 500


@page_bp.route("/verify-email/<token>", methods=["POST"])
def verify_email(token):
    user = User.query.filter_by(verification_token=token).first_or_404()

    if user.is_confirmed:
        return jsonify({
            "action": "login",
            "message": "Account is already confirmed. Please login"
        })

    if user.token_expiration and user.token_expiration < datetime.now(timezone.utc):
        return jsonify({
            "action": "verify",
            "message": "The verification link is expired. Please verify your account"
        })

    user.is_confirmed = True
    user.confirmed_on = datetime.now()
    user.verification_token = None
    user.token_expiration = None

    db.session.commit()

    return jsonify({
        "action": "login",
        "message": "Email verified successfully"
    }), 200


@page_bp.route("/resend-verification-email", methods=["POST"])
@login_required
def resend_verification_email():
    if current_user.is_confirmed:
        return jsonify({"message": "Account has been confirmed"}), 404

    token, expiration_time = generate_verification_token()
    current_user.verification_token = token
    current_user.token_expiration = expiration_time

    db.session.commit()
    send_verification_email(current_user)

    return jsonify({"message": "A new verification email has been sent"}), 200
