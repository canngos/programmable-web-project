"""
Unit tests for flight routes endpoints.
Tests all HTTP endpoints in the flight routes blueprint.
"""

import pytest
from datetime import datetime
from decimal import Decimal
from ticket_management_system.extensions import db
from ticket_management_system.models import Flight, FlightStatus


class TestAirportsEndpoint:
    """Test GET /api/flights/airports endpoint."""

    def test_get_airports_empty_database(self, client, app, auth_headers):
        """Test getting airports when no flights exist."""
        with app.app_context():
            response = client.get('/api/flights/airports', headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()

            assert 'airports' in data
            assert 'count' in data
            assert data['count'] == 0
            assert data['airports'] == []

    def test_get_airports_with_flights(self, client, app, sample_flights, auth_headers):
        """Test getting airports with flights in database."""
        with app.app_context():
            response = client.get('/api/flights/airports', headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()

            assert data['count'] > 0
            assert len(data['airports']) == data['count']
            assert isinstance(data['airports'], list)

    def test_get_airports_returns_json(self, client, app, sample_flights, auth_headers):
        """Test that response content type is JSON."""
        with app.app_context():
            response = client.get('/api/flights/airports', headers=auth_headers)

            assert response.content_type == 'application/json'

    def test_get_airports_distinct_values(self, client, app, auth_headers):
        """Test that airports list has no duplicates."""
        with app.app_context():
            # Create flights with duplicate airports
            flight1 = Flight(
                flight_code='AA101',
                origin_airport='JFK',
                destination_airport='LAX',
                departure_time=datetime(2026, 3, 15, 10, 0),
                arrival_time=datetime(2026, 3, 15, 14, 0),
                base_price=Decimal('299.99'),
                status=FlightStatus.active
            )
            flight2 = Flight(
                flight_code='AA102',
                origin_airport='JFK',
                destination_airport='LAX',
                departure_time=datetime(2026, 3, 16, 10, 0),
                arrival_time=datetime(2026, 3, 16, 14, 0),
                base_price=Decimal('299.99'),
                status=FlightStatus.active
            )
            db.session.add(flight1)
            db.session.add(flight2)
            db.session.commit()

            response = client.get('/api/flights/airports', headers=auth_headers)
            data = response.get_json()

            # Should only return unique airports
            airports_set = set(data['airports'])
            assert len(airports_set) == len(data['airports'])

            # Cleanup
            db.session.delete(flight1)
            db.session.delete(flight2)
            db.session.commit()

    def test_get_airports_sorted(self, client, app, auth_headers):
        """Test that airports are returned in sorted order."""
        with app.app_context():
            # Create flights with various airports
            flight1 = Flight(
                flight_code='AA101',
                origin_airport='ORD',
                destination_airport='ATL',
                departure_time=datetime(2026, 3, 15, 10, 0),
                arrival_time=datetime(2026, 3, 15, 14, 0),
                base_price=Decimal('199.99'),
                status=FlightStatus.active
            )
            db.session.add(flight1)
            db.session.commit()

            response = client.get('/api/flights/airports', headers=auth_headers)
            data = response.get_json()

            # Check if sorted
            assert data['airports'] == sorted(data['airports'])

            # Cleanup
            db.session.delete(flight1)
            db.session.commit()

    def test_get_airports_without_auth(self, client, app):
        """Test that endpoint requires authentication."""
        with app.app_context():
            response = client.get('/api/flights/airports')

            assert response.status_code == 401
            data = response.get_json()
            assert 'error' in data


class TestFlightSearchEndpoint:
    """Test GET /api/flights/search endpoint."""

    def test_search_flights_no_parameters(self, client, app, sample_flights, auth_headers):
        """Test search without any query parameters."""
        with app.app_context():
            response = client.get('/api/flights/search', headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()

            assert 'flights' in data
            assert 'pagination' in data
            assert isinstance(data['flights'], list)

    def test_search_flights_by_origin(self, client, app, auth_headers):
        """Test search by origin airport."""
        with app.app_context():
            flight = Flight(
                flight_code='AA101',
                origin_airport='JFK',
                destination_airport='LAX',
                departure_time=datetime(2026, 3, 15, 10, 0),
                arrival_time=datetime(2026, 3, 15, 14, 0),
                base_price=Decimal('299.99'),
                status=FlightStatus.active
            )
            db.session.add(flight)
            db.session.commit()

            response = client.get('/api/flights/search?origin_airport=JFK', headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()

            assert len(data['flights']) > 0
            for f in data['flights']:
                assert 'JFK' in f['origin_airport']

            # Cleanup
            db.session.delete(flight)
            db.session.commit()

    def test_search_flights_by_destination(self, client, app, auth_headers):
        """Test search by destination airport."""
        with app.app_context():
            flight = Flight(
                flight_code='AA101',
                origin_airport='JFK',
                destination_airport='LAX',
                departure_time=datetime(2026, 3, 15, 10, 0),
                arrival_time=datetime(2026, 3, 15, 14, 0),
                base_price=Decimal('299.99'),
                status=FlightStatus.active
            )
            db.session.add(flight)
            db.session.commit()

            response = client.get('/api/flights/search?destination_airport=LAX', headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()

            assert len(data['flights']) > 0
            for f in data['flights']:
                assert 'LAX' in f['destination_airport']

            # Cleanup
            db.session.delete(flight)
            db.session.commit()

    def test_search_flights_by_both_airports(self, client, app, auth_headers):
        """Test search by both origin and destination."""
        with app.app_context():
            flight = Flight(
                flight_code='AA101',
                origin_airport='JFK',
                destination_airport='LAX',
                departure_time=datetime(2026, 3, 15, 10, 0),
                arrival_time=datetime(2026, 3, 15, 14, 0),
                base_price=Decimal('299.99'),
                status=FlightStatus.active
            )
            db.session.add(flight)
            db.session.commit()

            response = client.get(
                '/api/flights/search?origin_airport=JFK&destination_airport=LAX',
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.get_json()

            assert len(data['flights']) > 0
            for f in data['flights']:
                assert 'JFK' in f['origin_airport']
                assert 'LAX' in f['destination_airport']

            # Cleanup
            db.session.delete(flight)
            db.session.commit()

    def test_search_flights_by_departure_date(self, client, app, auth_headers):
        """Test search by departure date."""
        with app.app_context():
            flight = Flight(
                flight_code='AA101',
                origin_airport='JFK',
                destination_airport='LAX',
                departure_time=datetime(2026, 3, 15, 10, 0),
                arrival_time=datetime(2026, 3, 15, 14, 0),
                base_price=Decimal('299.99'),
                status=FlightStatus.active
            )
            db.session.add(flight)
            db.session.commit()

            response = client.get('/api/flights/search?departure_date=2026-03-15', headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()

            # If flights found, check they're on the right date
            for f in data['flights']:
                departure = datetime.fromisoformat(f['departure_time'])
                assert departure.date().isoformat() == '2026-03-15'

            # Cleanup
            db.session.delete(flight)
            db.session.commit()

    def test_search_flights_by_arrival_date(self, client, app, auth_headers):
        """Test search by arrival date."""
        with app.app_context():
            flight = Flight(
                flight_code='AA101',
                origin_airport='JFK',
                destination_airport='LAX',
                departure_time=datetime(2026, 3, 15, 10, 0),
                arrival_time=datetime(2026, 3, 15, 14, 0),
                base_price=Decimal('299.99'),
                status=FlightStatus.active
            )
            db.session.add(flight)
            db.session.commit()

            response = client.get('/api/flights/search?arrival_date=2026-03-15', headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()

            # Cleanup
            db.session.delete(flight)
            db.session.commit()

    def test_search_flights_complex_query(self, client, app, auth_headers):
        """Test search with multiple filters."""
        with app.app_context():
            flight = Flight(
                flight_code='AA101',
                origin_airport='JFK',
                destination_airport='LAX',
                departure_time=datetime(2026, 3, 15, 10, 0),
                arrival_time=datetime(2026, 3, 15, 14, 0),
                base_price=Decimal('299.99'),
                status=FlightStatus.active
            )
            db.session.add(flight)
            db.session.commit()

            response = client.get(
                '/api/flights/search?'
                'origin_airport=JFK&'
                'destination_airport=LAX&'
                'departure_date=2026-03-15',
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.get_json()

            # Cleanup
            db.session.delete(flight)
            db.session.commit()

    def test_search_flights_with_pagination(self, client, app, multiple_flights, auth_headers):
        """Test search with pagination parameters."""
        with app.app_context():
            response = client.get('/api/flights/search?page=1&per_page=5', headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()

            assert data['pagination']['page'] == 1
            assert data['pagination']['per_page'] == 5
            assert len(data['flights']) <= 5

    def test_search_flights_second_page(self, client, app, multiple_flights, auth_headers):
        """Test getting second page of results."""
        with app.app_context():
            response = client.get('/api/flights/search?page=2&per_page=3', headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()

            assert data['pagination']['page'] == 2

    def test_search_flights_no_results(self, client, app, auth_headers):
        """Test search that returns no results."""
        with app.app_context():
            response = client.get('/api/flights/search?origin_airport=NONEXISTENT', headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()

            assert data['flights'] == []
            assert data['pagination']['total_items'] == 0

    def test_search_flights_invalid_date_format(self, client, app, sample_flights, auth_headers):
        """Test search with invalid date format."""
        with app.app_context():
            response = client.get('/api/flights/search?departure_date=invalid-date', headers=auth_headers)

            # Should return 400 Bad Request with Marshmallow error format
            assert response.status_code == 400
            data = response.get_json()
            assert 'error' in data
            assert 'Bad Request' in data['error']
            assert 'message' in data
            assert 'errors' in data  # Marshmallow returns errors dict
            assert 'departure_date' in data['errors']  # Field-specific error

    def test_search_flights_invalid_arrival_date_format(self, client, app, auth_headers):
        """Test search with invalid arrival date format."""
        with app.app_context():
            response = client.get('/api/flights/search?arrival_date=2026/02/08', headers=auth_headers)

            # Should return 400 Bad Request
            assert response.status_code == 400
            data = response.get_json()
            assert 'error' in data
            assert 'errors' in data
            assert 'arrival_date' in data['errors']

    def test_search_flights_valid_date_formats(self, client, app, auth_headers):
        """Test search with valid date formats."""
        with app.app_context():
            # All these should return 200 (even if no results)
            # Use future dates to pass Marshmallow validation
            response1 = client.get('/api/flights/search?departure_date=2026-12-15', headers=auth_headers)
            response2 = client.get('/api/flights/search?arrival_date=2026-12-31', headers=auth_headers)
            response3 = client.get('/api/flights/search?departure_date=2026-12-01&arrival_date=2026-12-01', headers=auth_headers)

            assert response1.status_code == 200
            assert response2.status_code == 200
            assert response3.status_code == 200

    def test_search_flights_partial_invalid_dates(self, client, app, auth_headers):
        """Test search with partially invalid dates."""
        with app.app_context():
            # Invalid month
            response1 = client.get('/api/flights/search?departure_date=2026-13-01', headers=auth_headers)
            assert response1.status_code == 400

            # Invalid day
            response2 = client.get('/api/flights/search?departure_date=2026-02-30', headers=auth_headers)
            assert response2.status_code == 400

            # Wrong format
            response3 = client.get('/api/flights/search?departure_date=08-02-2026', headers=auth_headers)
            assert response3.status_code == 400

    def test_search_flights_returns_json(self, client, app, sample_flights, auth_headers):
        """Test that response content type is JSON."""
        with app.app_context():
            response = client.get('/api/flights/search', headers=auth_headers)

            assert response.content_type == 'application/json'

    def test_search_flights_without_auth(self, client, app):
        """Test that endpoint requires authentication."""
        with app.app_context():
            response = client.get('/api/flights/search')

            assert response.status_code == 401
            data = response.get_json()
            assert 'error' in data


class TestFlightSearchPagination:
    """Test pagination functionality in search endpoint."""

    def test_search_default_pagination(self, client, app, sample_flights, auth_headers):
        """Test default pagination values."""
        with app.app_context():
            response = client.get('/api/flights/search', headers=auth_headers)
            data = response.get_json()

            pagination = data['pagination']
            assert pagination['page'] == 1
            assert pagination['per_page'] == 10

    def test_search_custom_page_size(self, client, app, multiple_flights, auth_headers):
        """Test custom page size."""
        with app.app_context():
            response = client.get('/api/flights/search?per_page=20', headers=auth_headers)
            data = response.get_json()

            assert data['pagination']['per_page'] == 20

    def test_search_pagination_metadata(self, client, app, multiple_flights, auth_headers):
        """Test pagination metadata presence."""
        with app.app_context():
            response = client.get('/api/flights/search', headers=auth_headers)
            data = response.get_json()

            pagination = data['pagination']
            assert 'page' in pagination
            assert 'per_page' in pagination
            assert 'total_pages' in pagination
            assert 'total_items' in pagination
            assert 'has_next' in pagination
            assert 'has_prev' in pagination
            assert 'next_page' in pagination
            assert 'prev_page' in pagination

    def test_search_first_page_no_prev(self, client, app, multiple_flights, auth_headers):
        """Test that first page has no previous page."""
        with app.app_context():
            response = client.get('/api/flights/search?page=1', headers=auth_headers)
            data = response.get_json()

            assert data['pagination']['has_prev'] is False
            assert data['pagination']['prev_page'] is None

    def test_search_navigation_links(self, client, app, multiple_flights, auth_headers):
        """Test pagination navigation links."""
        with app.app_context():
            response = client.get('/api/flights/search?page=2&per_page=3', headers=auth_headers)
            data = response.get_json()

            pagination = data['pagination']
            if pagination['has_prev']:
                assert pagination['prev_page'] == 1
            if pagination['has_next']:
                assert pagination['next_page'] == 3


class TestFlightSearchResponseFormat:
    """Test response format and structure."""

    def test_search_response_structure(self, client, app, sample_flights, auth_headers):
        """Test that response has correct structure."""
        with app.app_context():
            response = client.get('/api/flights/search', headers=auth_headers)
            data = response.get_json()

            # Top-level keys
            assert 'flights' in data
            assert 'pagination' in data

            # Flights array
            assert isinstance(data['flights'], list)

            if data['flights']:
                flight = data['flights'][0]
                # Flight object keys
                assert 'id' in flight
                assert 'flight_code' in flight
                assert 'origin_airport' in flight
                assert 'destination_airport' in flight
                assert 'departure_time' in flight
                assert 'arrival_time' in flight
                assert 'base_price' in flight
                assert 'status' in flight
                assert 'created_at' in flight

    def test_search_flight_data_types(self, client, app, auth_headers):
        """Test that flight data has correct types."""
        with app.app_context():
            flight = Flight(
                flight_code='AA101',
                origin_airport='JFK',
                destination_airport='LAX',
                departure_time=datetime(2026, 3, 15, 10, 0),
                arrival_time=datetime(2026, 3, 15, 14, 0),
                base_price=Decimal('299.99'),
                status=FlightStatus.active
            )
            db.session.add(flight)
            db.session.commit()

            response = client.get('/api/flights/search', headers=auth_headers)
            data = response.get_json()

            if data['flights']:
                f = data['flights'][0]
                assert isinstance(f['id'], str)
                assert isinstance(f['flight_code'], str)
                assert isinstance(f['origin_airport'], str)
                assert isinstance(f['destination_airport'], str)
                assert isinstance(f['departure_time'], str)
                assert isinstance(f['arrival_time'], str)
                assert isinstance(f['base_price'], str)
                assert isinstance(f['status'], str)

            # Cleanup
            db.session.delete(flight)
            db.session.commit()

    def test_search_pagination_structure(self, client, app, sample_flights, auth_headers):
        """Test pagination object structure."""
        with app.app_context():
            response = client.get('/api/flights/search', headers=auth_headers)
            data = response.get_json()

            pagination = data['pagination']
            assert isinstance(pagination['page'], int)
            assert isinstance(pagination['per_page'], int)
            assert isinstance(pagination['total_pages'], int)
            assert isinstance(pagination['total_items'], int)
            assert isinstance(pagination['has_next'], bool)
            assert isinstance(pagination['has_prev'], bool)


class TestFlightSearchEdgeCases:
    """Test edge cases and error scenarios."""

    def test_search_empty_database(self, client, app, auth_headers):
        """Test search when database is empty."""
        with app.app_context():
            response = client.get('/api/flights/search', headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()

            assert data['flights'] == []
            assert data['pagination']['total_items'] == 0

    def test_search_special_characters_in_query(self, client, app, auth_headers):
        """Test search with special characters."""
        with app.app_context():
            response = client.get('/api/flights/search?origin_airport=%20test%20', headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert 'flights' in data

    def test_search_very_long_query_string(self, client, app, auth_headers):
        """Test search with very long query string."""
        with app.app_context():
            long_string = 'A' * 1000
            response = client.get(f'/api/flights/search?origin_airport={long_string}', headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert data['flights'] == []

    def test_search_negative_page_number(self, client, app, sample_flights, auth_headers):
        """Test search with negative page number."""
        with app.app_context():
            response = client.get('/api/flights/search?page=-1', headers=auth_headers)

            # Marshmallow validates and rejects negative page numbers
            assert response.status_code == 400
            data = response.get_json()
            assert 'errors' in data
            assert 'page' in data['errors']

    def test_search_zero_per_page(self, client, app, sample_flights, auth_headers):
        """Test search with zero per_page."""
        with app.app_context():
            response = client.get('/api/flights/search?per_page=0', headers=auth_headers)

            # Marshmallow validates and rejects zero per_page
            assert response.status_code == 400
            data = response.get_json()
            assert 'errors' in data
            assert 'per_page' in data['errors']

    def test_search_excessive_per_page(self, client, app, sample_flights, auth_headers):
        """Test search with per_page exceeding maximum."""
        with app.app_context():
            response = client.get('/api/flights/search?per_page=500', headers=auth_headers)

            # Marshmallow validates and rejects excessive per_page
            assert response.status_code == 400
            data = response.get_json()
            assert 'errors' in data
            assert 'per_page' in data['errors']


class TestFlightRoutesIntegration:
    """Integration tests for flight routes."""

    def test_airports_then_search_workflow(self, client, app, auth_headers):
        """Test typical user workflow: get airports, then search."""
        with app.app_context():
            # Create a flight
            flight = Flight(
                flight_code='AA101',
                origin_airport='JFK',
                destination_airport='LAX',
                departure_time=datetime(2026, 3, 15, 10, 0),
                arrival_time=datetime(2026, 3, 15, 14, 0),
                base_price=Decimal('299.99'),
                status=FlightStatus.active
            )
            db.session.add(flight)
            db.session.commit()

            # Step 1: Get available airports
            airports_response = client.get('/api/flights/airports', headers=auth_headers)
            airports_data = airports_response.get_json()

            assert airports_response.status_code == 200
            assert len(airports_data['airports']) > 0

            # Step 2: Use one of the airports to search
            first_airport = airports_data['airports'][0]
            search_response = client.get(
                f'/api/flights/search?origin_airport={first_airport}',
                headers=auth_headers
            )
            search_data = search_response.get_json()

            assert search_response.status_code == 200
            assert 'flights' in search_data

            # Cleanup
            db.session.delete(flight)
            db.session.commit()
