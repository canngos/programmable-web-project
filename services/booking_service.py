"""
Booking service - Business logic for booking and ticket operations.
Handles booking creation and ticket purchase workflow.
"""

from decimal import Decimal, ROUND_HALF_UP

from extensions import db
from models import Booking, BookingStatus, Flight, FlightStatus, SeatClass, Ticket
from exceptions import FlightNotFoundError, SeatUnavailableError


class BookingService:
    """Service class for booking-related business logic."""

    BOOKABLE_STATUSES = {
        FlightStatus.active,
        FlightStatus.delayed,
        FlightStatus.started
    }

    PRICE_MULTIPLIERS = {
        SeatClass.economy: Decimal("1.0"),
        SeatClass.business: Decimal("2.5"),
        SeatClass.first: Decimal("4.0")
    }

    @staticmethod
    def get_booking_by_id(booking_id):
        """
        Get booking by ID.

        Args:
            booking_id: Booking UUID

        Returns:
            Booking: Booking object or None
        """
        return Booking.query.filter_by(id=booking_id).first()

    @staticmethod
    def get_paginated_bookings(user_id=None, page=1, per_page=10):
        """
        Get paginated bookings.

        Args:
            user_id: Optional user UUID filter. If None, returns all bookings.
            page: Page number
            per_page: Items per page

        Returns:
            dict: Paginated bookings with metadata
        """
        query = Booking.query
        if user_id is not None:
            query = query.filter(Booking.user_id == user_id)

        query = query.order_by(Booking.created_at.desc())

        if page < 1:
            page = 1
        if per_page < 1:
            per_page = 10
        if per_page > 100:
            per_page = 100

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        bookings_data = [BookingService.format_booking_summary(booking) for booking in pagination.items]

        return {
            "bookings": bookings_data,
            "pagination": {
                "page": pagination.page,
                "per_page": pagination.per_page,
                "total_pages": pagination.pages,
                "total_items": pagination.total,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev,
                "next_page": pagination.next_num if pagination.has_next else None,
                "prev_page": pagination.prev_num if pagination.has_prev else None
            }
        }

    @staticmethod
    def get_seat_availability(flight_id, seat_num):
        """
        Check if seat is available for a flight.

        Args:
            flight_id: Flight UUID
            seat_num: Seat number (e.g., 12A)

        Returns:
            bool: True if seat is available, False otherwise
        """
        normalized_seat = BookingService._normalize_seat_number(seat_num)
        # To simplify the project to keep the project in-scope,
        # additional details such as allowing booking tickets for same flight in
        # different dates have not been considered.
        existing_ticket = Ticket.query.filter_by(
            flight_id=flight_id,
            seat_num=normalized_seat
        ).first()
        return existing_ticket is None

    @staticmethod
    def calculate_ticket_price(base_price, seat_class):
        """
        Calculate ticket price based on seat class multiplier.

        Args:
            base_price: Flight base price
            seat_class: SeatClass enum

        Returns:
            Decimal: Calculated ticket price
        """
        multiplier = BookingService.PRICE_MULTIPLIERS[seat_class]
        price = Decimal(str(base_price)) * multiplier
        return price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def book_tickets(user_id, flight_id, passengers, booking_status=BookingStatus.booked):
        """
        Create a booking and corresponding tickets in a single transaction.

        Args:
            user_id: User UUID
            flight_id: Flight UUID
            passengers: List of passenger payloads
                [
                    {
                        "passenger_name": "John Doe",
                        "passenger_passport_num": "P12345678",
                        "seat_num": "12A",
                        "seat_class": "economy"
                    }
                ]
            booking_status: Booking status enum or string

        Returns:
            tuple: (Booking, list[Ticket]) - created booking and tickets

        Raises:
            FlightNotFoundError: If flight does not exist
            SeatUnavailableError: If a requested seat is already taken
            ValueError: If input payload is invalid
        """
        if not isinstance(passengers, list) or len(passengers) == 0:
            raise ValueError("passengers must be a non-empty list")

        flight = Flight.query.filter_by(id=flight_id).first()
        if not flight:
            raise FlightNotFoundError(flight_id)

        if flight.status not in BookingService.BOOKABLE_STATUSES:
            raise ValueError(
                f"Flight {flight.flight_code} is not bookable with status '{flight.status.name}'"
            )

        normalized_booking_status = BookingService._parse_booking_status(booking_status)
        requested_seats = set()
        created_tickets = []
        total_price = Decimal("0.00")

        try:
            booking = Booking(
                user_id=user_id,
                flight_id=flight.id,
                total_price=Decimal("0.00"),
                booking_status=normalized_booking_status
            )
            db.session.add(booking)
            db.session.flush()

            for passenger in passengers:
                ticket = BookingService._build_ticket(
                    booking_id=booking.id,
                    flight=flight,
                    passenger=passenger,
                    requested_seats=requested_seats
                )
                db.session.add(ticket)
                created_tickets.append(ticket)
                total_price += ticket.price

            booking.total_price = total_price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            db.session.commit()
            return booking, created_tickets

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def format_booking_detail(booking):
        """
        Format detailed booking data including ticket details.

        Args:
            booking: Booking object

        Returns:
            dict: Formatted booking payload
        """
        return {
            "booking": {
                "id": str(booking.id),
                "user_id": str(booking.user_id),
                "flight_id": str(booking.flight_id),
                "total_price": str(booking.total_price),
                "booking_status": booking.booking_status.name,
                "created_at": booking.created_at.isoformat(),
                "updated_at": booking.updated_at.isoformat(),
                "tickets": [
                    {
                        "id": str(ticket.id),
                        "passenger_name": ticket.passenger_name,
                        "passenger_passport_num": ticket.passenger_passport_num,
                        "seat_num": ticket.seat_num,
                        "seat_class": ticket.seat_class.name,
                        "price": str(ticket.price),
                        "created_at": ticket.created_at.isoformat()
                    }
                    for ticket in booking.tickets
                ]
            }
        }

    @staticmethod
    def format_booking_summary(booking):
        """
        Format compact booking data for list endpoints.

        Args:
            booking: Booking object

        Returns:
            dict: Summary booking payload
        """
        return {
            "id": str(booking.id),
            "user_id": str(booking.user_id),
            "flight_id": str(booking.flight_id),
            "total_price": str(booking.total_price),
            "booking_status": booking.booking_status.name,
            "ticket_count": len(booking.tickets),
            "created_at": booking.created_at.isoformat(),
            "updated_at": booking.updated_at.isoformat()
        }

    @staticmethod
    def _build_ticket(booking_id, flight, passenger, requested_seats):
        required_fields = ["passenger_name", "passenger_passport_num", "seat_num"]
        missing_fields = [
            field for field in required_fields
            if field not in passenger or passenger[field] in (None, "")
        ]
        if missing_fields:
            raise ValueError(f"Missing required passenger fields: {', '.join(missing_fields)}")

        seat_num = BookingService._normalize_seat_number(passenger["seat_num"])
        if seat_num in requested_seats:
            raise SeatUnavailableError(seat_num)
        requested_seats.add(seat_num)

        if not BookingService.get_seat_availability(flight.id, seat_num):
            raise SeatUnavailableError(seat_num)

        seat_class = BookingService._parse_seat_class(
            passenger.get("seat_class", SeatClass.economy)
        )

        price = BookingService.calculate_ticket_price(flight.base_price, seat_class)
        return Ticket(
            booking_id=booking_id,
            passenger_name=passenger["passenger_name"].strip(),
            passenger_passport_num=passenger["passenger_passport_num"].strip(),
            seat_num=seat_num,
            seat_class=seat_class,
            flight_id=flight.id,
            price=price
        )

    @staticmethod
    def _parse_seat_class(seat_class):
        if isinstance(seat_class, SeatClass):
            return seat_class
        if isinstance(seat_class, str):
            try:
                return SeatClass[seat_class.lower()]
            except KeyError:
                pass
        raise ValueError("Invalid seat_class. Must be one of: economy, business, first")

    @staticmethod
    def _parse_booking_status(booking_status):
        if isinstance(booking_status, BookingStatus):
            return booking_status
        if isinstance(booking_status, str):
            try:
                return BookingStatus[booking_status.lower()]
            except KeyError:
                pass
        raise ValueError("Invalid booking_status")

    @staticmethod
    def _normalize_seat_number(seat_num):
        if not isinstance(seat_num, str) or not seat_num.strip():
            raise ValueError("seat_num must be a non-empty string")
        return seat_num.strip().upper()
