"""
Routes package for the Flight Management System API.
This package contains all API endpoint definitions organized by resource.
"""

from flask import Blueprint

# Create a main API blueprint that can be used as a base
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Import all route modules to register them
from routes import user_routes, root_routes, flight_routes

def init_routes(app):
    """
    Initialize and register all route blueprints with the Flask app.

    Args:
        app: Flask application instance
    """
    # Register the root routes blueprint
    app.register_blueprint(root_routes.root_bp)

    # Register the user routes blueprint
    app.register_blueprint(user_routes.user_bp)

    # Register the flight routes blueprint
    app.register_blueprint(flight_routes.flight_bp)
