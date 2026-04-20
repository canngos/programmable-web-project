"""
Unit tests for UserService class.
Tests all business logic methods in the user service layer.
"""

from datetime import datetime, timezone, timedelta
from ticket_management_system.extensions import db
from ticket_management_system.models import User, Roles
from ticket_management_system.resources.user_service import UserService
from ticket_management_system.exceptions import (
    InvalidRoleError,
    InvalidTokenError,
    ResourcePermissionError,
    TokenExpiredError,
    UserNotFoundError,
)
import jwt
import os
import pytest


class TestUserServiceValidation:
    """Test validation methods."""

    def test_validate_role_user(self):
        """Test role validation for user role."""
        role = UserService.validate_role('user')
        assert role == Roles.user

    def test_validate_role_admin(self):
        """Test role validation for admin role."""
        role = UserService.validate_role('admin')
        assert role == Roles.admin

    def test_validate_role_case_insensitive(self):
        """Test role validation is case insensitive."""
        role = UserService.validate_role('ADMIN')
        assert role == Roles.admin

    def test_validate_role_invalid(self):
        """Test role validation with invalid role raises exception."""
        with pytest.raises(InvalidRoleError):
            UserService.validate_role('superuser')

    def test_validate_role_empty(self):
        """Test role validation with empty string defaults to user."""
        role = UserService.validate_role('')
        assert role == Roles.user

    def test_validate_role_none(self):
        """Test role validation with None defaults to user."""
        role = UserService.validate_role(None)
        assert role == Roles.user


class TestUserServiceDatabaseOperations:
    """Test database operations."""

    def test_email_exists_true(self, app, test_user):
        """Test email_exists returns True for existing email."""
        with app.app_context():
            exists = UserService.email_exists(test_user.email)
            assert exists is True

    def test_email_exists_false(self, app):
        """Test email_exists returns False for non-existing email."""
        with app.app_context():
            exists = UserService.email_exists('nonexistent@example.com')
            assert exists is False

    def test_create_user(self, app):
        """Test creating a new user."""
        with app.app_context():
            user = UserService.create_user(
                firstname='Jane',
                lastname='Smith',
                email='jane@example.com',
                role=Roles.user
            )

            assert user.id is not None
            assert user.firstname == 'Jane'
            assert user.lastname == 'Smith'
            assert user.email == 'jane@example.com'
            assert user.role == Roles.user
            assert user.created_at is not None

            # Cleanup
            db.session.delete(user)
            db.session.commit()

    def test_create_user_with_admin_role(self, app):
        """Test creating a user with admin role."""
        with app.app_context():
            user = UserService.create_user(
                firstname='Admin',
                lastname='User',
                email='admin2@example.com',
                role=Roles.admin
            )

            assert user.role == Roles.admin

            # Cleanup
            db.session.delete(user)
            db.session.commit()

    def test_get_user_by_id(self, app, test_user):
        """Test getting user by ID."""
        with app.app_context():
            user = UserService.get_user_by_id(test_user.id)
            assert user is not None
            assert user.id == test_user.id
            assert user.email == test_user.email

    def test_get_user_by_id_not_found(self, app):
        """Test getting user by non-existent ID."""
        with app.app_context():
            import uuid
            fake_id = uuid.uuid4()
            user = UserService.get_user_by_id(fake_id)
            assert user is None


class TestUserServiceTokenAuthentication:
    """Test scoped token authentication methods."""

    def test_generate_token(self, app, test_user):
        """Test JWT token generation."""
        with app.app_context():
            token = UserService.generate_token(test_user)
            assert token is not None
            assert isinstance(token, str)

            # Decode and verify token
            secret = os.getenv('JWT_SECRET_KEY', 'dummy-secret-key-for-development')
            payload = jwt.decode(token, secret, algorithms=['HS256'])

            assert payload['user_id'] == str(test_user.id)
            assert payload['email'] == test_user.email
            assert payload['role'] == test_user.role.name
            assert 'permitted_resources' in payload
            assert 'users:read:self' in payload['permitted_resources']
            assert 'exp' in payload
            assert 'iat' in payload

    def test_verify_token_valid(self, app, test_user):
        """Test verifying a valid token."""
        with app.app_context():
            token = UserService.generate_token(test_user)
            user = UserService.verify_token(token)

            assert user is not None
            assert user.id == test_user.id

    def test_verify_token_with_required_resource(self, app, test_user):
        """Test token verification succeeds for permitted resource."""
        with app.app_context():
            token = UserService.generate_token(test_user)
            user = UserService.verify_token(token, required_resource='users:read:self')

            assert user.id == test_user.id

    def test_verify_token_rejects_unpermitted_resource(self, app, test_user):
        """Test token verification rejects missing resource scope."""
        with app.app_context():
            token = UserService.generate_token(test_user)

            with pytest.raises(ResourcePermissionError):
                UserService.verify_token(token, required_resource='users:read:all')

    def test_verify_token_expired(self, app, test_user):
        """Test verifying an expired token raises exception."""
        with app.app_context():
            # Create an expired token
            secret = os.getenv('JWT_SECRET_KEY', 'dummy-secret-key-for-development')
            payload = {
                'user_id': str(test_user.id),
                'email': test_user.email,
                'role': test_user.role.name,
                'permitted_resources': UserService.get_permitted_resources(test_user),
                'exp': datetime.now(timezone.utc) - timedelta(hours=1),  # Expired 1 hour ago
                'iat': datetime.now(timezone.utc) - timedelta(hours=2)
            }
            token = jwt.encode(payload, secret, algorithm='HS256')

            with pytest.raises(TokenExpiredError):
                UserService.verify_token(token)

    def test_verify_token_invalid(self, app):
        """Test verifying an invalid token raises exception."""
        with app.app_context():
            with pytest.raises(InvalidTokenError):
                UserService.verify_token('invalid.token.here')

    def test_verify_token_user_not_found(self, app):
        """Test verifying token for non-existent user raises exception."""
        with app.app_context():
            import uuid
            fake_id = str(uuid.uuid4())
            secret = os.getenv('JWT_SECRET_KEY', 'dummy-secret-key-for-development')
            payload = {
                'user_id': fake_id,
                'email': 'fake@example.com',
                'role': 'user',
                'permitted_resources': ['users:read:self'],
                'exp': datetime.now(timezone.utc) + timedelta(hours=24),
                'iat': datetime.now(timezone.utc)
            }
            token = jwt.encode(payload, secret, algorithm='HS256')

            with pytest.raises(UserNotFoundError):
                UserService.verify_token(token)


