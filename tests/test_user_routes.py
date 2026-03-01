"""
Unit tests for user routes endpoints.
Tests all HTTP endpoints in the user routes blueprint.
"""

from models import User, Roles
from services.user_service import UserService
from extensions import db


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
        assert 'Missing required fields' in data['message']

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
        assert 'firstname must be 30 characters or less' in data['message']

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
        assert 'password must be at least 6 characters' in data['message']

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
        assert 'Invalid role' in data['message']


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
