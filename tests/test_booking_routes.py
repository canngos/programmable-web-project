"""
Unit tests for booking route endpoints.
Tests create/list/detail/availability workflows.
"""

from datetime import datetime
from decimal import Decimal
from urllib.parse import quote

from ticket_management_system.extensions import db
from ticket_management_system.models import Flight, FlightStatus, Roles, User
from ticket_management_system.resources.booking_service import BookingService
from ticket_management_system.resources.user_service import UserService
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


class TestUpdateBookingEndpoint:
    """Test PUT /api/bookings/<booking_id> endpoint."""

    def test_update_booking_success_by_owner(self, client, app, test_user, auth_headers):
        """Owner can successfully update their booking status."""
        with app.app_context():
            flight = _create_test_flight(code="RT110")
            db.session.add(flight)
            db.session.commit()

            booking, _ = BookingService.book_tickets(
                user_id=test_user.id,
                flight_id=flight.id,
                passengers=[
                    {
                        "passenger_name": "Test Passenger",
                        "passenger_passport_num": "P99999999",
                        "seat_num": "10A",
                        "seat_class": "economy"
                    }
                ]
            )

            response = client.put(
                f"/api/bookings/{booking.id}",
                headers=auth_headers,
                json={"booking_status": "paid"}
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data["message"] == "Booking updated successfully"
            assert data["booking"]["booking_status"] == "paid"
            assert data["booking"]["id"] == str(booking.id)

            db.session.delete(flight)
            db.session.commit()

    def test_update_booking_booked_to_cancelled(self, client, app, test_user, auth_headers):
        """Update booking from booked to cancelled."""
        with app.app_context():
            flight = _create_test_flight(code="RT111")
            db.session.add(flight)
            db.session.commit()

            booking, _ = BookingService.book_tickets(
                user_id=test_user.id,
                flight_id=flight.id,
                passengers=[
                    {
                        "passenger_name": "Test Passenger",
                        "passenger_passport_num": "P10101010",
                        "seat_num": "11A",
                        "seat_class": "economy"
                    }
                ]
            )

            response = client.put(
                f"/api/bookings/{booking.id}",
                headers=auth_headers,
                json={"booking_status": "cancelled"}
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data["booking"]["booking_status"] == "cancelled"

            db.session.delete(flight)
            db.session.commit()

    def test_update_booking_paid_to_refunded(self, client, app, test_user, auth_headers):
        """Update booking from paid to refunded."""
        with app.app_context():
            flight = _create_test_flight(code="RT112")
            db.session.add(flight)
            db.session.commit()

            booking, _ = BookingService.book_tickets(
                user_id=test_user.id,
                flight_id=flight.id,
                passengers=[
                    {
                        "passenger_name": "Test Passenger",
                        "passenger_passport_num": "P11111112",
                        "seat_num": "12A",
                        "seat_class": "economy"
                    }
                ],
                booking_status="paid"
            )

            response = client.put(
                f"/api/bookings/{booking.id}",
                headers=auth_headers,
                json={"booking_status": "refunded"}
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data["booking"]["booking_status"] == "refunded"

            db.session.delete(flight)
            db.session.commit()

    def test_update_booking_cannot_update_cancelled(self, client, app, test_user, auth_headers):
        """Cannot update a booking that is already cancelled."""
        with app.app_context():
            flight = _create_test_flight(code="RT113")
            db.session.add(flight)
            db.session.commit()

            booking, _ = BookingService.book_tickets(
                user_id=test_user.id,
                flight_id=flight.id,
                passengers=[
                    {
                        "passenger_name": "Test Passenger",
                        "passenger_passport_num": "P12121212",
                        "seat_num": "13A",
                        "seat_class": "economy"
                    }
                ],
                booking_status="cancelled"
            )

            response = client.put(
                f"/api/bookings/{booking.id}",
                headers=auth_headers,
                json={"booking_status": "paid"}
            )

            assert response.status_code == 400
            data = response.get_json()
            assert data["error"] == "Bad Request"
            assert "cancelled" in data["message"].lower()

            db.session.delete(flight)
            db.session.commit()

    def test_update_booking_cannot_update_refunded(self, client, app, test_user, auth_headers):
        """Cannot update a booking that is already refunded."""
        with app.app_context():
            flight = _create_test_flight(code="RT114")
            db.session.add(flight)
            db.session.commit()

            booking, _ = BookingService.book_tickets(
                user_id=test_user.id,
                flight_id=flight.id,
                passengers=[
                    {
                        "passenger_name": "Test Passenger",
                        "passenger_passport_num": "P13131313",
                        "seat_num": "14A",
                        "seat_class": "economy"
                    }
                ],
                booking_status="refunded"
            )

            response = client.put(
                f"/api/bookings/{booking.id}",
                headers=auth_headers,
                json={"booking_status": "paid"}
            )

            assert response.status_code == 400
            data = response.get_json()
            assert data["error"] == "Bad Request"
            assert "refunded" in data["message"].lower()

            db.session.delete(flight)
            db.session.commit()

    def test_update_booking_invalid_status(self, client, app, test_user, auth_headers):
        """Invalid booking_status should fail validation."""
        with app.app_context():
            flight = _create_test_flight(code="RT115")
            db.session.add(flight)
            db.session.commit()

            booking, _ = BookingService.book_tickets(
                user_id=test_user.id,
                flight_id=flight.id,
                passengers=[
                    {
                        "passenger_name": "Test Passenger",
                        "passenger_passport_num": "P14141414",
                        "seat_num": "15A",
                        "seat_class": "economy"
                    }
                ]
            )

            response = client.put(
                f"/api/bookings/{booking.id}",
                headers=auth_headers,
                json={"booking_status": "invalid_status"}
            )

            assert response.status_code == 400
            data = response.get_json()
            assert data["error"] == "Bad Request"
            assert "errors" in data

            db.session.delete(flight)
            db.session.commit()

    def test_update_booking_missing_status(self, client, app, test_user, auth_headers):
        """booking_status is required in request body."""
        with app.app_context():
            flight = _create_test_flight(code="RT116")
            db.session.add(flight)
            db.session.commit()

            booking, _ = BookingService.book_tickets(
                user_id=test_user.id,
                flight_id=flight.id,
                passengers=[
                    {
                        "passenger_name": "Test Passenger",
                        "passenger_passport_num": "P15151515",
                        "seat_num": "16A",
                        "seat_class": "economy"
                    }
                ]
            )

            response = client.put(
                f"/api/bookings/{booking.id}",
                headers=auth_headers,
                json={}
            )

            assert response.status_code == 400
            data = response.get_json()
            assert data["error"] == "Bad Request"
            assert "errors" in data

            db.session.delete(flight)
            db.session.commit()

    def test_update_booking_not_found(self, client, auth_headers):
        """Update non-existent booking returns 404."""
        booking_id = "00000000-0000-0000-0000-000000000002"
        response = client.put(
            f"/api/bookings/{booking_id}",
            headers=auth_headers,
            json={"booking_status": "paid"}
        )

        assert response.status_code == 404
        data = response.get_json()
        assert data["error"] == "Not Found"

    def test_update_booking_forbidden_for_non_owner(self, client, app, test_user):
        """Non-owner cannot update another user's booking."""
        with app.app_context():
            flight = _create_test_flight(code="RT117")
            db.session.add(flight)
            db.session.commit()

            owner = User(
                firstname="Booking",
                lastname="Owner",
                email="owner.update@test.com",
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
                        "passenger_name": "Owner Passenger",
                        "passenger_passport_num": "P16161616",
                        "seat_num": "17A",
                        "seat_class": "economy"
                    }
                ]
            )

            token = UserService.generate_token(test_user)
            headers = {"Authorization": f"Bearer {token}"}
            response = client.put(
                f"/api/bookings/{booking.id}",
                headers=headers,
                json={"booking_status": "paid"}
            )

            assert response.status_code == 403
            data = response.get_json()
            assert data["error"] == "Forbidden"

            db.session.delete(owner)
            db.session.delete(flight)
            db.session.commit()

    def test_update_booking_admin_can_update_any(self, client, app, test_user, admin_headers):
        """Admin can update any user's booking."""
        with app.app_context():
            flight = _create_test_flight(code="RT118")
            db.session.add(flight)
            db.session.commit()

            booking, _ = BookingService.book_tickets(
                user_id=test_user.id,
                flight_id=flight.id,
                passengers=[
                    {
                        "passenger_name": "User Passenger",
                        "passenger_passport_num": "P17171717",
                        "seat_num": "18A",
                        "seat_class": "economy"
                    }
                ]
            )

            response = client.put(
                f"/api/bookings/{booking.id}",
                headers=admin_headers,
                json={"booking_status": "paid"}
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data["booking"]["booking_status"] == "paid"

            db.session.delete(flight)
            db.session.commit()

    def test_update_booking_requires_auth(self, client, app, test_user):
        """Update endpoint requires authentication."""
        with app.app_context():
            flight = _create_test_flight(code="RT119")
            db.session.add(flight)
            db.session.commit()

            booking, _ = BookingService.book_tickets(
                user_id=test_user.id,
                flight_id=flight.id,
                passengers=[
                    {
                        "passenger_name": "Test Passenger",
                        "passenger_passport_num": "P18181818",
                        "seat_num": "19A",
                        "seat_class": "economy"
                    }
                ]
            )

            response = client.put(
                f"/api/bookings/{booking.id}",
                json={"booking_status": "paid"}
            )

            assert response.status_code == 401
            data = response.get_json()
            assert data["error"] == "Authentication required"

            db.session.delete(flight)
            db.session.commit()


class TestCancelBookingEndpoint:
    """Test DELETE /api/bookings/<booking_id> endpoint."""

    def test_cancel_booking_success_by_owner(self, client, app, test_user, auth_headers):
        """Owner can successfully cancel their booking."""
        with app.app_context():
            flight = _create_test_flight(code="RT120")
            db.session.add(flight)
            db.session.commit()

            booking, _ = BookingService.book_tickets(
                user_id=test_user.id,
                flight_id=flight.id,
                passengers=[
                    {
                        "passenger_name": "Test Passenger",
                        "passenger_passport_num": "P19191919",
                        "seat_num": "20A",
                        "seat_class": "economy"
                    }
                ]
            )

            response = client.delete(
                f"/api/bookings/{booking.id}",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data["message"] == "Booking cancelled successfully"
            assert data["booking"]["booking_status"] == "cancelled"
            assert data["booking"]["id"] == str(booking.id)

            db.session.delete(flight)
            db.session.commit()

    def test_cancel_booking_paid_status(self, client, app, test_user, auth_headers):
        """Can cancel a paid booking."""
        with app.app_context():
            flight = _create_test_flight(code="RT121")
            db.session.add(flight)
            db.session.commit()

            booking, _ = BookingService.book_tickets(
                user_id=test_user.id,
                flight_id=flight.id,
                passengers=[
                    {
                        "passenger_name": "Test Passenger",
                        "passenger_passport_num": "P20202020",
                        "seat_num": "21A",
                        "seat_class": "economy"
                    }
                ],
                booking_status="paid"
            )

            response = client.delete(
                f"/api/bookings/{booking.id}",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data["booking"]["booking_status"] == "cancelled"

            db.session.delete(flight)
            db.session.commit()

    def test_cancel_booking_already_cancelled(self, client, app, test_user, auth_headers):
        """Cannot cancel an already cancelled booking."""
        with app.app_context():
            flight = _create_test_flight(code="RT122")
            db.session.add(flight)
            db.session.commit()

            booking, _ = BookingService.book_tickets(
                user_id=test_user.id,
                flight_id=flight.id,
                passengers=[
                    {
                        "passenger_name": "Test Passenger",
                        "passenger_passport_num": "P21212121",
                        "seat_num": "22A",
                        "seat_class": "economy"
                    }
                ],
                booking_status="cancelled"
            )

            response = client.delete(
                f"/api/bookings/{booking.id}",
                headers=auth_headers
            )

            assert response.status_code == 400
            data = response.get_json()
            assert data["error"] == "Bad Request"
            assert "already cancelled" in data["message"].lower()

            db.session.delete(flight)
            db.session.commit()

    def test_cancel_booking_cannot_cancel_refunded(self, client, app, test_user, auth_headers):
        """Cannot cancel a refunded booking."""
        with app.app_context():
            flight = _create_test_flight(code="RT123")
            db.session.add(flight)
            db.session.commit()

            booking, _ = BookingService.book_tickets(
                user_id=test_user.id,
                flight_id=flight.id,
                passengers=[
                    {
                        "passenger_name": "Test Passenger",
                        "passenger_passport_num": "P22222222",
                        "seat_num": "23A",
                        "seat_class": "economy"
                    }
                ],
                booking_status="refunded"
            )

            response = client.delete(
                f"/api/bookings/{booking.id}",
                headers=auth_headers
            )

            assert response.status_code == 400
            data = response.get_json()
            assert data["error"] == "Bad Request"
            assert "refunded" in data["message"].lower()

            db.session.delete(flight)
            db.session.commit()

    def test_cancel_booking_not_found(self, client, auth_headers):
        """Cancel non-existent booking returns 404."""
        booking_id = "00000000-0000-0000-0000-000000000003"
        response = client.delete(
            f"/api/bookings/{booking_id}",
            headers=auth_headers
        )

        assert response.status_code == 404
        data = response.get_json()
        assert data["error"] == "Not Found"

    def test_cancel_booking_forbidden_for_non_owner(self, client, app, test_user):
        """Non-owner cannot cancel another user's booking."""
        with app.app_context():
            flight = _create_test_flight(code="RT124")
            db.session.add(flight)
            db.session.commit()

            owner = User(
                firstname="Booking",
                lastname="Owner",
                email="owner.cancel@test.com",
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
                        "passenger_name": "Owner Passenger",
                        "passenger_passport_num": "P23232323",
                        "seat_num": "24A",
                        "seat_class": "economy"
                    }
                ]
            )

            token = UserService.generate_token(test_user)
            headers = {"Authorization": f"Bearer {token}"}
            response = client.delete(
                f"/api/bookings/{booking.id}",
                headers=headers
            )

            assert response.status_code == 403
            data = response.get_json()
            assert data["error"] == "Forbidden"

            db.session.delete(owner)
            db.session.delete(flight)
            db.session.commit()

    def test_cancel_booking_admin_can_cancel_any(self, client, app, test_user, admin_headers):
        """Admin can cancel any user's booking."""
        with app.app_context():
            flight = _create_test_flight(code="RT125")
            db.session.add(flight)
            db.session.commit()

            booking, _ = BookingService.book_tickets(
                user_id=test_user.id,
                flight_id=flight.id,
                passengers=[
                    {
                        "passenger_name": "User Passenger",
                        "passenger_passport_num": "P24242424",
                        "seat_num": "25A",
                        "seat_class": "economy"
                    }
                ]
            )

            response = client.delete(
                f"/api/bookings/{booking.id}",
                headers=admin_headers
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data["booking"]["booking_status"] == "cancelled"

            db.session.delete(flight)
            db.session.commit()

    def test_cancel_booking_requires_auth(self, client, app, test_user):
        """Cancel endpoint requires authentication."""
        with app.app_context():
            flight = _create_test_flight(code="RT126")
            db.session.add(flight)
            db.session.commit()

            booking, _ = BookingService.book_tickets(
                user_id=test_user.id,
                flight_id=flight.id,
                passengers=[
                    {
                        "passenger_name": "Test Passenger",
                        "passenger_passport_num": "P25252525",
                        "seat_num": "26A",
                        "seat_class": "economy"
                    }
                ]
            )

            response = client.delete(f"/api/bookings/{booking.id}")

            assert response.status_code == 401
            data = response.get_json()
            assert data["error"] == "Authentication required"

            db.session.delete(flight)
            db.session.commit()

    def test_cancel_booking_updates_timestamp(self, client, app, test_user, auth_headers):
        """Cancelling a booking updates the updated_at timestamp."""
        with app.app_context():
            flight = _create_test_flight(code="RT127")
            db.session.add(flight)
            db.session.commit()

            booking, _ = BookingService.book_tickets(
                user_id=test_user.id,
                flight_id=flight.id,
                passengers=[
                    {
                        "passenger_name": "Test Passenger",
                        "passenger_passport_num": "P26262626",
                        "seat_num": "27A",
                        "seat_class": "economy"
                    }
                ]
            )

            original_updated_at = booking.updated_at

            import time
            time.sleep(0.1)

            response = client.delete(
                f"/api/bookings/{booking.id}",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.get_json()

            # Parse timestamps and compare
            from datetime import datetime
            response_updated_at = datetime.fromisoformat(data["booking"]["updated_at"])
            assert response_updated_at > original_updated_at

            db.session.delete(flight)
            db.session.commit()


class TestBookingErrorHandling:
    """Test error handling and exception paths in booking endpoints."""

    def test_create_booking_with_invalid_json_format(self, client, auth_headers):
        """Test create booking with invalid JSON format."""
        response = client.post(
            "/api/bookings/",
            headers=auth_headers,
            data="invalid json",
            content_type="application/json"
        )
        # Invalid JSON returns 500 from Flask request parsing
        assert response.status_code in [400, 500]

    def test_create_booking_empty_passengers_list(self, client, auth_headers):
        """Test create booking with empty passengers list."""
        response = client.post(
            "/api/bookings/",
            headers=auth_headers,
            json={
                "flight_id": "fe4a1338-4b98-4b51-9f5c-1234567890ab",
                "passengers": []
            }
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data["error"] == "Bad Request"

    def test_update_booking_nonexistent(self, client, auth_headers):
        """Test update nonexistent booking returns 404."""
        fake_id = "fe4a1338-4b98-4b51-9f5c-1234567890ab"
        response = client.put(
            f"/api/bookings/{fake_id}",
            headers=auth_headers,
            json={"booking_status": "cancelled"}
        )
        assert response.status_code == 404
        data = response.get_json()
        assert "not found" in data["message"].lower()

    def test_update_booking_invalid_status(self, client, app, auth_headers, test_user):
        """Test update booking with invalid status value."""
        with app.app_context():
            flight = _create_test_flight()
            db.session.add(flight)
            db.session.commit()

            booking, _ = BookingService.book_tickets(
                user_id=test_user.id,
                flight_id=flight.id,
                passengers=[
                    {
                        "passenger_name": "Test",
                        "passenger_passport_num": "P99999999",
                        "seat_num": "99A",
                        "seat_class": "economy"
                    }
                ]
            )
            booking_id = booking.id

        response = client.put(
            f"/api/bookings/{booking_id}",
            headers=auth_headers,
            json={"booking_status": "invalid_status"}
        )
        assert response.status_code == 400

    def test_update_booking_forbidden_other_user(self, client, app):
        """Test user cannot update another user's booking."""
        user1_id = None
        user2_id = None
        booking_id = None

        with app.app_context():
            user1 = User(
                firstname='User1',
                lastname='One',
                email=f'user1_{datetime.now().timestamp()}@test.com',
                password_hash=generate_password_hash('password123'),
                role=Roles.user
            )
            user2 = User(
                firstname='User2',
                lastname='Two',
                email=f'user2_{datetime.now().timestamp()}@test.com',
                password_hash=generate_password_hash('password123'),
                role=Roles.user
            )
            db.session.add(user1)
            db.session.add(user2)
            db.session.commit()
            user1_id = user1.id
            user2_id = user2.id

            flight = _create_test_flight()
            db.session.add(flight)
            db.session.commit()

            booking, _ = BookingService.book_tickets(
                user_id=user1.id,
                flight_id=flight.id,
                passengers=[
                    {
                        "passenger_name": "User1",
                        "passenger_passport_num": "P11111111",
                        "seat_num": "11A",
                        "seat_class": "economy"
                    }
                ]
            )
            booking_id = booking.id

        with app.app_context():
            user2 = User.query.get(user2_id)
            token = UserService.generate_token(user2)
            headers = {'Authorization': f'Bearer {token}'}

        response = client.put(
            f"/api/bookings/{booking_id}",
            headers=headers,
            json={"booking_status": "cancelled"}
        )
        assert response.status_code == 403
        assert "not allowed" in response.get_json()['message'].lower()

    def test_cancel_booking_nonexistent(self, client, auth_headers):
        """Test cancel nonexistent booking returns 404."""
        fake_id = "fe4a1338-4b98-4b51-9f5c-1234567890ab"
        response = client.delete(
            f"/api/bookings/{fake_id}",
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_cancel_booking_forbidden_other_user(self, client, app):
        """Test user cannot cancel another user's booking."""
        user1_id = None
        user2_id = None
        booking_id = None

        with app.app_context():
            user1 = User(
                firstname='User1',
                lastname='One',
                email=f'user1_{datetime.now().timestamp()}@test.com',
                password_hash=generate_password_hash('password123'),
                role=Roles.user
            )
            user2 = User(
                firstname='User2',
                lastname='Two',
                email=f'user2_{datetime.now().timestamp()}@test.com',
                password_hash=generate_password_hash('password123'),
                role=Roles.user
            )
            db.session.add(user1)
            db.session.add(user2)
            db.session.commit()
            user2_id = user2.id

            flight = _create_test_flight()
            db.session.add(flight)
            db.session.commit()

            booking, _ = BookingService.book_tickets(
                user_id=user1.id,
                flight_id=flight.id,
                passengers=[
                    {
                        "passenger_name": "User1",
                        "passenger_passport_num": "P22222222",
                        "seat_num": "22A",
                        "seat_class": "economy"
                    }
                ]
            )
            booking_id = booking.id

        with app.app_context():
            user2 = User.query.get(user2_id)
            token = UserService.generate_token(user2)
            headers = {'Authorization': f'Bearer {token}'}

        response = client.delete(
            f"/api/bookings/{booking_id}",
            headers=headers
        )
        assert response.status_code == 403

    def test_get_booking_nonexistent(self, client, auth_headers):
        """Test get nonexistent booking returns 404."""
        fake_id = "fe4a1338-4b98-4b51-9f5c-1234567890ab"
        response = client.get(
            f"/api/bookings/{fake_id}",
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_get_booking_forbidden_other_user(self, client, app):
        """Test user cannot get another user's booking."""
        user1_id = None
        user2_id = None
        booking_id = None

        with app.app_context():
            user1 = User(
                firstname='User1',
                lastname='One',
                email=f'user1_{datetime.now().timestamp()}@test.com',
                password_hash=generate_password_hash('password123'),
                role=Roles.user
            )
            user2 = User(
                firstname='User2',
                lastname='Two',
                email=f'user2_{datetime.now().timestamp()}@test.com',
                password_hash=generate_password_hash('password123'),
                role=Roles.user
            )
            db.session.add(user1)
            db.session.add(user2)
            db.session.commit()
            user2_id = user2.id

            flight = _create_test_flight()
            db.session.add(flight)
            db.session.commit()

            booking, _ = BookingService.book_tickets(
                user_id=user1.id,
                flight_id=flight.id,
                passengers=[
                    {
                        "passenger_name": "User1",
                        "passenger_passport_num": "P33333333",
                        "seat_num": "33A",
                        "seat_class": "economy"
                    }
                ]
            )
            booking_id = booking.id

        with app.app_context():
            user2 = User.query.get(user2_id)
            token = UserService.generate_token(user2)
            headers = {'Authorization': f'Bearer {token}'}

        response = client.get(
            f"/api/bookings/{booking_id}",
            headers=headers
        )
        assert response.status_code == 403

    def test_seat_availability_invalid_flight_id(self, client, auth_headers):
        """Test seat availability with invalid flight ID."""
        response = client.get(
            "/api/bookings/availability?flight_id=invalid&seat_num=1A",
            headers=auth_headers
        )
        assert response.status_code == 400

    def test_seat_availability_missing_seat_num(self, client, auth_headers):
        """Test seat availability with missing seat number."""
        response = client.get(
            f"/api/bookings/availability?flight_id=fe4a1338-4b98-4b51-9f5c-1234567890ab",
            headers=auth_headers
        )
        assert response.status_code == 400

    def test_seat_availability_missing_flight_id(self, client, auth_headers):
        """Test seat availability with missing flight ID."""
        response = client.get(
            "/api/bookings/availability?seat_num=1A",
            headers=auth_headers
        )
        assert response.status_code == 400

    def test_list_bookings_with_pagination(self, client, app, auth_headers, test_user):
        """Test list bookings with pagination."""
        with app.app_context():
            flight = _create_test_flight()
            db.session.add(flight)
            db.session.commit()

            for i in range(5):
                BookingService.book_tickets(
                    user_id=test_user.id,
                    flight_id=flight.id,
                    passengers=[
                        {
                            "passenger_name": f"User{i}",
                            "passenger_passport_num": f"P{i:08d}",
                            "seat_num": f"{i+1}A",
                            "seat_class": "economy"
                        }
                    ]
                )

        response = client.get(
            "/api/bookings/?page=1&per_page=2",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["per_page"] == 2

    def test_list_bookings_invalid_page(self, client, auth_headers):
        """Test list bookings with invalid page number."""
        response = client.get(
            "/api/bookings/?page=invalid&per_page=10",
            headers=auth_headers
        )
        assert response.status_code == 400

    def test_seat_availability_ValueError_exception(self, client, app, auth_headers):
        """Test seat availability endpoint handles ValueError from service."""
        with app.app_context():
            flight = _create_test_flight()
            db.session.add(flight)
            db.session.commit()
            flight_id = flight.id

            # Monkey patch the service method to raise ValueError
            original_method = BookingService.get_seat_availability
            def raise_value_error(*args, **kwargs):
                raise ValueError("Invalid seat format")
            BookingService.get_seat_availability = raise_value_error

        response = client.get(
            f"/api/bookings/availability?flight_id={flight_id}&seat_num=1A",
            headers=auth_headers
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data["error"] == "Bad Request"
        assert "invalid seat" in data["message"].lower()

        # Restore original method
        with app.app_context():
            BookingService.get_seat_availability = original_method

    def test_seat_availability_unexpected_exception(self, client, app, auth_headers):
        """Test seat availability endpoint handles unexpected exceptions."""
        with app.app_context():
            flight = _create_test_flight()
            db.session.add(flight)
            db.session.commit()
            flight_id = flight.id

            # Monkey patch the service method to raise an exception
            original_method = BookingService.get_seat_availability
            def raise_exception(*args, **kwargs):
                raise Exception("Unexpected error in service")
            BookingService.get_seat_availability = raise_exception

        response = client.get(
            f"/api/bookings/availability?flight_id={flight_id}&seat_num=1A",
            headers=auth_headers
        )
        assert response.status_code == 500
        data = response.get_json()
        assert data["error"] == "Internal Server Error"
        assert "unexpected" in data["message"].lower()

        # Restore original method
        with app.app_context():
            BookingService.get_seat_availability = original_method

