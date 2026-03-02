from datetime import datetime, timedelta

from ticket_management_system.exceptions import FlightAlreadyExistsError
from ticket_management_system.extensions import db
from ticket_management_system.models import Flight, FlightStatus


class FlightService:
    @staticmethod
    def get_available_airports():
        origins = db.session.query(Flight.origin_airport).distinct().all()
        destinations = db.session.query(Flight.destination_airport).distinct().all()

        airports = set()
        for (airport,) in origins:
            airports.add(airport)
        for (airport,) in destinations:
            airports.add(airport)

        airport_list = sorted(list(airports))

        return {"airports": airport_list, "count": len(airport_list)}

    @staticmethod
    def search_flights(
        origin_airport=None,
        destination_airport=None,
        departure_date=None,
        arrival_date=None,
        page=1,
        per_page=10,
    ):
        query = Flight.query.filter(Flight.status == FlightStatus.active)

        if origin_airport:
            query = query.filter(Flight.origin_airport.ilike(f"%{origin_airport}%"))

        if destination_airport:
            query = query.filter(Flight.destination_airport.ilike(f"%{destination_airport}%"))

        if departure_date:
            try:
                date_obj = datetime.strptime(departure_date, "%Y-%m-%d")
                next_day = date_obj + timedelta(days=1)
                query = query.filter(
                    Flight.departure_time >= date_obj,
                    Flight.departure_time < next_day,
                )
            except ValueError:
                pass

        if arrival_date:
            try:
                date_obj = datetime.strptime(arrival_date, "%Y-%m-%d")
                next_day = date_obj + timedelta(days=1)
                query = query.filter(
                    Flight.arrival_time >= date_obj,
                    Flight.arrival_time < next_day,
                )
            except ValueError:
                pass

        query = query.order_by(Flight.departure_time.asc())

        if page < 1:
            page = 1
        if per_page < 1:
            per_page = 10
        if per_page > 100:
            per_page = 100

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        flights_data = [
            {
                "id": str(flight.id),
                "flight_code": flight.flight_code,
                "origin_airport": flight.origin_airport,
                "destination_airport": flight.destination_airport,
                "departure_time": flight.departure_time.isoformat(),
                "arrival_time": flight.arrival_time.isoformat(),
                "base_price": str(flight.base_price),
                "status": flight.status.name,
                "created_at": flight.created_at.isoformat(),
            }
            for flight in pagination.items
        ]

        return {
            "flights": flights_data,
            "pagination": {
                "page": pagination.page,
                "per_page": pagination.per_page,
                "total_pages": pagination.pages,
                "total_items": pagination.total,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev,
                "next_page": pagination.next_num if pagination.has_next else None,
                "prev_page": pagination.prev_num if pagination.has_prev else None,
            },
        }

    @staticmethod
    def get_flight_by_id(flight_id):
        return Flight.query.filter_by(id=flight_id).first()

    @staticmethod
    def format_flight_detail(flight):
        return {
            "flight": {
                "id": str(flight.id),
                "flight_code": flight.flight_code,
                "origin_airport": flight.origin_airport,
                "destination_airport": flight.destination_airport,
                "departure_time": flight.departure_time.isoformat(),
                "arrival_time": flight.arrival_time.isoformat(),
                "base_price": str(flight.base_price),
                "status": flight.status.name,
                "created_at": flight.created_at.isoformat(),
                "updated_at": flight.updated_at.isoformat(),
            }
        }

    @staticmethod
    def create_flight(
        flight_code,
        origin_airport,
        destination_airport,
        departure_time,
        arrival_time,
        base_price,
    ):
        existing_flight = Flight.query.filter_by(flight_code=flight_code.upper()).first()
        if existing_flight:
            raise FlightAlreadyExistsError(flight_code.upper())

        new_flight = Flight(
            flight_code=flight_code.upper(),
            origin_airport=origin_airport,
            destination_airport=destination_airport,
            departure_time=departure_time,
            arrival_time=arrival_time,
            base_price=base_price,
            status=FlightStatus.active,
        )

        db.session.add(new_flight)
        db.session.commit()

        return new_flight
