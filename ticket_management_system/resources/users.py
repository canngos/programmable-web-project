"""User authentication and management API endpoints."""
from functools import wraps
from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from ticket_management_system.models import Roles
from ticket_management_system.utils import handle_validation_error, handle_general_error, handle_conflict_error
from ticket_management_system.resources.user_service import UserService
from ticket_management_system.static.schema.user_schemas import UserProfileUpdateSchema, UserRegistrationSchema
from ticket_management_system.exceptions import (
    InvalidCredentialsError,
    TokenExpiredError,
    InvalidTokenError,
    UserNotFoundError,
    EmailAlreadyExistsError,
    InvalidRoleError
)

user_bp = Blueprint('users', __name__, url_prefix='/api/users')


def token_required(f):
    """Decorator to require JWT authentication."""
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
        try:
            current_user = UserService.verify_token(token)
        except TokenExpiredError as e:
            return jsonify({
                'error': 'Token expired',
                'message': e.message
            }), 401
        except (InvalidTokenError, UserNotFoundError) as e:
            return jsonify({
                'error': 'Invalid token',
                'message': e.message
            }), 401

        # Pass current_user to the route
        return f(current_user, *args, **kwargs)

    return decorated


def admin_required(f):
    """Decorator to require admin role."""
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
def register():  # pylint: disable=too-many-return-statements
    """Register a new user."""
    try:
        # Get JSON data - handle empty body
        try:
            json_data = request.get_json()
        except Exception:  # pylint: disable=broad-exception-caught
            return jsonify({
                'error': 'Bad Request',
                'message': 'Request body must be valid JSON'
            }), 400

        # Check if request body is empty or None
        if json_data is None:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Request body must be JSON'
            }), 400

        # Validate request data using Marshmallow schema
        schema = UserRegistrationSchema()
        validated_data = schema.load(json_data)

        # Check if email already exists
        if UserService.email_exists(validated_data['email']):
            return jsonify({
                'error': 'Conflict',
                'message': 'Email already registered'
            }), 409

        # Validate and convert role
        role = UserService.validate_role(validated_data.get('role'))

        # Create new user
        new_user = UserService.create_user(
            firstname=validated_data['firstname'],
            lastname=validated_data['lastname'],
            email=validated_data['email'],
            password=validated_data['password'],
            role=role
        )
        # Format response with token
        response = UserService.format_user_response(new_user, include_token=True)
        response['message'] = 'User registered successfully'

        return jsonify(response), 201
    except ValidationError as err:
        return handle_validation_error(err)
    except InvalidRoleError as e:
        return jsonify({
            'error': 'Bad Request',
            'message': e.message
        }), 409
    except Exception as e:  # pylint: disable=broad-exception-caught
        return handle_general_error(e)


@user_bp.route('/login', methods=['POST'])
def login():
    """Login user and return JWT token."""
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
        user = UserService.authenticate_user(data['email'], data['password'])

        # Format response with token
        response = UserService.format_user_response(user, include_token=True)
        response['message'] = 'Login successful'

        return jsonify(response), 200

    except InvalidCredentialsError as e:
        return jsonify({
            'error': 'Unauthorized',
            'message': e.message
        }), 401
    except Exception as e:  # pylint: disable=broad-exception-caught
        return handle_general_error(e, rollback=False)


@user_bp.route('/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    """Get current user profile."""
    response = UserService.format_user_detail(current_user)
    return jsonify(response), 200


@user_bp.route('/me', methods=['PATCH'])
@token_required
def update_current_user(current_user):  # pylint: disable=too-many-return-statements
    """Update current user profile."""
    try:
        # Get JSON data - handle empty body
        try:
            json_data = request.get_json()
        except Exception:  # pylint: disable=broad-exception-caught
            return jsonify({
                'error': 'Bad Request',
                'message': 'Request body must be valid JSON'
            }), 400

        # Check if request body is empty or None
        if json_data is None:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Request body must be JSON'
            }), 400

        # Validate request data using Marshmallow schema
        schema = UserProfileUpdateSchema()
        validated_data = schema.load(json_data)

        # At least one field must be provided
        if not validated_data:
            return jsonify({
                'error': 'Bad Request',
                'message': 'At least one field (firstname, lastname, email, or password) must be provided'
            }), 400

        # Update user profile
        updated_user = UserService.update_user_profile(
            user=current_user,
            firstname=validated_data.get('firstname'),
            lastname=validated_data.get('lastname'),
            email=validated_data.get('email'),
            password=validated_data.get('password')
        )

        # Format response
        response = UserService.format_user_detail(updated_user)
        response['message'] = 'Profile updated successfully'

        return jsonify(response), 200

    except ValidationError as err:
        return handle_validation_error(err)
    except EmailAlreadyExistsError as e:
        return handle_conflict_error(e.message)
    except Exception as e:  # pylint: disable=broad-exception-caught
        return handle_general_error(e)


@user_bp.route('/', methods=['GET'])
@token_required
@admin_required
def get_all_users(_current_user):
    """Get paginated list of all users (admin only)."""
    # Get pagination parameters from query string
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    result = UserService.get_paginated_users(page, per_page)

    return jsonify(result), 200
