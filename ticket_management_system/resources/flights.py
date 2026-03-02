from flasgger import swag_from
from flask import Blueprint, jsonify, request
from marshmallow import ValidationError

from ticket_management_system.exceptions import FlightAlreadyExistsError
from ticket_management_system.resources.flight_schemas import AddFlightSchema, FlightSearchSchema
from ticket_management_system.resources.flight_service import FlightService
from ticket_management_system.utils import admin_required, token_required

flight_bp = Blueprint("flights", __name__, url_prefix="/api/flights")


@flight_bp.route("/airports", methods=["GET"])
@token_required
@swag_from("../swagger_specs/airports_list.yml")
def get_airports(current_user):
    try:
        result = FlightService.get_available_airports()
        return jsonify(result), 200

    except Exception as exc:
        return jsonify({"error": "Internal Server Error", "message": str(exc)}), 500


@flight_bp.route("/search", methods=["GET"])
@token_required
@swag_from("../swagger_specs/flight_search.yml")
def search_flights(current_user):
    try:
        schema = FlightSearchSchema()
        validated_data = schema.load(request.args)

        origin_airport = validated_data.get("origin_airport")
        destination_airport = validated_data.get("destination_airport")
        departure_date = validated_data.get("departure_date")
        arrival_date = validated_data.get("arrival_date")
        page = validated_data.get("page", 1)
        per_page = validated_data.get("per_page", 10)

        departure_date_str = departure_date.strftime("%Y-%m-%d") if departure_date else None
        arrival_date_str = arrival_date.strftime("%Y-%m-%d") if arrival_date else None

        result = FlightService.search_flights(
            origin_airport=origin_airport,
            destination_airport=destination_airport,
            departure_date=departure_date_str,
            arrival_date=arrival_date_str,
            page=page,
            per_page=per_page,
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

    except Exception as exc:
        return jsonify({"error": "Internal Server Error", "message": str(exc)}), 500


@flight_bp.route("/", methods=["POST"])
@token_required
@admin_required
@swag_from("../swagger_specs/flight_add.yml")
def add_flight(current_user):
    try:
        schema = AddFlightSchema()
        validated_data = schema.load(request.get_json())

        new_flight = FlightService.create_flight(
            flight_code=validated_data["flight_code"],
            origin_airport=validated_data["origin_airport"],
            destination_airport=validated_data["destination_airport"],
            departure_time=validated_data["departure_time"],
            arrival_time=validated_data["arrival_time"],
            base_price=validated_data["base_price"],
        )

        response = FlightService.format_flight_detail(new_flight)
        response["message"] = "Flight created successfully"

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

    except FlightAlreadyExistsError as err:
        return jsonify({"error": "Conflict", "message": err.message}), 409

    except Exception as exc:
        from ticket_management_system.extensions import db

        db.session.rollback()
        return jsonify({"error": "Internal Server Error", "message": str(exc)}), 500
