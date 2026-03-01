"""
Flight routes for the Flight Management System API.
Provides endpoints for flight search and management.
"""

from flask import Blueprint, request, jsonify
from flasgger import swag_from
from marshmallow import ValidationError

from routes.user_routes import token_required, admin_required
from schemas.flight_schemas import FlightSearchSchema, AddFlightSchema
from services.flight_service import FlightService
from exceptions import FlightAlreadyExistsError

flight_bp = Blueprint('flights', __name__, url_prefix='/api/flights')


@flight_bp.route('/airports', methods=['GET'])
@token_required
@swag_from('../swagger_specs/airports_list.yml')
def get_airports(current_user):
    """
    Get list of all available airports in the system.
    Returns distinct airport names from both origin and destination airports.
    Requires authentication.
    """
    try:
        result = FlightService.get_available_airports()
        return jsonify(result), 200

    except Exception as e:
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e)
        }), 500


@flight_bp.route('/search', methods=['GET'])
@token_required
@swag_from('../swagger_specs/flight_search.yml')
def search_flights(current_user):
    """
    Search for flights with optional filters.
    Uses Marshmallow for automatic query parameter validation.

    Query parameters:
        - origin_airport: Filter by origin airport (partial match)
        - destination_airport: Filter by destination airport (partial match)
        - departure_date: Filter by departure date (YYYY-MM-DD)
        - arrival_date: Filter by arrival date (YYYY-MM-DD)
        - page: Page number (default: 1)
        - per_page: Items per page (default: 10, max: 100)
    """
    try:
        # Validate query parameters using Marshmallow schema
        schema = FlightSearchSchema()
        validated_data = schema.load(request.args)

        # Extract validated parameters
        origin_airport = validated_data.get('origin_airport')
        destination_airport = validated_data.get('destination_airport')
        departure_date = validated_data.get('departure_date')
        arrival_date = validated_data.get('arrival_date')
        page = validated_data.get('page', 1)
        per_page = validated_data.get('per_page', 10)

        # Convert date objects to strings for service layer
        departure_date_str = departure_date.strftime('%Y-%m-%d') if departure_date else None
        arrival_date_str = arrival_date.strftime('%Y-%m-%d') if arrival_date else None

        # Search flights using service
        result = FlightService.search_flights(
            origin_airport=origin_airport,
            destination_airport=destination_airport,
            departure_date=departure_date_str,
            arrival_date=arrival_date_str,
            page=page,
            per_page=per_page
        )

        return jsonify(result), 200

    except ValidationError as err:
        # Return validation errors with 400 status
        return jsonify({
            'error': 'Bad Request',
            'message': 'Validation failed',
            'errors': err.messages
        }), 400

    except Exception as e:
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e)
        }), 500


@flight_bp.route('/', methods=['POST'])
@token_required
@admin_required
@swag_from('../swagger_specs/flight_add.yml')
def add_flight(current_user):
    """
    Create a new flight (Admin only).
    Requires JWT authentication and admin role.
    Creates flight with active status.
    """
    try:
        # Get and validate request body using Marshmallow schema
        schema = AddFlightSchema()
        validated_data = schema.load(request.get_json())

        # Create flight using service
        new_flight = FlightService.create_flight(
            flight_code=validated_data['flight_code'],
            origin_airport=validated_data['origin_airport'],
            destination_airport=validated_data['destination_airport'],
            departure_time=validated_data['departure_time'],
            arrival_time=validated_data['arrival_time'],
            base_price=validated_data['base_price']
        )

        # Format response
        response = FlightService.format_flight_detail(new_flight)
        response['message'] = 'Flight created successfully'

        return jsonify(response), 201

    except ValidationError as err:
        # Return validation errors with 400 status
        return jsonify({
            'error': 'Bad Request',
            'message': 'Validation failed',
            'errors': err.messages
        }), 400

    except FlightAlreadyExistsError as err:
        # Handle duplicate flight code
        return jsonify({
            'error': 'Conflict',
            'message': err.message
        }), 409

    except Exception as e:
        from extensions import db
        db.session.rollback()
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e)
        }), 500

