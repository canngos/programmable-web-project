from flask import Blueprint, jsonify

root_bp = Blueprint("root", __name__)


@root_bp.route("/")
def index():
    return (
        jsonify(
            {
                "name": "Flight Management System API",
                "version": "1.0.0",
                "description": "RESTful API for managing flight bookings",
                "endpoints": {
                    "authentication": {
                        "register": "/api/users/register",
                        "login": "/api/users/login",
                        "profile": "/api/users/me",
                    },
                    "users": "/api/users/",
                    "flights": {
                        "airports": "/api/flights/airports",
                        "search": "/api/flights/search",
                    },
                    "bookings": {
                        "create_or_list": "/api/bookings/",
                        "detail": "/api/bookings/{booking_id}",
                        "seat_availability": "/api/bookings/availability",
                    },
                    "swagger": "/apidocs/",
                },
                "documentation": "Visit /apidocs/ for interactive API documentation",
            }
        ),
        200,
    )


@root_bp.route("/health")
def health_check():
    return (
        jsonify(
            {
                "status": "healthy",
                "service": "Flight Management System API",
            }
        ),
        200,
    )

