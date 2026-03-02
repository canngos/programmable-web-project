from flasgger import swag_from
from flask import Blueprint, jsonify, request

from ticket_management_system.extensions import db
from ticket_management_system.resources.user_service import UserService
from ticket_management_system.utils import admin_required, token_required

user_bp = Blueprint("users", __name__, url_prefix="/api/users")


@user_bp.route("/register", methods=["POST"])
@swag_from("../swagger_specs/user_register.yml")
def register():
    try:
        data = request.get_json(force=True, silent=True)

        is_valid, error_msg = UserService.validate_registration_data(data)
        if not is_valid:
            return jsonify({"error": "Bad Request", "message": error_msg}), 400

        if UserService.email_exists(data["email"]):
            return jsonify({"error": "Conflict", "message": "Email already registered"}), 409

        role, error_msg = UserService.validate_role(data.get("role"))
        if error_msg:
            return jsonify({"error": "Bad Request", "message": error_msg}), 400

        new_user = UserService.create_user(
            firstname=data["firstname"],
            lastname=data["lastname"],
            email=data["email"],
            password=data["password"],
            role=role,
        )

        response = UserService.format_user_response(new_user, include_token=True)
        response["message"] = "User registered successfully"

        return jsonify(response), 201

    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": "Internal Server Error", "message": str(exc)}), 500


@user_bp.route("/login", methods=["POST"])
@swag_from("../swagger_specs/user_login.yml")
def login():
    try:
        data = request.get_json(force=True, silent=True)

        if not data:
            return jsonify({"error": "Bad Request", "message": "Request body must be JSON"}), 400

        if "email" not in data or "password" not in data:
            return jsonify({"error": "Bad Request", "message": "Email and password are required"}), 400

        user, error_msg = UserService.authenticate_user(data["email"], data["password"])

        if error_msg:
            return jsonify({"error": "Unauthorized", "message": error_msg}), 401

        response = UserService.format_user_response(user, include_token=True)
        response["message"] = "Login successful"

        return jsonify(response), 200

    except Exception as exc:
        return jsonify({"error": "Internal Server Error", "message": str(exc)}), 500


@user_bp.route("/me", methods=["GET"])
@token_required
@swag_from("../swagger_specs/user_me.yml")
def get_current_user(current_user):
    response = UserService.format_user_detail(current_user)
    return jsonify(response), 200


@user_bp.route("/", methods=["GET"])
@token_required
@admin_required
@swag_from("../swagger_specs/user_list.yml")
def get_all_users(current_user):
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    result = UserService.get_paginated_users(page, per_page)

    return jsonify(result), 200
