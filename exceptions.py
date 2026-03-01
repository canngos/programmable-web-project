"""
Custom exceptions for the Flight Management System.
"""


class FlightAlreadyExistsError(Exception):
    """Exception raised when attempting to create a flight with a code that already exists."""

    def __init__(self, flight_code):
        self.flight_code = flight_code
        self.message = f'Flight with code {flight_code} already exists'
        super().__init__(self.message)


class FlightNotFoundError(Exception):
    """Exception raised when a flight cannot be found."""

    def __init__(self, flight_id):
        self.flight_id = flight_id
        self.message = f'Flight with ID {flight_id} not found'
        super().__init__(self.message)