class TestUserServiceFormatting:
    """Test response formatting methods."""

    def test_format_user_response_without_token(self, app, test_user):
        """Test formatting user response without token."""
        with app.app_context():
            response = UserService.format_user_response(test_user, include_token=False)

            assert 'user' in response
            assert response['user']['id'] == str(test_user.id)
            assert response['user']['firstname'] == test_user.firstname
            assert response['user']['lastname'] == test_user.lastname
            assert response['user']['email'] == test_user.email
            assert response['user']['role'] == test_user.role.name
            assert 'created_at' in response['user']

            assert 'token' not in response
            assert 'token_type' not in response
            assert 'expires_in' not in response

    def test_format_user_response_with_token(self, app, test_user):
        """Test formatting user response with token."""
        with app.app_context():
            response = UserService.format_user_response(test_user, include_token=True)

            assert 'user' in response
            assert 'token' in response
            assert 'token_type' in response
            assert 'expires_in' in response

            assert response['token_type'] == 'Bearer'
            assert response['expires_in'] == UserService.token_expires_in_seconds()
            assert 'permitted_resources' in response
            assert isinstance(response['token'], str)

    def test_format_user_detail(self, app, test_user):
        """Test formatting detailed user data."""
        with app.app_context():
            response = UserService.format_user_detail(test_user)

            assert 'user' in response
            assert response['user']['id'] == str(test_user.id)
            assert 'created_at' in response['user']
            assert 'updated_at' in response['user']


class TestUserServicePagination:
    """Test pagination methods."""

    def test_get_paginated_users_default(self, app, multiple_users):
        """Test getting paginated users with default parameters."""
        with app.app_context():
            result = UserService.get_paginated_users()

            assert 'users' in result
            assert 'pagination' in result
            assert isinstance(result['users'], list)
            assert len(result['users']) <= 10  # Default per_page
            assert result['pagination']['page'] == 1
            assert result['pagination']['per_page'] == 10
            assert result['pagination']['total_items'] >= 5

    def test_get_paginated_users_custom_page_size(self, app, multiple_users):
        """Test getting paginated users with custom page size."""
        with app.app_context():
            result = UserService.get_paginated_users(page=1, per_page=3)

            assert len(result['users']) <= 3
            assert result['pagination']['per_page'] == 3

    def test_get_paginated_users_second_page(self, app, multiple_users):
        """Test getting second page of users."""
        with app.app_context():
            result = UserService.get_paginated_users(page=2, per_page=3)

            assert result['pagination']['page'] == 2
            assert result['pagination']['has_prev'] is True

    def test_get_paginated_users_invalid_page(self, app, multiple_users):
        """Test pagination with invalid page number (should default to 1)."""
        with app.app_context():
            result = UserService.get_paginated_users(page=-1, per_page=10)

            assert result['pagination']['page'] == 1

    def test_get_paginated_users_invalid_per_page(self, app, multiple_users):
        """Test pagination with invalid per_page (should default to 10)."""
        with app.app_context():
            result = UserService.get_paginated_users(page=1, per_page=-5)

            assert result['pagination']['per_page'] == 10

    def test_get_paginated_users_max_per_page(self, app, multiple_users):
        """Test pagination with per_page exceeding max (should cap at 100)."""
        with app.app_context():
            result = UserService.get_paginated_users(page=1, per_page=200)

            assert result['pagination']['per_page'] == 100

    def test_get_paginated_users_metadata(self, app, multiple_users):
        """Test pagination metadata is correct."""
        with app.app_context():
            result = UserService.get_paginated_users(page=1, per_page=3)

            pagination = result['pagination']
            assert 'total_pages' in pagination
            assert 'total_items' in pagination
            assert 'has_next' in pagination
            assert 'has_prev' in pagination
            assert 'next_page' in pagination
            assert 'prev_page' in pagination

            assert pagination['has_prev'] is False
            assert pagination['prev_page'] is None

            if pagination['total_items'] > 3:
                assert pagination['has_next'] is True
                assert pagination['next_page'] == 2
