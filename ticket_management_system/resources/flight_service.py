"""Business logic for flight operations."""
from datetime import datetime, timedelta
from ticket_management_system.extensions import db
from ticket_management_system.models import Flight, FlightStatus
from ticket_management_system.exceptions import FlightAlreadyExistsError
from ticket_management_system.utils import format_pagination_response


class FlightService:
    """Service class for flight operations."""
    @staticmethod
    def get_available_airports():
        """Get list of available airports."""
        # Get all distinct origin airports
        origins = db.session.query(Flight.origin_airport).distinct().all()

        # Get all distinct destination airports
        destinations = db.session.query(Flight.destination_airport).distinct().all()

        # Combine and deduplicate
        airports = set()
        for (airport,) in origins:
            airports.add(airport)
        for (airport,) in destinations:
            airports.add(airport)

        # Convert to sorted list
        airport_list = sorted(list(airports))

        return {
            'airports': airport_list,
            'count': len(airport_list)
        }

    @staticmethod
    def search_flights(  # pylint: disable=too-many-positional-arguments,too-many-arguments
            origin_airport=None, destination_airport=None,
            departure_date=None, arrival_date=None,
            page=1, per_page=10):
        """Search flights with filters."""
        # Start with base query - only active flights
        query = Flight.query.filter(Flight.status == FlightStatus.active)

        # Apply filters if provided
        if origin_airport:
            query = query.filter(Flight.origin_airport.ilike(f'%{origin_airport}%'))

        if destination_airport:
            query = query.filter(Flight.destination_airport.ilike(f'%{destination_airport}%'))

        if departure_date:
            try:
                # Parse date and filter for flights on that day
                # Use date range to handle timestamps properly (00:00:00 to 23:59:59)
                date_obj = datetime.strptime(departure_date, '%Y-%m-%d')
                next_day = date_obj + timedelta(days=1)
                query = query.filter(
                    Flight.departure_time >= date_obj,
                    Flight.departure_time < next_day
                )
            except ValueError:
                pass  # Invalid date format, skip filter

        if arrival_date:
            try:
                # Parse date and filter for flights on that day
                # Use date range to handle timestamps properly (00:00:00 to 23:59:59)
                date_obj = datetime.strptime(arrival_date, '%Y-%m-%d')
                next_day = date_obj + timedelta(days=1)
                query = query.filter(
                    Flight.arrival_time >= date_obj,
                    Flight.arrival_time < next_day
                )
            except ValueError:
                pass  # Invalid date format, skip filter

        # Order by departure time
        query = query.order_by(Flight.departure_time.asc())

        # Validate pagination parameters
        page = max(page, 1)
        per_page = max(per_page, 1)
        per_page = min(per_page, 100)

        # Execute paginated query
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        # Format results
        flights_data = [FlightService.format_flight_detail(flight) for flight in pagination.items]

        return format_pagination_response('flights', flights_data, pagination)

    @staticmethod
    def get_flight_by_id(flight_id):
        """Get flight by ID."""
        return Flight.query.filter_by(id=flight_id).first()

    @staticmethod
    def format_flight_detail(flight):
        """Format flight details for response."""
        return {
            'flight': {
                'id': str(flight.id),
                'flight_code': flight.flight_code,
                'origin_airport': flight.origin_airport,
                'destination_airport': flight.destination_airport,
                'departure_time': flight.departure_time.isoformat(),
                'arrival_time': flight.arrival_time.isoformat(),
                'base_price': str(flight.base_price),
                'status': flight.status.name,
                'created_at': flight.created_at.isoformat(),
                'updated_at': flight.updated_at.isoformat()
            }
        }

    @staticmethod
    def create_flight(  # pylint: disable=too-many-positional-arguments,too-many-arguments
            flight_code, origin_airport, destination_airport,
            departure_time, arrival_time, base_price):
        """Create a new flight."""
        # Check if flight code already exists
        existing_flight = Flight.query.filter_by(flight_code=flight_code.upper()).first()
        if existing_flight:
            raise FlightAlreadyExistsError(flight_code.upper())

        # Create new flight with active status
        new_flight = Flight(
            flight_code=flight_code.upper(),  # Standardize to uppercase
            origin_airport=origin_airport,
            destination_airport=destination_airport,
            departure_time=departure_time,
            arrival_time=arrival_time,
            base_price=base_price,
            status=FlightStatus.active
        )

        db.session.add(new_flight)
        db.session.commit()

        return new_flight

    @staticmethod
    def delete_flight(flight_id):
        """Delete a flight by ID."""
        from ticket_management_system.exceptions import FlightNotFoundError

        flight = Flight.query.filter_by(id=flight_id).first()

        if not flight:
            raise FlightNotFoundError(flight_id)

        db.session.delete(flight)
        db.session.commit()
