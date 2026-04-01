"""Additional tests for booking operations to improve coverage."""
import pytest
from decimal import Decimal
from datetime import datetime
from ticket_management_system.extensions import db
from ticket_management_system.models import Flight, FlightStatus, Booking, BookingStatus, User, Roles, Ticket
from ticket_management_system.resources.booking_service import BookingService
from ticket_management_system.exceptions import SeatUnavailableError, FlightNotFoundError
from werkzeug.security import generate_password_hash


class TestBookingServiceEdgeCases:
    """Test edge cases and error conditions in booking service."""

    @pytest.fixture
    def flight_with_limited_seats(self, app):
        """Create a flight with limited seats for testing."""
        with app.app_context():
            flight = Flight(
                flight_code='LIM_SEATS_001',
                origin_airport='JFK',
                destination_airport='LAX',
                departure_time=datetime(2026, 5, 15, 10, 0),
                arrival_time=datetime(2026, 5, 15, 14, 0),
                base_price=Decimal('299.99'),
                status=FlightStatus.active
            )
            db.session.add(flight)
            db.session.commit()
            yield flight

    @pytest.fixture
    def booking_user(self, app):
        """Create a user for bookings."""
        with app.app_context():
            user = User(
                firstname='Booking',
                lastname='User',
                email='booking@test.com',
                password_hash=generate_password_hash('password123'),
                role=Roles.user
            )
            db.session.add(user)
            db.session.commit()
            db.session.refresh(user)
            yield user

    def test_book_multiple_passengers_success(self, app, flight_with_limited_seats, booking_user):
        """Test booking multiple passengers on a flight."""
        with app.app_context():
            passengers = [
                {
                    'passenger_name': 'John Doe',
                    'passenger_passport_num': 'ABC123456',
                    'seat_num': '1A',
                    'seat_class': 'economy'
                },
                {
                    'passenger_name': 'Jane Doe',
                    'passenger_passport_num': 'DEF789012',
                    'seat_num': '1B',
                    'seat_class': 'economy'
                }
            ]

            booking, tickets = BookingService.book_tickets(
                user_id=booking_user.id,
                flight_id=flight_with_limited_seats.id,
                passengers=passengers
            )

            assert booking is not None
            assert len(tickets) == 2
            assert booking.booking_status == BookingStatus.booked

    def test_book_with_custom_booking_status(self, app, flight_with_limited_seats, booking_user):
        """Test booking with custom booking status."""
        with app.app_context():
            passengers = [
                {
                    'passenger_name': 'Test User',
                    'passenger_passport_num': 'GHI345678',
                    'seat_num': '2A',
                    'seat_class': 'business'
                }
            ]

            booking, tickets = BookingService.book_tickets(
                user_id=booking_user.id,
                flight_id=flight_with_limited_seats.id,
                passengers=passengers,
                booking_status='booked'
            )

            assert booking.booking_status == BookingStatus.booked

    def test_book_same_seat_twice_fails(self, app, flight_with_limited_seats, booking_user):
        """Test that booking the same seat twice raises error."""
        with app.app_context():
            passengers_1 = [
                {
                    'passenger_name': 'First User',
                    'passenger_passport_num': 'JKL901234',
                    'seat_num': '3A',
                    'seat_class': 'economy'
                }
            ]

            # First booking should succeed
            booking1, tickets1 = BookingService.book_tickets(
                user_id=booking_user.id,
                flight_id=flight_with_limited_seats.id,
                passengers=passengers_1
            )
            assert booking1 is not None

            # Second booking of same seat should fail
            passengers_2 = [
                {
                    'passenger_name': 'Second User',
                    'passenger_passport_num': 'MNO567890',
                    'seat_num': '3A',
                    'seat_class': 'economy'
                }
            ]

            with pytest.raises(SeatUnavailableError):
                BookingService.book_tickets(
                    user_id=booking_user.id,
                    flight_id=flight_with_limited_seats.id,
                    passengers=passengers_2
                )

    def test_get_paginated_bookings_specific_user(self, app, flight_with_limited_seats, booking_user):
        """Test getting bookings for specific user."""
        with app.app_context():
            # Create a booking through the service
            passengers = [
                {
                    'passenger_name': 'Test Passenger',
                    'passenger_passport_num': 'PQR234567',
                    'seat_num': '4A',
                    'seat_class': 'economy'
                }
            ]

            booking, tickets = BookingService.book_tickets(
                user_id=booking_user.id,
                flight_id=flight_with_limited_seats.id,
                passengers=passengers
            )

            # Get bookings for this specific user
            result = BookingService.get_paginated_bookings(
                user_id=booking_user.id,
                page=1,
                per_page=10
            )

            assert result['pagination']['total_items'] >= 1
            for booking_data in result['bookings']:
                assert 'id' in booking_data
                assert 'flight_id' in booking_data
                assert 'booking_status' in booking_data

    def test_get_booking_by_id(self, app, flight_with_limited_seats, booking_user):
        """Test retrieving booking by ID."""
        with app.app_context():
            # Create a booking through service
            passengers = [
                {
                    'passenger_name': 'Another Passenger',
                    'passenger_passport_num': 'STU890123',
                    'seat_num': '5A',
                    'seat_class': 'first'
                }
            ]

            booking, tickets = BookingService.book_tickets(
                user_id=booking_user.id,
                flight_id=flight_with_limited_seats.id,
                passengers=passengers
            )

            # Retrieve booking
            retrieved = BookingService.get_booking_by_id(booking.id)

            assert retrieved is not None
            assert retrieved.id == booking.id
            assert retrieved.user_id == booking_user.id

    def test_get_nonexistent_booking_by_id(self, app):
        """Test retrieving non-existent booking returns None."""
        with app.app_context():
            import uuid
            fake_id = uuid.uuid4()
            retrieved = BookingService.get_booking_by_id(fake_id)

            assert retrieved is None

    def test_cancel_booking_success(self, app, flight_with_limited_seats, booking_user):
        """Test successfully cancelling a booking."""
        with app.app_context():
            passengers = [
                {
                    'passenger_name': 'Cancel Passenger',
                    'passenger_passport_num': 'VWX456789',
                    'seat_num': '6A',
                    'seat_class': 'economy'
                }
            ]

            booking, tickets = BookingService.book_tickets(
                user_id=booking_user.id,
                flight_id=flight_with_limited_seats.id,
                passengers=passengers
            )

            # Cancel booking
            updated = BookingService.cancel_booking(booking.id)

            assert updated.booking_status == BookingStatus.cancelled




