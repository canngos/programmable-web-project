from decimal import Decimal, ROUND_HALF_UP

from ticket_management_system.extensions import db
from ticket_management_system.models import Booking, BookingStatus, Flight, FlightStatus, SeatClass, Ticket
from ticket_management_system.exceptions import FlightNotFoundError, SeatUnavailableError


class BookingService:
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
        return Booking.query.filter_by(id=booking_id).first()

    @staticmethod
    def get_paginated_bookings(user_id=None, page=1, per_page=10):
        query = Booking.query
        if user_id is not None:
            query = query.filter(Booking.user_id == user_id)

        query = query.order_by(Booking.created_at.desc())

        page = max(page, 1)
        per_page = max(per_page, 1)
        per_page = min(per_page, 100)

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
        normalized_seat = BookingService._normalize_seat_number(seat_num)
        existing_ticket = Ticket.query.filter_by(
            flight_id=flight_id,
            seat_num=normalized_seat
        ).first()
        return existing_ticket is None

    @staticmethod
    def calculate_ticket_price(base_price, seat_class):
        multiplier = BookingService.PRICE_MULTIPLIERS[seat_class]
        price = Decimal(str(base_price)) * multiplier
        return price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def book_tickets(user_id, flight_id, passengers, booking_status=BookingStatus.booked):
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

    @staticmethod
    def update_booking(booking_id, booking_status=None):
        if booking_status is None:
            raise ValueError("booking_status is required")

        booking = Booking.query.filter_by(id=booking_id).first()
        if not booking:
            return None

        # Don't allow updating cancelled or refunded bookings
        if booking.booking_status in (BookingStatus.cancelled, BookingStatus.refunded):
            raise ValueError(f"Cannot update booking with status '{booking.booking_status.name}'")

        normalized_status = BookingService._parse_booking_status(booking_status)
        booking.booking_status = normalized_status

        from datetime import datetime, timezone
        booking.updated_at = datetime.now(timezone.utc)

        db.session.commit()
        return booking

    @staticmethod
    def cancel_booking(booking_id):
        booking = Booking.query.filter_by(id=booking_id).first()
        if not booking:
            return None

        # Check if already cancelled or refunded
        if booking.booking_status == BookingStatus.cancelled:
            raise ValueError("Booking is already cancelled")
        if booking.booking_status == BookingStatus.refunded:
            raise ValueError("Cannot cancel a refunded booking")

        booking.booking_status = BookingStatus.cancelled

        from datetime import datetime, timezone
        booking.updated_at = datetime.now(timezone.utc)

        db.session.commit()
        return booking

