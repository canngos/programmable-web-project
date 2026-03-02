"""
Unit tests for user routes endpoints.
Tests all HTTP endpoints in the user routes blueprint.
"""

from ticket_management_system.extensions import db
from ticket_management_system.models import User, Roles
from ticket_management_system.resources.user_service import UserService


class TestRegisterEndpoint:
    """Test POST /api/users/register endpoint."""

    def test_register_success(self, client, app):
        """Test successful user registration."""
        with app.app_context():
            response = client.post('/api/users/register',
                json={
                    'firstname': 'John',
                    'lastname': 'Doe',
                    'email': 'john@example.com',
                    'password': 'password123'
                })

            assert response.status_code == 201
            data = response.get_json()

            assert data['message'] == 'User registered successfully'
            assert 'user' in data
            assert data['user']['firstname'] == 'John'
            assert data['user']['lastname'] == 'Doe'
            assert data['user']['email'] == 'john@example.com'
            assert data['user']['role'] == 'user'

            assert 'token' in data
            assert 'token_type' in data
            assert data['token_type'] == 'Bearer'
            assert 'expires_in' in data

            # Cleanup
            user = User.query.filter_by(email='john@example.com').first()
            if user:
                db.session.delete(user)
                db.session.commit()

    def test_register_with_admin_role(self, client, app):
        """Test registration with admin role."""
        with app.app_context():
            response = client.post('/api/users/register',
                json={
                    'firstname': 'Admin',
                    'lastname': 'User',
                    'email': 'admin@example.com',
                    'password': 'admin123',
                    'role': 'admin'
                })

            assert response.status_code == 201
            data = response.get_json()
            assert data['user']['role'] == 'admin'

            # Cleanup
            user = User.query.filter_by(email='admin@example.com').first()
            if user:
                db.session.delete(user)
                db.session.commit()

    def test_register_missing_fields(self, client):
        """Test registration with missing required fields."""
        response = client.post('/api/users/register',
            json={
                'firstname': 'John',
                'email': 'john@example.com'
            })

        assert response.status_code == 400
        data = response.get_json()
        assert data['error'] == 'Bad Request'
        assert data['message'] == 'Validation failed'
        assert 'errors' in data
        assert 'lastname' in data['errors']
        assert 'password' in data['errors']

    def test_register_empty_body(self, client):
        """Test registration with empty request body."""
        response = client.post('/api/users/register',
            data='',
            content_type='application/json')

        assert response.status_code == 400
        data = response.get_json()
        assert data['error'] == 'Bad Request'

    def test_register_duplicate_email(self, client, app, test_user):
        """Test registration with existing email."""
        with app.app_context():
            response = client.post('/api/users/register',
                json={
                    'firstname': 'Jane',
                    'lastname': 'Doe',
                    'email': test_user.email,
                    'password': 'password123'
                })

            assert response.status_code == 409
            data = response.get_json()
            assert data['error'] == 'Conflict'
            assert 'Email already registered' in data['message']

    def test_register_firstname_too_long(self, client):
        """Test registration with firstname exceeding max length."""
        response = client.post('/api/users/register',
            json={
                'firstname': 'a' * 31,
                'lastname': 'Doe',
                'email': 'john@example.com',
                'password': 'password123'
            })

        assert response.status_code == 400
        data = response.get_json()
        assert data['message'] == 'Validation failed'
        assert 'errors' in data
        assert 'firstname' in data['errors']

    def test_register_password_too_short(self, client):
        """Test registration with password too short."""
        response = client.post('/api/users/register',
            json={
                'firstname': 'John',
                'lastname': 'Doe',
                'email': 'john@example.com',
                'password': '12345'
            })

        assert response.status_code == 400
        data = response.get_json()
        assert data['message'] == 'Validation failed'
        assert 'errors' in data
        assert 'password' in data['errors']

    def test_register_invalid_role(self, client):
        """Test registration with invalid role."""
        response = client.post('/api/users/register',
            json={
                'firstname': 'John',
                'lastname': 'Doe',
                'email': 'john@example.com',
                'password': 'password123',
                'role': 'superuser'
            })

        assert response.status_code == 400
        data = response.get_json()
        # Invalid role is caught by Marshmallow schema validation
        assert data['message'] == 'Validation failed'
        assert 'errors' in data
        assert 'role' in data['errors']


