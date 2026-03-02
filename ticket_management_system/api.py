from flask import Blueprint

from ticket_management_system.resources import bookings, flights, root, users

api_bp = Blueprint("api", __name__, url_prefix="/api")


def init_routes(app):
    app.register_blueprint(root.root_bp)
    app.register_blueprint(users.user_bp)
    app.register_blueprint(flights.flight_bp)
    app.register_blueprint(bookings.booking_bp)

