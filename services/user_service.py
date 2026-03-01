"""
User service - Business logic for user operations.
Handles user registration, authentication, and user management.
"""

from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from models import User, Roles
import jwt
import os
from datetime import datetime, timedelta, timezone

# JWT Configuration
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dummy-secret-key-for-development')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24


class UserService:
    """Service class for user-related business logic."""

    @staticmethod
    def validate_registration_data(data):
        """
        Validate user registration data.

        Args:
            data: Dictionary containing registration data

        Returns:
            tuple: (is_valid, error_message)
        """
        if not data:
            return False, 'Request body must be JSON'

        required_fields = ['firstname', 'lastname', 'email', 'password']
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            return False, f'Missing required fields: {", ".join(missing_fields)}'

        # Validate field lengths
        if len(data['firstname']) > 30:
            return False, 'firstname must be 30 characters or less'
        if len(data['lastname']) > 30:
            return False, 'lastname must be 30 characters or less'
        if len(data['email']) > 30:
            return False, 'email must be 30 characters or less'
        if len(data['password']) < 6:
            return False, 'password must be at least 6 characters'

        return True, None

    @staticmethod
    def validate_role(role_str):
        """
        Validate and convert role string to Roles enum.

        Args:
            role_str: String role ('admin' or 'user')

        Returns:
            tuple: (role_enum, error_message)
        """
        if not role_str:
            return Roles.user, None

        role_str = role_str.lower()
        if role_str == 'admin':
            return Roles.admin, None
        elif role_str == 'user':
            return Roles.user, None
        else:
            return None, 'Invalid role. Must be "admin" or "user"'

    @staticmethod
    def email_exists(email):
        """
        Check if email already exists in database.

        Args:
            email: Email address to check

        Returns:
            bool: True if email exists, False otherwise
        """
        return User.query.filter_by(email=email).first() is not None

    @staticmethod
    def create_user(firstname, lastname, email, password, role=Roles.user):
        """
        Create a new user in the database.

        Args:
            firstname: User's first name
            lastname: User's last name
            email: User's email address
            password: Plain text password (will be hashed)
            role: User role (Roles enum)

        Returns:
            User: Created user object
        """
        password_hash = generate_password_hash(password)

        new_user = User(
            firstname=firstname,
            lastname=lastname,
            email=email,
            password_hash=password_hash,
            role=role
        )

        db.session.add(new_user)
        db.session.commit()

        return new_user

    @staticmethod
    def generate_token(user):
        """
        Generate JWT token for a user.

        Args:
            user: User object

        Returns:
            str: JWT token
        """
        token_payload = {
            'user_id': str(user.id),
            'email': user.email,
            'role': user.role.name,
            'exp': datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS),
            'iat': datetime.now(timezone.utc)
        }

        token = jwt.encode(token_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return token

    @staticmethod
    def format_user_response(user, include_token=False):
        """
        Format user data for API response.

        Args:
            user: User object
            include_token: Whether to include JWT token in response

        Returns:
            dict: Formatted user data
        """
        response = {
            'user': {
                'id': str(user.id),
                'firstname': user.firstname,
                'lastname': user.lastname,
                'email': user.email,
                'role': user.role.name,
                'created_at': user.created_at.isoformat()
            }
        }

        if include_token:
            token = UserService.generate_token(user)
            response['token'] = token
            response['token_type'] = 'Bearer'
            response['expires_in'] = JWT_EXPIRATION_HOURS * 3600  # seconds

        return response

    @staticmethod
    def authenticate_user(email, password):
        """
        Authenticate user with email and password.

        Args:
            email: User's email
            password: User's password

        Returns:
            tuple: (user_object or None, error_message or None)
        """
        user = User.query.filter_by(email=email).first()

        if not user:
            return None, 'Invalid email or password'

        if not check_password_hash(user.password_hash, password):
            return None, 'Invalid email or password'

        return user, None

    @staticmethod
    def verify_token(token):
        """
        Verify and decode JWT token.

        Args:
            token: JWT token string

        Returns:
            tuple: (user_object or None, error_message or None)
        """
        try:
            import uuid as uuid_lib
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

            # Convert string UUID to UUID object for database compatibility
            user_id = payload['user_id']
            if isinstance(user_id, str):
                user_id = uuid_lib.UUID(user_id)

            user = User.query.filter_by(id=user_id).first()

            if not user:
                return None, 'User not found'

            return user, None

        except jwt.ExpiredSignatureError:
            return None, 'Token expired'
        except jwt.InvalidTokenError:
            return None, 'Invalid token'

    @staticmethod
    def get_user_by_id(user_id):
        """
        Get user by ID.

        Args:
            user_id: User's UUID

        Returns:
            User: User object or None
        """
        return User.query.filter_by(id=user_id).first()

    @staticmethod
    def get_paginated_users(page=1, per_page=10):
        """
        Get paginated list of users.

        Args:
            page: Page number (1-indexed)
            per_page: Number of items per page

        Returns:
            dict: Paginated users data with metadata
        """
        # Validate pagination parameters
        if page < 1:
            page = 1
        if per_page < 1:
            per_page = 10
        if per_page > 100:
            per_page = 100

        # Query users with pagination
        pagination = User.query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        users_data = [{
            'id': str(user.id),
            'firstname': user.firstname,
            'lastname': user.lastname,
            'email': user.email,
            'role': user.role.name,
            'created_at': user.created_at.isoformat()
        } for user in pagination.items]

        return {
            'users': users_data,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total_pages': pagination.pages,
                'total_items': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev,
                'next_page': pagination.next_num if pagination.has_next else None,
                'prev_page': pagination.prev_num if pagination.has_prev else None
            }
        }

    @staticmethod
    def format_user_detail(user):
        """
        Format detailed user data including updated_at.

        Args:
            user: User object

        Returns:
            dict: Formatted user data
        """
        return {
            'user': {
                'id': str(user.id),
                'firstname': user.firstname,
                'lastname': user.lastname,
                'email': user.email,
                'role': user.role.name,
                'created_at': user.created_at.isoformat(),
                'updated_at': user.updated_at.isoformat()
            }
        }
