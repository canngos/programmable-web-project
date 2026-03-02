# ==================== Flight Exceptions ====================

class FlightAlreadyExistsError(Exception):
    def __init__(self, flight_code):
        self.flight_code = flight_code
        self.message = f'Flight with code {flight_code} already exists'
        super().__init__(self.message)


class FlightNotFoundError(Exception):
    def __init__(self, flight_id):
        self.flight_id = flight_id
        self.message = f'Flight with ID {flight_id} not found'
        super().__init__(self.message)


# ==================== User/Authentication Exceptions ====================

class InvalidCredentialsError(Exception):
    def __init__(self):
        self.message = 'Invalid email or password'
        super().__init__(self.message)


class UserNotFoundError(Exception):
    def __init__(self, identifier=None):
        if identifier:
            self.message = f'User with identifier {identifier} not found'
        else:
            self.message = 'User not found'
        super().__init__(self.message)


class TokenExpiredError(Exception):
    def __init__(self):
        self.message = 'Token expired'
        super().__init__(self.message)


class InvalidTokenError(Exception):
    def __init__(self):
        self.message = 'Invalid token'
        super().__init__(self.message)


class EmailAlreadyExistsError(Exception):
    def __init__(self, email=None):
        if email:
            self.message = f'Email {email} already in use by another user'
        else:
            self.message = 'Email already in use by another user'
        super().__init__(self.message)


class InvalidRoleError(Exception):
    def __init__(self, role):
        self.role = role
        self.message = f'Invalid role "{role}". Must be "admin" or "user"'
        super().__init__(self.message)


# ==================== Validation Exceptions ====================

class ValidationError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class FieldTooLongError(ValidationError):
    def __init__(self, field_name, max_length):
        self.field_name = field_name
        self.max_length = max_length
        super().__init__(f'{field_name} must be {max_length} characters or less')


class FieldTooShortError(ValidationError):
    def __init__(self, field_name, min_length):
        self.field_name = field_name
        self.min_length = min_length
        super().__init__(f'{field_name} must be at least {min_length} characters')


class FieldEmptyError(ValidationError):
    def __init__(self, field_name):
        self.field_name = field_name
        super().__init__(f'{field_name} cannot be empty')


# ==================== Booking/Ticket Exceptions ====================

class SeatUnavailableError(Exception):
    def __init__(self, seat_num):
        self.seat_num = seat_num
        self.message = f'Seat with seat number {seat_num} is unavailable for purchase'
        super().__init__(self.message)