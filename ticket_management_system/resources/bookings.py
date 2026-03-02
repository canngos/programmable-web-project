from flask import Blueprint, jsonify, request
from marshmallow import ValidationError

from ticket_management_system.exceptions import FlightNotFoundError, SeatUnavailableError
from ticket_management_system.models import Roles
from ticket_management_system.resources.booking_schemas import (
    BookTicketsSchema,
    PaginationQuerySchema,
    SeatAvailabilityQuerySchema,
)
from ticket_management_system.resources.booking_service import BookingService
from ticket_management_system.utils import token_required

booking_bp = Blueprint("bookings", __name__, url_prefix="/api/bookings")


@booking_bp.route("/", methods=["POST"])
@token_required
def create_booking(current_user):
    try:
        schema = BookTicketsSchema()
        data = schema.load(request.get_json())

        booking, _tickets = BookingService.book_tickets(
            user_id=current_user.id,
            flight_id=data["flight_id"],
            passengers=data["passengers"],
            booking_status=data.get("booking_status", "booked"),
        )

        response = BookingService.format_booking_detail(booking)
        response["message"] = "Booking created successfully"
        return jsonify(response), 201

    except ValidationError as err:
        return (
            jsonify(
                {
                    "error": "Bad Request",
                    "message": "Validation failed",
                    "errors": err.messages,
                }
            ),
            400,
        )
    except FlightNotFoundError as err:
        return jsonify({"error": "Not Found", "message": err.message}), 404
    except SeatUnavailableError as err:
        return jsonify({"error": "Conflict", "message": err.message}), 409
    except ValueError as err:
        return jsonify({"error": "Bad Request", "message": str(err)}), 400
    except Exception as err:
        from ticket_management_system.extensions import db

        db.session.rollback()
        return jsonify({"error": "Internal Server Error", "message": str(err)}), 500


@booking_bp.route("/", methods=["GET"])
@token_required
def list_bookings(current_user):
    try:
        query_schema = PaginationQuerySchema()
        query_data = query_schema.load(request.args)

        include_all = request.args.get("all", "false").lower() == "true"
        user_filter = None if (current_user.role == Roles.admin and include_all) else current_user.id

        result = BookingService.get_paginated_bookings(
            user_id=user_filter,
            page=query_data.get("page", 1),
            per_page=query_data.get("per_page", 10),
        )
        return jsonify(result), 200

    except ValidationError as err:
        return (
            jsonify(
                {
                    "error": "Bad Request",
                    "message": "Validation failed",
                    "errors": err.messages,
                }
            ),
            400,
        )
    except Exception as err:
        return jsonify({"error": "Internal Server Error", "message": str(err)}), 500


@booking_bp.route("/<uuid:booking_id>", methods=["GET"])
@token_required
def get_booking(current_user, booking_id):
    booking = BookingService.get_booking_by_id(booking_id)
    if not booking:
        return (
            jsonify(
                {
                    "error": "Not Found",
                    "message": f"Booking with ID {booking_id} not found",
                }
            ),
            404,
        )

    if current_user.role != Roles.admin and booking.user_id != current_user.id:
        return (
            jsonify(
                {
                    "error": "Forbidden",
                    "message": "You are not allowed to access this booking",
                }
            ),
            403,
        )

    return jsonify(BookingService.format_booking_detail(booking)), 200


@booking_bp.route("/availability", methods=["GET"])
@token_required
def get_seat_availability(current_user):
    try:
        schema = SeatAvailabilityQuerySchema()
        data = schema.load(request.args)
        seat_num = data["seat_num"]
        available = BookingService.get_seat_availability(
            flight_id=data["flight_id"],
            seat_num=seat_num,
        )
        return (
            jsonify(
                {
                    "flight_id": str(data["flight_id"]),
                    "seat_num": seat_num.strip().upper(),
                    "available": available,
                }
            ),
            200,
        )

    except ValidationError as err:
        return (
            jsonify(
                {
                    "error": "Bad Request",
                    "message": "Validation failed",
                    "errors": err.messages,
                }
            ),
            400,
        )
    except ValueError as err:
        return jsonify({"error": "Bad Request", "message": str(err)}), 400
    except Exception as err:
        return jsonify({"error": "Internal Server Error", "message": str(err)}), 500
