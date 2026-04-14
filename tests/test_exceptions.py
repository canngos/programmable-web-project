"""Tests for custom exceptions."""
import pytest
from ticket_management_system.exceptions import (
    FlightAlreadyExistsError,
    FlightNotFoundError,
    InvalidCredentialsError,
    UserNotFoundError,
    TokenExpiredError,
    InvalidTokenError,
    EmailAlreadyExistsError,
    InvalidRoleError,
    SeatUnavailableError,
    BookingNotFoundError,
    BookingConflictError,
    FieldTooLongError,
    FieldTooShortError,
    FieldEmptyError
)


class TestFlightExceptions:
    """Test flight-related exceptions."""

    def test_flight_already_exists_error(self):
        """Test FlightAlreadyExistsError initialization."""
        error = FlightAlreadyExistsError('AA101')
        assert error.flight_code == 'AA101'
        assert error.message == 'Flight with code AA101 already exists'
        assert str(error) == 'Flight with code AA101 already exists'

    def test_flight_not_found_error(self):
        """Test FlightNotFoundError initialization."""
        flight_id = 'flight-123'
        error = FlightNotFoundError(flight_id)
        assert error.flight_id == flight_id
        assert error.message == f'Flight with ID {flight_id} not found'
        assert str(error) == f'Flight with ID {flight_id} not found'


class TestAuthenticationExceptions:
    """Test authentication-related exceptions."""

    def test_invalid_credentials_error(self):
        """Test InvalidCredentialsError initialization."""
        error = InvalidCredentialsError()
        assert error.message == 'Invalid email or password'
        assert str(error) == 'Invalid email or password'

    def test_user_not_found_error_no_identifier(self):
        """Test UserNotFoundError without identifier."""
        error = UserNotFoundError()
        assert error.message == 'User not found'
        assert str(error) == 'User not found'

    def test_user_not_found_error_with_identifier(self):
        """Test UserNotFoundError with identifier."""
        error = UserNotFoundError('user@example.com')
        assert error.message == 'User with identifier user@example.com not found'

    def test_token_expired_error(self):
        """Test TokenExpiredError initialization."""
        error = TokenExpiredError()
        assert error.message == 'Token expired'
        assert str(error) == 'Token expired'

    def test_invalid_token_error(self):
        """Test InvalidTokenError initialization."""
        error = InvalidTokenError()
        assert error.message == 'Invalid token'
        assert str(error) == 'Invalid token'

    def test_email_already_exists_error_without_email(self):
        """Test EmailAlreadyExistsError without email parameter."""
        error = EmailAlreadyExistsError()
        assert error.message == 'Email already in use by another user'

    def test_email_already_exists_error_with_email(self):
        """Test EmailAlreadyExistsError with email parameter."""
        error = EmailAlreadyExistsError('test@example.com')
        assert error.message == 'Email test@example.com already in use by another user'

    def test_invalid_role_error(self):
        """Test InvalidRoleError initialization."""
        error = InvalidRoleError('superuser')
        assert error.role == 'superuser'
        assert error.message == 'Invalid role "superuser". Must be "admin" or "user"'


class TestValidationExceptions:
    """Test validation-related exceptions."""

    def test_field_too_long_error(self):
        """Test FieldTooLongError initialization."""
        error = FieldTooLongError('firstname', 30)
        assert error.field_name == 'firstname'
        assert error.max_length == 30
        assert error.message == 'firstname must be 30 characters or less'
        assert str(error) == 'firstname must be 30 characters or less'

    def test_field_too_short_error(self):
        """Test FieldTooShortError initialization."""
        error = FieldTooShortError('password', 6)
        assert error.field_name == 'password'
        assert error.min_length == 6
        assert error.message == 'password must be at least 6 characters'
        assert str(error) == 'password must be at least 6 characters'

    def test_field_empty_error(self):
        """Test FieldEmptyError initialization."""
        error = FieldEmptyError('email')
        assert error.field_name == 'email'
        assert error.message == 'email cannot be empty'
        assert str(error) == 'email cannot be empty'


class TestBookingExceptions:
    """Test booking-related exceptions."""

    def test_seat_unavailable_error(self):
        """Test SeatUnavailableError initialization."""
        error = SeatUnavailableError('12A')
        assert error.seat_num == '12A'
        assert 'unavailable' in error.message.lower()

    def test_booking_not_found_error(self):
        """Test BookingNotFoundError initialization."""
        booking_id = 'booking-123'
        error = BookingNotFoundError(booking_id)
        assert error.booking_id == booking_id
        assert error.message == f'Booking with ID {booking_id} not found'

    def test_booking_conflict_error(self):
        """Test BookingConflictError initialization."""
        error = BookingConflictError("Booking is already cancelled")
        assert error.message == "Booking is already cancelled"
        assert str(error) == "Booking is already cancelled"


