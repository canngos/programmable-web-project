import os

from dotenv import load_dotenv
from flask import Flask
from flasgger import Swagger

from ticket_management_system.extensions import db, migrate

load_dotenv()


def create_app():
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL",
        "postgresql://flask_user:flask_password@localhost:5432/flask_db",
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    app.config["SWAGGER"] = {
        "title": "Flight Management System API",
        "uiversion": 3,
        "version": "1.0.0",
        "description": "RESTful API for managing flight bookings with JWT authentication",
        "termsOfService": "",
        "specs_route": "/apidocs/",
        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": 'JWT Authorization header using the Bearer scheme. Example: "Authorization: Bearer {token}"',
            }
        },
        "security": [{"Bearer": []}],
    }

    Swagger(app)

    db.init_app(app)
    migrate.init_app(app, db)

    # Import models during app initialization so SQLAlchemy sees all tables.
    with app.app_context():
        from ticket_management_system.models import Booking, Flight, Ticket, User

    from ticket_management_system.api import init_routes

    init_routes(app)
    return app