class TestLoginEndpoint:
    """Test POST /api/users/login endpoint."""

    def test_login_success(self, client, app, test_user):
        """Test successful login."""
        with app.app_context():
            response = client.post('/api/users/login',
                json={
                    'email': test_user.email,
                    'password': 'password123'
                })

            assert response.status_code == 200
            data = response.get_json()

            assert data['message'] == 'Login successful'
            assert 'user' in data
            assert data['user']['email'] == test_user.email
            assert 'token' in data
            assert 'token_type' in data
            assert data['token_type'] == 'Bearer'

    def test_login_wrong_password(self, client, app, test_user):
        """Test login with wrong password."""
        with app.app_context():
            response = client.post('/api/users/login',
                json={
                    'email': test_user.email,
                    'password': 'wrongpassword'
                })

            assert response.status_code == 401
            data = response.get_json()
            assert data['error'] == 'Unauthorized'
            assert 'Invalid email or password' in data['message']

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user."""
        response = client.post('/api/users/login',
            json={
                'email': 'nonexistent@example.com',
                'password': 'password123'
            })

        assert response.status_code == 401
        data = response.get_json()
        assert data['error'] == 'Unauthorized'

    def test_login_missing_email(self, client):
        """Test login without email."""
        response = client.post('/api/users/login',
            json={
                'password': 'password123'
            })

        assert response.status_code == 400
        data = response.get_json()
        assert 'Email and password are required' in data['message']

    def test_login_missing_password(self, client):
        """Test login without password."""
        response = client.post('/api/users/login',
            json={
                'email': 'test@example.com'
            })

        assert response.status_code == 400
        data = response.get_json()
        assert 'Email and password are required' in data['message']

    def test_login_empty_body(self, client):
        """Test login with empty request body."""
        response = client.post('/api/users/login',
            data='',
            content_type='application/json')

        assert response.status_code == 400
        data = response.get_json()
        assert data['error'] == 'Bad Request'


class TestGetCurrentUserEndpoint:
    """Test GET /api/users/me endpoint."""

    def test_get_current_user_success(self, client, app, auth_headers):
        """Test getting current user profile with valid token."""
        with app.app_context():
            response = client.get('/api/users/me', headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()

            assert 'user' in data
            assert 'id' in data['user']
            assert 'firstname' in data['user']
            assert 'lastname' in data['user']
            assert 'email' in data['user']
            assert 'role' in data['user']
            assert 'created_at' in data['user']
            assert 'updated_at' in data['user']

    def test_get_current_user_no_token(self, client):
        """Test getting current user without token."""
        response = client.get('/api/users/me')

        assert response.status_code == 401
        data = response.get_json()
        assert data['error'] == 'Authentication required'
        assert 'No token provided' in data['message']

    def test_get_current_user_invalid_token(self, client):
        """Test getting current user with invalid token."""
        headers = {'Authorization': 'Bearer invalid.token.here'}
        response = client.get('/api/users/me', headers=headers)

        assert response.status_code == 401
        data = response.get_json()
        assert 'Invalid token' in data['error'] or 'Token expired' in data['error']

    def test_get_current_user_malformed_header(self, client):
        """Test getting current user with malformed Authorization header."""
        headers = {'Authorization': 'InvalidFormat'}
        response = client.get('/api/users/me', headers=headers)

        assert response.status_code == 401
        data = response.get_json()
        assert 'Invalid authorization header format' in data['error']

    def test_get_current_user_expired_token(self, client, app, expired_token):
        """Test getting current user with expired token."""
        with app.app_context():
            headers = {'Authorization': f'Bearer {expired_token}'}
            response = client.get('/api/users/me', headers=headers)

            assert response.status_code == 401
            data = response.get_json()
            assert 'Token expired' in data['error']


class TestGetAllUsersEndpoint:
    """Test GET /api/users/ endpoint."""

    def test_get_all_users_as_admin(self, client, app, admin_headers, multiple_users):
        """Test getting all users as admin."""
        with app.app_context():
            response = client.get('/api/users/', headers=admin_headers)

            assert response.status_code == 200
            data = response.get_json()

            assert 'users' in data
            assert 'pagination' in data
            assert isinstance(data['users'], list)
            assert len(data['users']) > 0

            # Check pagination metadata
            pagination = data['pagination']
            assert 'page' in pagination
            assert 'per_page' in pagination
            assert 'total_pages' in pagination
            assert 'total_items' in pagination
            assert 'has_next' in pagination
            assert 'has_prev' in pagination

    def test_get_all_users_pagination(self, client, app, admin_headers, multiple_users):
        """Test pagination parameters."""
        with app.app_context():
            response = client.get('/api/users/?page=1&per_page=3', headers=admin_headers)

            assert response.status_code == 200
            data = response.get_json()

            assert len(data['users']) <= 3
            assert data['pagination']['page'] == 1
            assert data['pagination']['per_page'] == 3

    def test_get_all_users_second_page(self, client, app, admin_headers, multiple_users):
        """Test getting second page."""
        with app.app_context():
            response = client.get('/api/users/?page=2&per_page=2', headers=admin_headers)

            assert response.status_code == 200
            data = response.get_json()

            assert data['pagination']['page'] == 2
            assert data['pagination']['has_prev'] is True

    def test_get_all_users_as_regular_user(self, client, app, auth_headers):
        """Test getting all users as regular user (should fail)."""
        with app.app_context():
            response = client.get('/api/users/', headers=auth_headers)

            assert response.status_code == 403
            data = response.get_json()
            assert data['error'] == 'Forbidden'
            assert 'Admin privileges required' in data['message']

    def test_get_all_users_no_token(self, client):
        """Test getting all users without token."""
        response = client.get('/api/users/')

        assert response.status_code == 401
        data = response.get_json()
        assert data['error'] == 'Authentication required'

    def test_get_all_users_invalid_token(self, client):
        """Test getting all users with invalid token."""
        headers = {'Authorization': 'Bearer invalid.token'}
        response = client.get('/api/users/', headers=headers)

        assert response.status_code == 401


class TestTokenDecorator:
    """Test token_required decorator functionality."""

    def test_token_required_with_valid_token(self, client, app, auth_headers):
        """Test protected endpoint with valid token."""
        with app.app_context():
            response = client.get('/api/users/me', headers=auth_headers)
            assert response.status_code == 200

    def test_token_required_without_token(self, client):
        """Test protected endpoint without token."""
        response = client.get('/api/users/me')
        assert response.status_code == 401
        data = response.get_json()
        assert 'No token provided' in data['message']

    def test_token_required_with_bearer_prefix_missing(self, client, app, test_user):
        """Test token without Bearer prefix."""
        with app.app_context():
            token = UserService.generate_token(test_user)
            # Send token without "Bearer " prefix
            headers = {'Authorization': token}
            response = client.get('/api/users/me', headers=headers)

            assert response.status_code == 401


class TestAdminDecorator:
    """Test admin_required decorator functionality."""

    def test_admin_required_with_admin_user(self, client, app, admin_headers):
        """Test admin-only endpoint with admin token."""
        with app.app_context():
            response = client.get('/api/users/', headers=admin_headers)
            assert response.status_code == 200

    def test_admin_required_with_regular_user(self, client, app, auth_headers):
        """Test admin-only endpoint with regular user token."""
        with app.app_context():
            response = client.get('/api/users/', headers=auth_headers)
            assert response.status_code == 403
            data = response.get_json()
            assert 'Admin privileges required' in data['message']


class TestResponseFormats:
    """Test response format consistency."""

    def test_error_response_format(self, client):
        """Test error responses have consistent format."""
        response = client.post('/api/users/login',
            json={'email': 'test@example.com'})

        assert response.status_code == 400
        data = response.get_json()

        assert 'error' in data
        assert 'message' in data
        assert isinstance(data['error'], str)
        assert isinstance(data['message'], str)

    def test_success_response_format_register(self, client, app):
        """Test successful registration response format."""
        with app.app_context():
            response = client.post('/api/users/register',
                json={
                    'firstname': 'Test',
                    'lastname': 'User',
                    'email': 'testformat@example.com',
                    'password': 'password123'
                })

            assert response.status_code == 201
            data = response.get_json()

            assert 'message' in data
            assert 'user' in data
            assert 'token' in data
            assert 'token_type' in data
            assert 'expires_in' in data

            # Cleanup
            user = User.query.filter_by(email='testformat@example.com').first()
            if user:
                db.session.delete(user)
                db.session.commit()

    def test_json_content_type(self, client, app, auth_headers):
        """Test responses have JSON content type."""
        with app.app_context():
            response = client.get('/api/users/me', headers=auth_headers)
            assert response.content_type == 'application/json'


class TestUpdateCurrentUserEndpoint:
    """Test PATCH /api/users/me endpoint."""

    def test_update_firstname_only(self, client, auth_headers):
        """Test successfully updating only the firstname field."""
        response = client.patch('/api/users/me',
            json={'firstname': 'UpdatedFirst'},
            headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'Profile updated successfully'
        assert data['user']['firstname'] == 'UpdatedFirst'
        assert 'user' in data
        assert 'id' in data['user']

    def test_update_lastname_only(self, client, auth_headers):
        """Test successfully updating only the lastname field."""
        response = client.patch('/api/users/me',
            json={'lastname': 'UpdatedLastName'},
            headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'Profile updated successfully'
        assert data['user']['lastname'] == 'UpdatedLastName'

    def test_update_email_to_unique_value(self, client, auth_headers):
        """Test successfully updating email to a unique value."""
        new_email = 'unique_new_email@example.com'
        response = client.patch('/api/users/me',
            json={'email': new_email},
            headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data['user']['email'] == new_email

    def test_update_password_only(self, client, auth_headers):
        """Test successfully updating password."""
        response = client.patch('/api/users/me',
            json={'password': 'newSecurePassword123'},
            headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'Profile updated successfully'
        # Password hash should not be in response
        assert 'password' not in data['user']
        assert 'password_hash' not in data['user']

    def test_update_multiple_fields_simultaneously(self, client, auth_headers):
        """Test updating multiple fields in a single request."""
        update_data = {
            'firstname': 'MultiFirst',
            'lastname': 'MultiLast',
            'email': 'multi_update@example.com'
        }
        response = client.patch('/api/users/me',
            json=update_data,
            headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data['user']['firstname'] == 'MultiFirst'
        assert data['user']['lastname'] == 'MultiLast'
        assert data['user']['email'] == 'multi_update@example.com'

    def test_update_all_fields_together(self, client, auth_headers):
        """Test updating all allowed fields together."""
        update_data = {
            'firstname': 'AllFirst',
            'lastname': 'AllLast',
            'email': 'all_fields@example.com',
            'password': 'newPassword123'
        }
        response = client.patch('/api/users/me',
            json=update_data,
            headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data['user']['firstname'] == 'AllFirst'
        assert data['user']['lastname'] == 'AllLast'
        assert data['user']['email'] == 'all_fields@example.com'

    def test_update_with_empty_json_object(self, client, auth_headers):
        """Test update with empty JSON object returns 400."""
        response = client.patch('/api/users/me',
            json={},
            headers=auth_headers)

        assert response.status_code == 400
        data = response.get_json()
        assert data['error'] == 'Bad Request'

    def test_update_with_null_body(self, client, auth_headers):
        """Test update with null/None body returns 400."""
        response = client.patch('/api/users/me',
            data='',
            content_type='application/json',
            headers=auth_headers)

        assert response.status_code == 400
        data = response.get_json()
        assert data['error'] == 'Bad Request'
        assert 'message' in data

    def test_update_with_invalid_json(self, client, auth_headers):
        """Test update with malformed JSON returns 400."""
        response = client.patch('/api/users/me',
            data='{"invalid": json}',
            content_type='application/json',
            headers=auth_headers)

        assert response.status_code == 400
        data = response.get_json()
        assert data['error'] == 'Bad Request'

    def test_update_email_to_existing_email(self, client, auth_headers, admin_user):
        """Test updating email to one already taken by another user returns 409."""
        response = client.patch('/api/users/me',
            json={'email': admin_user.email},
            headers=auth_headers)

        assert response.status_code == 409
        data = response.get_json()
        assert data['error'] == 'Conflict'
        assert 'already in use' in data['message'].lower()

    def test_update_firstname_exceeds_max_length(self, client, auth_headers):
        """Test firstname validation when exceeding 30 characters."""
        response = client.patch('/api/users/me',
            json={'firstname': 'a' * 31},
            headers=auth_headers)

        assert response.status_code == 400
        data = response.get_json()
        assert data['message'] == 'Validation failed'
        assert 'errors' in data
        assert 'firstname' in data['errors']

    def test_update_lastname_exceeds_max_length(self, client, auth_headers):
        """Test lastname validation when exceeding 30 characters."""
        response = client.patch('/api/users/me',
            json={'lastname': 'b' * 31},
            headers=auth_headers)

        assert response.status_code == 400
        data = response.get_json()
        assert data['message'] == 'Validation failed'
        assert 'errors' in data
        assert 'lastname' in data['errors']

    def test_update_email_exceeds_max_length(self, client, auth_headers):
        """Test email validation when exceeding 255 characters."""
        long_email = 'a' * 250 + '@example.com'  # Total > 255
        response = client.patch('/api/users/me',
            json={'email': long_email},
            headers=auth_headers)

        assert response.status_code == 400
        data = response.get_json()
        assert data['message'] == 'Validation failed'
        assert 'errors' in data
        assert 'email' in data['errors']

    def test_update_password_below_minimum_length(self, client, auth_headers):
        """Test password validation when below 6 characters."""
        response = client.patch('/api/users/me',
            json={'password': '12345'},
            headers=auth_headers)

        assert response.status_code == 400
        data = response.get_json()
        assert data['message'] == 'Validation failed'
        assert 'errors' in data
        assert 'password' in data['errors']

    def test_update_firstname_with_only_whitespace(self, client, auth_headers):
        """Test firstname validation rejects whitespace-only values."""
        response = client.patch('/api/users/me',
            json={'firstname': '   '},
            headers=auth_headers)

        assert response.status_code == 400
        data = response.get_json()
        assert data['message'] == 'Validation failed'
        assert 'errors' in data
        assert 'firstname' in data['errors']

    def test_update_lastname_with_only_whitespace(self, client, auth_headers):
        """Test lastname validation rejects whitespace-only values."""
        response = client.patch('/api/users/me',
            json={'lastname': '   '},
            headers=auth_headers)

        assert response.status_code == 400
        data = response.get_json()
        assert data['message'] == 'Validation failed'
        assert 'errors' in data
        assert 'lastname' in data['errors']

    def test_update_email_with_invalid_format(self, client, auth_headers):
        """Test email validation rejects invalid email formats."""
        invalid_emails = [
            'not-an-email',
            'missing@domain',
            '@example.com',
            'user@',
            'user space@example.com'
        ]

        for invalid_email in invalid_emails:
            response = client.patch('/api/users/me',
                json={'email': invalid_email},
                headers=auth_headers)

            assert response.status_code == 400
            data = response.get_json()
            assert 'errors' in data
            assert 'email' in data['errors']

    def test_update_without_authentication(self, client):
        """Test update requires authentication token."""
        response = client.patch('/api/users/me',
            json={'firstname': 'NewName'})

        assert response.status_code == 401
        data = response.get_json()
        assert data['error'] == 'Authentication required'

    def test_update_with_invalid_token(self, client):
        """Test update rejects invalid authentication token."""
        response = client.patch('/api/users/me',
            json={'firstname': 'NewName'},
            headers={'Authorization': 'Bearer invalid_token_string'})

        assert response.status_code == 401
        data = response.get_json()
        assert data['error'] == 'Invalid token'

    def test_update_with_expired_token(self, client, test_user):
        """Test update rejects expired authentication token."""
        import jwt
        import os
        from datetime import datetime, timedelta, timezone

        # Create expired token
        secret = os.getenv('JWT_SECRET_KEY', 'dummy-secret-key-for-development')
        payload = {
            'user_id': str(test_user.id),
            'email': test_user.email,
            'role': test_user.role.name,
            'exp': datetime.now(timezone.utc) - timedelta(hours=1),
            'iat': datetime.now(timezone.utc) - timedelta(hours=2)
        }
        expired_token = jwt.encode(payload, secret, algorithm='HS256')

        response = client.patch('/api/users/me',
            json={'firstname': 'NewName'},
            headers={'Authorization': f'Bearer {expired_token}'})

        assert response.status_code == 401
        data = response.get_json()
        assert data['error'] == 'Token expired'

    def test_update_response_contains_all_required_fields(self, client, auth_headers):
        """Test successful update response includes all expected fields."""
        response = client.patch('/api/users/me',
            json={'firstname': 'TestField'},
            headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()

        # Check top-level response structure
        assert 'message' in data
        assert 'user' in data

        # Check user object fields
        user_data = data['user']
        required_fields = ['id', 'firstname', 'lastname', 'email', 'role', 'created_at', 'updated_at']
        for field in required_fields:
            assert field in user_data, f"Missing required field: {field}"

        # Ensure sensitive fields are NOT included
        assert 'password' not in user_data
        assert 'password_hash' not in user_data

    def test_update_preserves_unchanged_fields(self, client, auth_headers, test_user):
        """Test updating one field doesn't modify other fields."""
        # Store original values
        original_lastname = test_user.lastname
        original_email = test_user.email
        original_role = test_user.role

        # Update only firstname
        response = client.patch('/api/users/me',
            json={'firstname': 'OnlyFirstChanged'},
            headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()

        # Verify only firstname changed
        assert data['user']['firstname'] == 'OnlyFirstChanged'
        assert data['user']['lastname'] == original_lastname
        assert data['user']['email'] == original_email
        assert data['user']['role'] == original_role.name

    def test_update_updates_timestamp(self, client, auth_headers, test_user):
        """Test that update modifies the updated_at timestamp."""
        import time

        # Get original updated_at
        original_updated_at = test_user.updated_at

        # Wait a moment and update
        time.sleep(0.1)

        response = client.patch('/api/users/me',
            json={'firstname': 'TimestampTest'},
            headers=auth_headers)

        assert response.status_code == 200

        # Refresh user from database
        db.session.refresh(test_user)

        # Verify updated_at changed
        assert test_user.updated_at > original_updated_at

    def test_update_can_keep_same_email(self, client, auth_headers, test_user):
        """Test user can update other fields while keeping the same email."""
        # Update firstname but keep same email
        response = client.patch('/api/users/me',
            json={
                'firstname': 'NewFirst',
                'email': test_user.email  # Same email
            },
            headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data['user']['firstname'] == 'NewFirst'
        assert data['user']['email'] == test_user.email

    def test_update_firstname_minimum_length(self, client, auth_headers):
        """Test firstname accepts minimum valid length."""
        response = client.patch('/api/users/me',
            json={'firstname': 'A'},
            headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data['user']['firstname'] == 'A'

    def test_update_password_minimum_length(self, client, auth_headers):
        """Test password accepts minimum valid length of 6 characters."""
        response = client.patch('/api/users/me',
            json={'password': '123456'},
            headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'Profile updated successfully'

    def test_update_with_special_characters_in_name(self, client, auth_headers):
        """Test update accepts names with special characters."""
        response = client.patch('/api/users/me',
            json={
                'firstname': "O'Brien",
                'lastname': 'Smith-Jones'
            },
            headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data['user']['firstname'] == "O'Brien"
        assert data['user']['lastname'] == 'Smith-Jones'

    def test_update_with_unicode_characters(self, client, auth_headers):
        """Test update accepts unicode characters in names."""
        response = client.patch('/api/users/me',
            json={
                'firstname': 'José',
                'lastname': 'Müller'
            },
            headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data['user']['firstname'] == 'José'
        assert data['user']['lastname'] == 'Müller'

