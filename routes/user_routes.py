"""
User authentication routes for the Flight Management System API.
Provides endpoints for user registration and login with JWT authentication.
"""

from flask import Blueprint, request, jsonify
from functools import wraps
from flasgger import swag_from
from extensions import db
from models import Roles
from services.user_service import UserService

user_bp = Blueprint('users', __name__, url_prefix='/api/users')


def token_required(f):
    """
    Decorator to protect routes that require authentication.
    Validates JWT token from Authorization header.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Get token from Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                # Expected format: "Bearer <token>"
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({
                    'error': 'Invalid authorization header format',
                    'message': 'Use format: Bearer <token>'
                }), 401

        if not token:
            return jsonify({
                'error': 'Authentication required',
                'message': 'No token provided'
            }), 401

        # Verify token using service
        current_user, error = UserService.verify_token(token)

        if error:
            return jsonify({
                'error': 'Token expired' if 'expired' in error.lower() else 'Invalid token',
                'message': error
            }), 401

        # Pass current_user to the route
        return f(current_user, *args, **kwargs)

    return decorated


def admin_required(f):
    """
    Decorator to protect routes that require admin role.
    Must be used after @token_required.
    """
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        if current_user.role != Roles.admin:
            return jsonify({
                'error': 'Forbidden',
                'message': 'Admin privileges required'
            }), 403

        return f(current_user, *args, **kwargs)

    return decorated


@user_bp.route('/register', methods=['POST'])
@swag_from('../swagger_specs/user_register.yml')
def register():
    """Register a new user"""
    try:
        data = request.get_json(force=True, silent=True)

        # Validate registration data
        is_valid, error_msg = UserService.validate_registration_data(data)
        if not is_valid:
            return jsonify({
                'error': 'Bad Request',
                'message': error_msg
            }), 400

        # Check if email already exists
        if UserService.email_exists(data['email']):
            return jsonify({
                'error': 'Conflict',
                'message': 'Email already registered'
            }), 409

        # Validate and convert role
        role, error_msg = UserService.validate_role(data.get('role'))
        if error_msg:
            return jsonify({
                'error': 'Bad Request',
                'message': error_msg
            }), 400

        # Create new user
        new_user = UserService.create_user(
            firstname=data['firstname'],
            lastname=data['lastname'],
            email=data['email'],
            password=data['password'],
            role=role
        )

        # Format response with token
        response = UserService.format_user_response(new_user, include_token=True)
        response['message'] = 'User registered successfully'

        return jsonify(response), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e)
        }), 500


@user_bp.route('/login', methods=['POST'])
@swag_from('../swagger_specs/user_login.yml')
def login():
    """Authenticate user and return JWT token"""
    try:
        data = request.get_json(force=True, silent=True)

        # Validate required fields
        if not data:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Request body must be JSON'
            }), 400

        if 'email' not in data or 'password' not in data:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Email and password are required'
            }), 400

        # Authenticate user
        user, error_msg = UserService.authenticate_user(data['email'], data['password'])

        if error_msg:
            return jsonify({
                'error': 'Unauthorized',
                'message': error_msg
            }), 401

        # Format response with token
        response = UserService.format_user_response(user, include_token=True)
        response['message'] = 'Login successful'

        return jsonify(response), 200

    except Exception as e:
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e)
        }), 500


@user_bp.route('/me', methods=['GET'])
@token_required
@swag_from('../swagger_specs/user_me.yml')
def get_current_user(current_user):
    """Get current authenticated user's profile"""
    response = UserService.format_user_detail(current_user)
    return jsonify(response), 200


@user_bp.route('/', methods=['GET'])
@token_required
@admin_required
@swag_from('../swagger_specs/user_list.yml')
def get_all_users(current_user):
    """Get all users with pagination (Admin only)"""
    # Get pagination parameters from query string
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    # Get paginated users from service
    result = UserService.get_paginated_users(page, per_page)

    return jsonify(result), 200
