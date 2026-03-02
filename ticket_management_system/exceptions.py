class FlightAlreadyExistsError(Exception):
    def __init__(self, flight_code):
        self.flight_code = flight_code
        self.message = f"Flight with code {flight_code} already exists"
        super().__init__(self.message)


class FlightNotFoundError(Exception):
    def __init__(self, flight_id):
        self.flight_id = flight_id
        self.message = f"Flight with ID {flight_id} not found"
        super().__init__(self.message)


class SeatUnavailableError(Exception):
    def __init__(self, seat_num):
        self.seat_num = seat_num
        self.message = f"Seat with seat number {seat_num} is unvailable for purchase."
        super().__init__(self.message)

