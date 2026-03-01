"""
Unit tests for booking route endpoints.
Tests create/list/detail/availability workflows.
"""

from datetime import datetime
from decimal import Decimal
from urllib.parse import quote

from extensions import db
from models import Flight, FlightStatus, Roles, User
from services.booking_service import BookingService
from services.user_service import UserService
from werkzeug.security import generate_password_hash


def _create_test_flight(code="RT101", status=FlightStatus.active, base_price=Decimal("300.00")):
    """Build a flight object for route tests."""
    return Flight(
        flight_code=code,
        origin_airport="JFK",
        destination_airport="LAX",
        departure_time=datetime(2026, 5, 1, 10, 0),
        arrival_time=datetime(2026, 5, 1, 14, 0),
        base_price=base_price,
        status=status
    )


class TestCreateBookingEndpoint:
    """Test POST /api/bookings/ endpoint."""

    def test_create_booking_success(self, client, app, auth_headers, sample_flights):
        """Create booking with one passenger."""
        with app.app_context():
            response = client.post(
                "/api/bookings/",
                headers=auth_headers,
                json={
                    "flight_id": str(sample_flights[0].id),
                    "passengers": [
                        {
                            "passenger_name": "John Doe",
                            "passenger_passport_num": "P12345678",
                            "seat_num": "12A",
                            "seat_class": "economy"
                        }
                    ]
                }
            )

            assert response.status_code == 201
            data = response.get_json()
            assert data["message"] == "Booking created successfully"
            assert "booking" in data
            assert data["booking"]["flight_id"] == str(sample_flights[0].id)
            assert len(data["booking"]["tickets"]) == 1

    def test_create_booking_invalid_payload(self, client, auth_headers):
        """Validation error for missing required fields."""
        response = client.post(
            "/api/bookings/",
            headers=auth_headers,
            json={"passengers": []}
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data["error"] == "Bad Request"
        assert "errors" in data

    def test_create_booking_flight_not_found(self, client, auth_headers):
        """Return 404 when target flight does not exist."""
        response = client.post(
            "/api/bookings/",
            headers=auth_headers,
            json={
                "flight_id": "fe4a1338-4b98-4b51-9f5c-1234567890ab",
                "passengers": [
                    {
                        "passenger_name": "John Doe",
                        "passenger_passport_num": "P12345678",
                        "seat_num": "12A",
                        "seat_class": "economy"
                    }
                ]
            }
        )

        assert response.status_code == 404
        data = response.get_json()
        assert data["error"] == "Not Found"

    def test_create_booking_seat_already_taken(self, client, app, auth_headers):
        """Return 409 when booking an already reserved seat."""
        with app.app_context():
            flight = _create_test_flight(code="RT102")
            db.session.add(flight)
            db.session.commit()

            first = client.post(
                "/api/bookings/",
                headers=auth_headers,
                json={
                    "flight_id": str(flight.id),
                    "passengers": [
                        {
                            "passenger_name": "Passenger One",
                            "passenger_passport_num": "P11111111",
                            "seat_num": "1A",
                            "seat_class": "economy"
                        }
                    ]
                }
            )
            assert first.status_code == 201

            second = client.post(
                "/api/bookings/",
                headers=auth_headers,
                json={
                    "flight_id": str(flight.id),
                    "passengers": [
                        {
                            "passenger_name": "Passenger Two",
                            "passenger_passport_num": "P22222222",
                            "seat_num": "1A",
                            "seat_class": "economy"
                        }
                    ]
                }
            )
            assert second.status_code == 409
            data = second.get_json()
            assert data["error"] == "Conflict"

            db.session.delete(flight)
            db.session.commit()

    def test_create_booking_requires_auth(self, client, sample_flights):
        """Protected endpoint should reject missing token."""
        response = client.post(
            "/api/bookings/",
            json={
                "flight_id": str(sample_flights[0].id),
                "passengers": [
                    {
                        "passenger_name": "John Doe",
                        "passenger_passport_num": "P12345678",
                        "seat_num": "12A",
                        "seat_class": "economy"
                    }
                ]
            }
        )

        assert response.status_code == 401
        data = response.get_json()
        assert data["error"] == "Authentication required"


class TestListBookingsEndpoint:
    """Test GET /api/bookings/ endpoint."""

    def test_list_bookings_returns_current_user_only(self, client, app, test_user, auth_headers):
        """Regular user should only see own bookings."""
        with app.app_context():
            flight1 = _create_test_flight(code="RT103")
            flight2 = _create_test_flight(code="RT104")
            db.session.add(flight1)
            db.session.add(flight2)
            db.session.commit()

            other_user = User(
                firstname="Other",
                lastname="User",
                email="other.user@test.com",
                password_hash=generate_password_hash("password123"),
                role=Roles.user
            )
            db.session.add(other_user)
            db.session.commit()
            db.session.refresh(other_user)

            BookingService.book_tickets(
                user_id=test_user.id,
                flight_id=flight1.id,
                passengers=[
                    {
                        "passenger_name": "Owner",
                        "passenger_passport_num": "P33333333",
                        "seat_num": "3A",
                        "seat_class": "economy"
                    }
                ]
            )
            BookingService.book_tickets(
                user_id=other_user.id,
                flight_id=flight2.id,
                passengers=[
                    {
                        "passenger_name": "Other User",
                        "passenger_passport_num": "P44444444",
                        "seat_num": "4A",
                        "seat_class": "economy"
                    }
                ]
            )

            response = client.get("/api/bookings/", headers=auth_headers)
            assert response.status_code == 200
            data = response.get_json()

            assert "bookings" in data
            assert "pagination" in data
            assert all(item["user_id"] == str(test_user.id) for item in data["bookings"])

            db.session.delete(other_user)
            db.session.delete(flight1)
            db.session.delete(flight2)
            db.session.commit()

    def test_list_bookings_admin_all_true_returns_all_users(self, client, app, admin_headers, test_user):
        """Admin can fetch all bookings with all=true."""
        with app.app_context():
            flight = _create_test_flight(code="RT105")
            db.session.add(flight)
            db.session.commit()

            BookingService.book_tickets(
                user_id=test_user.id,
                flight_id=flight.id,
                passengers=[
                    {
                        "passenger_name": "Admin Visible",
                        "passenger_passport_num": "P55555555",
                        "seat_num": "5A",
                        "seat_class": "economy"
                    }
                ]
            )

            response = client.get("/api/bookings/?all=true", headers=admin_headers)
            assert response.status_code == 200
            data = response.get_json()
            assert data["pagination"]["total_items"] >= 1

            db.session.delete(flight)
            db.session.commit()

    def test_list_bookings_invalid_pagination(self, client, auth_headers):
        """Invalid page/per_page should return marshmallow error."""
        response = client.get("/api/bookings/?page=0&per_page=0", headers=auth_headers)

        assert response.status_code == 400
        data = response.get_json()
        assert data["error"] == "Bad Request"
        assert "errors" in data


class TestGetBookingEndpoint:
    """Test GET /api/bookings/<booking_id> endpoint."""

    def test_get_booking_success_for_owner(self, client, app, test_user, auth_headers):
        """Owner should retrieve own booking."""
        with app.app_context():
            flight = _create_test_flight(code="RT106")
            db.session.add(flight)
            db.session.commit()

            booking, _ = BookingService.book_tickets(
                user_id=test_user.id,
                flight_id=flight.id,
                passengers=[
                    {
                        "passenger_name": "Owner",
                        "passenger_passport_num": "P66666666",
                        "seat_num": "6A",
                        "seat_class": "economy"
                    }
                ]
            )

            response = client.get(f"/api/bookings/{booking.id}", headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert "booking" in data
            assert data["booking"]["id"] == str(booking.id)

            db.session.delete(flight)
            db.session.commit()

    def test_get_booking_forbidden_for_non_owner(self, client, app, test_user):
        """Non-owner user should get 403."""
        with app.app_context():
            flight = _create_test_flight(code="RT107")
            db.session.add(flight)
            db.session.commit()

            owner = User(
                firstname="Booking",
                lastname="Owner",
                email="booking.owner@test.com",
                password_hash=generate_password_hash("password123"),
                role=Roles.user
            )
            db.session.add(owner)
            db.session.commit()
            db.session.refresh(owner)

            booking, _ = BookingService.book_tickets(
                user_id=owner.id,
                flight_id=flight.id,
                passengers=[
                    {
                        "passenger_name": "Owner",
                        "passenger_passport_num": "P77777777",
                        "seat_num": "7A",
                        "seat_class": "economy"
                    }
                ]
            )

            token = UserService.generate_token(test_user)
            headers = {"Authorization": f"Bearer {token}"}
            response = client.get(f"/api/bookings/{booking.id}", headers=headers)

            assert response.status_code == 403
            data = response.get_json()
            assert data["error"] == "Forbidden"

            db.session.delete(owner)
            db.session.delete(flight)
            db.session.commit()

    def test_get_booking_not_found(self, client, auth_headers):
        """Unknown booking id should return 404."""
        booking_id = "00000000-0000-0000-0000-000000000001"
        response = client.get(f"/api/bookings/{booking_id}", headers=auth_headers)

        assert response.status_code == 404
        data = response.get_json()
        assert data["error"] == "Not Found"


class TestSeatAvailabilityEndpoint:
    """Test GET /api/bookings/availability endpoint."""

    def test_seat_availability_true_then_false(self, client, app, auth_headers):
        """Availability should flip after ticket purchase."""
        with app.app_context():
            flight = _create_test_flight(code="RT108")
            db.session.add(flight)
            db.session.commit()

            available_response = client.get(
                f"/api/bookings/availability?flight_id={flight.id}&seat_num=9A",
                headers=auth_headers
            )
            assert available_response.status_code == 200
            assert available_response.get_json()["available"] is True

            create_response = client.post(
                "/api/bookings/",
                headers=auth_headers,
                json={
                    "flight_id": str(flight.id),
                    "passengers": [
                        {
                            "passenger_name": "Seat Owner",
                            "passenger_passport_num": "P88888888",
                            "seat_num": "9A",
                            "seat_class": "economy"
                        }
                    ]
                }
            )
            assert create_response.status_code == 201

            unavailable_response = client.get(
                f"/api/bookings/availability?flight_id={flight.id}&seat_num=9A",
                headers=auth_headers
            )
            assert unavailable_response.status_code == 200
            assert unavailable_response.get_json()["available"] is False

            db.session.delete(flight)
            db.session.commit()

    def test_seat_availability_validation_error(self, client, auth_headers):
        """Invalid seat length should fail schema validation."""
        seat_num = quote("ABCDE")
        response = client.get(
            f"/api/bookings/availability?flight_id=fe4a1338-4b98-4b51-9f5c-1234567890ab&seat_num={seat_num}",
            headers=auth_headers
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data["error"] == "Bad Request"
        assert "errors" in data

    def test_seat_availability_requires_auth(self, client, app):
        """Availability endpoint should require valid token."""
        with app.app_context():
            flight = _create_test_flight(code="RT109")
            db.session.add(flight)
            db.session.commit()

            response = client.get(f"/api/bookings/availability?flight_id={flight.id}&seat_num=1A")
            assert response.status_code == 401

            db.session.delete(flight)
            db.session.commit()
