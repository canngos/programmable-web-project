"""Business logic for user operations."""
import os
from datetime import datetime, timedelta, timezone
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from ticket_management_system.extensions import db
from ticket_management_system.models import User, Roles
from ticket_management_system.utils import format_pagination_response
from ticket_management_system.exceptions import (
    InvalidCredentialsError,
    UserNotFoundError,
    TokenExpiredError,
    InvalidTokenError,
    EmailAlreadyExistsError,
    InvalidRoleError
)

# JWT Configuration
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dummy-secret-key-for-development')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24


class UserService:
    """Service class for user operations."""
    @staticmethod
    def validate_role(role_str):
        """Validate and convert role string to Roles enum."""
        if not role_str:
            return Roles.user

        role_str = role_str.lower()
        if role_str == 'admin':
            return Roles.admin
        if role_str == 'user':
            return Roles.user
        raise InvalidRoleError(role_str)

    @staticmethod
    def email_exists(email):
        """Check if email already exists in database."""
        return User.query.filter_by(email=email).first() is not None

    @staticmethod
    def create_user(firstname, lastname, email, password, role=Roles.user):
        """Create a new user with hashed password."""
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
        """Generate JWT token for user authentication."""
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
        """Format user data for API response, optionally including JWT token."""
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
        """Authenticate user with credentials."""
        user = User.query.filter_by(email=email).first()

        if not user:
            raise InvalidCredentialsError()

        if not check_password_hash(user.password_hash, password):
            raise InvalidCredentialsError()

        return user

    @staticmethod
    def verify_token(token):
        """Verify and decode JWT token, return user or raise exception."""
        try:
            import uuid as uuid_lib
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

            # Convert string UUID to UUID object for database compatibility
            user_id = payload['user_id']
            if isinstance(user_id, str):
                user_id = uuid_lib.UUID(user_id)

            user = User.query.filter_by(id=user_id).first()

            if not user:
                raise UserNotFoundError()

            return user

        except jwt.ExpiredSignatureError as exc:
            raise TokenExpiredError() from exc
        except jwt.InvalidTokenError as exc:
            raise InvalidTokenError() from exc

    @staticmethod
    def get_user_by_id(user_id):
        """Get user by ID."""
        return User.query.filter_by(id=user_id).first()

    @staticmethod
    def get_paginated_users(page=1, per_page=10):
        """Get paginated list of all users."""
        # Validate pagination parameters
        page = max(page, 1)
        per_page = per_page if per_page > 0 else 10  # Default to 10 if invalid
        per_page = min(per_page, 100)

        # Query users with pagination
        pagination = User.query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        users_data = [UserService.format_user_detail(user) for user in pagination.items]

        return format_pagination_response('users', users_data, pagination)

    @staticmethod
    def format_user_detail(user):
        """Format user details for response."""
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

    @staticmethod
    def update_user_profile(user, firstname=None, lastname=None, email=None, password=None):
        """Update user profile."""
        # Validate email uniqueness if provided
        if email and email != user.email:
            if UserService.email_exists(email):
                raise EmailAlreadyExistsError()
            user.email = email

        # Update firstname if provided
        if firstname is not None:
            user.firstname = firstname

        # Update lastname if provided
        if lastname is not None:
            user.lastname = lastname

        # Update password if provided (hash it)
        if password is not None:
            user.password_hash = generate_password_hash(password)

        user.updated_at = datetime.now(timezone.utc)

        # Save changes
        db.session.commit()
        return user
