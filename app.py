# app.py
import os
from flask import Flask
from dotenv import load_dotenv
from extensions import db, migrate
from flasgger import Swagger

# Load environment variables
load_dotenv()


def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL', 
        'postgresql://flask_user:flask_password@localhost:5432/flask_db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Swagger UI Configuration
    app.config['SWAGGER'] = {
        'title': 'Flight Management System API',
        'uiversion': 3,
        'version': '1.0.0',
        'description': 'RESTful API for managing flight bookings with JWT authentication',
        'termsOfService': '',
        'specs_route': '/apidocs/',
        'securityDefinitions': {
            'Bearer': {
                'type': 'apiKey',
                'name': 'Authorization',
                'in': 'header',
                'description': 'JWT Authorization header using the Bearer scheme. Example: "Authorization: Bearer {token}"'
            }
        },
        'security': [
            {'Bearer': []}
        ]
    }

    # Initialize Swagger UI
    Swagger(app)

    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    
     # IMPORT MODELS HERE, inside app context
    # This ensures proper initialization order
    with app.app_context():
        from models import User, Booking, Flight, Ticket  # Import all models

    # Import and register all route blueprints
    from routes import init_routes
    init_routes(app)

    return app

# Create app instance
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=os.getenv('FLASK_ENV') == 'development')