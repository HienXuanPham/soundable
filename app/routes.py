from flask_login import login_user, logout_user, login_required
from app import db, login_manager
from flask import Blueprint, request, jsonify
from app.models.user import User
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import SQLAlchemyError

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

@login_manager.user_loader
def load_user(user_id):
    return User.query.filter(User.user_id == int(user_id)).first()

@page_bp.route("/login", methods=["POST"])
def user_login():
    try:
        request_data = request.get_json()

        validation_result = validate_login_request(request_data)
        if not validation_result["valid"]:
            return jsonify({"message": validation_result["message"]}), 400 # 400 Bad Request: missing or invalid data
        
        user_email = request_data.get("email")
        user_password = request_data.get("password")

        db_user = User.query.filter_by(email=user_email).first()

        if db_user and check_password_hash(db_user.password, user_password):
            login_user(db_user)  # initialize a user session
            return jsonify({
                "message": "success",
                "name": f"{db_user.name}"
            })
        
        return jsonify({"message": "Your email or password is incorrect"}), 401 # 401 Unauthorized
    except SQLAlchemyError as e:
        # Handle database errors
        db.session.rollback()
        return jsonify({"message": "Database error occurred"}), 500  # 500 Internal Server Error: a server-side error occurred
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
            return jsonify({"message": f"{data['email']} already existed"}), 409  # 409 Conflict

        new_user = User(
            name=data["name"],
            email=data["email"],
            password=generate_password_hash(data["password"])
        )

        db.session.add(new_user)
        db.session.commit()

        return jsonify({"message": "Successfully created an account"}), 201 # 201 Created: successfully create a new resource
    except SQLAlchemyError as e:
        db.session.rollback()  # Rollback the session to prevent partial changes
        return jsonify({"message": "Database error occurred"}), 500
    except Exception as e:
        return jsonify({"message": "An unexpected error occurred"}), 500
