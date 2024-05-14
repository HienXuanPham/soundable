from datetime import datetime, timedelta, timezone
from flask_login import login_user, logout_user, login_required, current_user
from app import db, login_manager, mail
from flask import Blueprint, request, jsonify, url_for, session, send_file
from app.models.user import User
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import SQLAlchemyError
from flask_mail import Message
import secrets
import os
from io import BytesIO
import threading
import pyttsx3
from PyPDF2 import PdfReader

users_bp = Blueprint("users", __name__, url_prefix="/users")
page_bp = Blueprint("", __name__, url_prefix="")

# ----------------- HELPER FUNCTION -----------------------------#


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


def validate_change_password_request(data):
    if "password" not in data or "confirm_password" not in data:
        return {"valid": False, "message": "Password and confirm password are required"}
    elif not data["password"]:
        return {"valid": False, "message": "Password cannot be empty"}
    elif not data["confirm_password"]:
        return {"valid": False, "message": "Confirm password cannot be empty"}
    elif data["password"] != data["confirm_password"]:
        return {"valid": False, "message": "Password and confirm password do not match"}
    else:
        return {"valid": True}


def generate_verification_token():
    token = secrets.token_hex(16)
    expiration_time = datetime.now(timezone.utc) + timedelta(hours=1)
    return token, expiration_time


def send_token_email(user, route, email_subject, email_body):
    verification_link = url_for(
        route, token=user.verification_token, _external=True)
    msg = Message(email_subject, recipients=[user.email])
    msg.body = f"{email_body}: {
        verification_link}"
    mail.send(msg)

# ----------------- LOAD USER -----------------------------#


@login_manager.user_loader
def load_user(user_id):
    return User.query.filter(User.user_id == int(user_id)).first()

# ----------------- LOGIN -----------------------------#


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

        if db_user:
            session["logged_in_user_email"] = db_user.email
            if check_password_hash(db_user.password, user_password):
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

# ----------------- ERROR HANDLER -----------------------------#


@page_bp.errorhandler(401)
def unauthorized_access(error):
    return jsonify({"message": "Unauthorized access. Please log in."}), 401

# ----------------- LOGOUT -----------------------------#


@page_bp.route("/logout")
@login_required
def user_logout():
    logout_user()
    return jsonify({"message": "Logged out successfully"}), 200

# ----------------- SIGNUP -----------------------------#


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

        send_token_email(new_user, "verify_email", "Verify Your Email",
                         "Please click the following link to verify your email")

        # 201 Created: successfully create a new resource
        return jsonify({"message": "Successfully created an account"}), 201
    except SQLAlchemyError as e:
        db.session.rollback()  # Rollback the session to prevent partial changes
        return jsonify({"message": "Database error occurred"}), 500
    except Exception as e:
        return jsonify({"message": "An unexpected error occurred"}), 500

# ----------------- VERIFY ACCOUNT -----------------------------#


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
    send_token_email(current_user, "verify_email", "Verify Your Email",
                     "Please click the following link to verify your email")

    return jsonify({"message": "A new verification email has been sent"}), 200

# ----------------- CHANGE PASSWORD -----------------------------#


@page_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    user_email = session.get("logged_in_user_email")

    if user_email:
        db_user = User.query.filter_by(email=user_email).first()
        if db_user:
            db_user.verification_token, db_user.token_expiration = generate_verification_token()
            db.session.commit()

            send_token_email(db_user, "change_password", "Change Your Password",
                             "Please click the following link to change your password")

            return jsonify({"message": "An email has been sent to change password"}), 200
        else:
            return jsonify({"message": "User not found"}), 404
    else:
        return jsonify({"message": "No user email in session"}), 400


@page_bp.route("/change-password/<token>", methods=["POST"])
def change_password(token):
    db_user = User.query.filter_by(verification_token=token).first_or_404()

    if db_user:
        if db_user.token_expiration and db_user.token_expiration < datetime.now(timezone.utc):
            return jsonify({
                "action": "change password",
                "message": "The link is expired. Please try again"
            })

        try:
            request_data = request.get_json()
            validation_result = validate_change_password_request(
                request_data)

            if not validation_result["valid"]:
                return jsonify({"message": validation_result["message"]}), 400

            db_user.password = generate_password_hash(
                request_data["password"])
            db_user.verification_token = None
            db_user.token_expiration = None

            db.session.commit()

            return jsonify({
                "action": "change password",
                "message": "Successfully changed password"
            }), 200

        except SQLAlchemyError as e:
            db.session.rollback()
            return jsonify({"message": "Database error occurred"}), 500
        except Exception as e:
            return jsonify({"message": "An unexpected error occurred"}), 500
    else:
        return jsonify({"message": "Invalid token"}), 404

# ----------------- CONVERT PDF TO AUDIO -----------------------------#


def remove_pdf_content(pdf_content):
    pdf_content = None


def remove_audio_file(audio_file_path):
    if audio_file_path:
        os.remove(audio_file_path)
        audio_file_path = None


@users_bp.route("/convert-pdf-to-audio", methods=["POST"])
@login_required
def convert_pdf():
    if "file" not in request.files:
        return jsonify({"message": "No file part"})

    pdf_file = request.files["file"]
    if pdf_file.filename == "":
        return jsonify({"message": "No selected file"})

    if not pdf_file.filename.endswith(".pdf"):
        return jsonify({"message": "Not a PDF file"}), 400

    try:
        # Read PDF file into memory
        bytes_file = BytesIO(pdf_file.read())

        # Extract text from PDF
        reader = PdfReader(bytes_file)
        pdf_content = ""

        for page in reader.pages:
            pdf_content += page.extract_text()

        # Convert text to audio
        tts_engine = pyttsx3.init()
        tts_engine.save_to_file(pdf_content, "tts.mp3")
        tts_engine.runAndWait()

        # Send the audio file to the user for download
        send_file("tts.mp3", as_attachment=True)

        # Set timers to remove PDF content and audio file after 10 minutes
        pdf_timer = threading.Timer(
            600, remove_pdf_content, args=[pdf_content])
        audio_timer = threading.Timer(600, remove_audio_file, args=["tts.mp3"])
        pdf_timer.start()
        audio_timer.start()

        return jsonify({"message": "Successfully converted PDF to audio"}), 200

    except Exception as e:
        return jsonify({"message": f"Error processing PDF file: {e}"}), 500
