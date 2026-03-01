"""
Pytest configuration and shared fixtures for tests.
"""

import pytest
import os
from datetime import datetime, timedelta, timezone
import jwt
from app import create_app
from extensions import db
from models import User, Roles
from werkzeug.security import generate_password_hash
from services.user_service import UserService


@pytest.fixture(scope='session')
def app():
    """Create application for testing with in-memory SQLite database."""
    # Use SQLite in-memory database for tests (isolated, doesn't affect real DB)
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    os.environ['FLASK_ENV'] = 'testing'

    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    # Create all tables in the in-memory database
    with app.app_context():
        db.create_all()

    yield app

    # Clean up: drop all tables after all tests
    with app.app_context():
        db.session.remove()
        db.drop_all()



@pytest.fixture(scope='function')
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture(scope='function')
def test_user(app):
    """Create a test user for each test."""
    with app.app_context():
        user = User(
            firstname='Test',
            lastname='User',
            email='test@example.com',
            password_hash=generate_password_hash('password123'),
            role=Roles.user
        )
        db.session.add(user)
        db.session.commit()

        # Refresh to get the ID
        db.session.refresh(user)
        user_id = user.id

        yield user

        # Cleanup
        user = db.session.get(User, user_id)
        if user:
            db.session.delete(user)
            db.session.commit()


@pytest.fixture(scope='function')
def admin_user(app):
    """Create an admin user for each test."""
    with app.app_context():
        user = User(
            firstname='Admin',
            lastname='User',
            email='admin@test.com',
            password_hash=generate_password_hash('admin123'),
            role=Roles.admin
        )
        db.session.add(user)
        db.session.commit()

        db.session.refresh(user)
        user_id = user.id

        yield user

        # Cleanup
        user = db.session.get(User, user_id)
        if user:
            db.session.delete(user)
            db.session.commit()


@pytest.fixture(scope='function')
def auth_headers(app, test_user):
    """Generate authentication headers with valid token for regular user."""
    with app.app_context():
        token = UserService.generate_token(test_user)
        return {'Authorization': f'Bearer {token}'}


@pytest.fixture(scope='function')
def admin_headers(app, admin_user):
    """Generate authentication headers with valid token for admin user."""
    with app.app_context():
        token = UserService.generate_token(admin_user)
        return {'Authorization': f'Bearer {token}'}


@pytest.fixture(scope='function')
def expired_token(app, test_user):
    """Generate an expired JWT token."""
    with app.app_context():
        secret = os.getenv('JWT_SECRET_KEY', 'dummy-secret-key-for-development')
        payload = {
            'user_id': str(test_user.id),
            'email': test_user.email,
            'role': test_user.role.name,
            'exp': datetime.now(timezone.utc) - timedelta(hours=1),
            'iat': datetime.now(timezone.utc) - timedelta(hours=2)
        }
        return jwt.encode(payload, secret, algorithm='HS256')


@pytest.fixture(scope='function')
def multiple_users(app):
    """Create multiple users for pagination testing."""
    with app.app_context():
        users = []
        for i in range(5):
            user = User(
                firstname=f'User{i}',
                lastname=f'Test{i}',
                email=f'user{i}@test.com',
                password_hash=generate_password_hash('password123'),
                role=Roles.user
            )
            users.append(user)
            db.session.add(user)

        db.session.commit()

        # Get IDs
        user_ids = [u.id for u in users]

        yield users

        # Cleanup
        for user_id in user_ids:
            user = db.session.get(User, user_id)
            if user:
                db.session.delete(user)
        db.session.commit()


@pytest.fixture(scope='function')
def sample_flights(app):
    """Create sample flights for testing."""
    with app.app_context():
        from models import Flight, FlightStatus
        from decimal import Decimal
        from datetime import datetime

        flights = []

        # Create a few sample flights
        flight1 = Flight(
            flight_code='AA101',
            origin_airport='JFK - John F Kennedy International',
            destination_airport='LAX - Los Angeles International',
            departure_time=datetime(2026, 3, 15, 10, 0),
            arrival_time=datetime(2026, 3, 15, 14, 0),
            base_price=Decimal('299.99'),
            status=FlightStatus.active
        )

        flight2 = Flight(
            flight_code='UA202',
            origin_airport='ORD - O\'Hare International',
            destination_airport='SFO - San Francisco International',
            departure_time=datetime(2026, 3, 16, 12, 0),
            arrival_time=datetime(2026, 3, 16, 15, 30),
            base_price=Decimal('249.99'),
            status=FlightStatus.active
        )

        flights.extend([flight1, flight2])

        for flight in flights:
            db.session.add(flight)

        db.session.commit()

        # Get IDs
        flight_ids = [f.id for f in flights]

        yield flights

        # Cleanup
        for flight_id in flight_ids:
            flight = db.session.get(Flight, flight_id)
            if flight:
                db.session.delete(flight)
        db.session.commit()


@pytest.fixture(scope='function')
def multiple_flights(app):
    """Create multiple flights for pagination testing."""
    with app.app_context():
        from models import Flight, FlightStatus
        from decimal import Decimal
        from datetime import datetime, timedelta

        flights = []
        base_date = datetime(2026, 3, 15)

        for i in range(10):
            flight = Flight(
                flight_code=f'FL{i+100}',
                origin_airport=f'Airport_{i % 3}',
                destination_airport=f'Airport_{(i+1) % 3}',
                departure_time=base_date + timedelta(days=i),
                arrival_time=base_date + timedelta(days=i, hours=4),
                base_price=Decimal(f'{200 + i * 10}.99'),
                status=FlightStatus.active
            )
            flights.append(flight)
            db.session.add(flight)

        db.session.commit()

        # Get IDs
        flight_ids = [f.id for f in flights]

        yield flights

        # Cleanup
        for flight_id in flight_ids:
            flight = db.session.get(Flight, flight_id)
            if flight:
                db.session.delete(flight)
        db.session.commit()

