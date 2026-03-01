"""
Root routes for the Flight Management System API.
Provides basic API information and health check endpoints.
"""

from flask import Blueprint, jsonify

root_bp = Blueprint('root', __name__)


@root_bp.route('/')
def index():
    """
    API root endpoint
    ---
    tags:
      - System
    responses:
      200:
        description: API information and available endpoints
        schema:
          type: object
          properties:
            name:
              type: string
              example: Flight Management System API
            version:
              type: string
              example: 1.0.0
            description:
              type: string
            endpoints:
              type: object
            documentation:
              type: string
    """
    return jsonify({
        'name': 'Flight Management System API',
        'version': '1.0.0',
        'description': 'RESTful API for managing flight bookings',
        'endpoints': {
            'authentication': {
                'register': '/api/users/register',
                'login': '/api/users/login',
                'profile': '/api/users/me'
            },
            'users': '/api/users/',
            'flights': '/api/flights/',
            'bookings': '/api/bookings/',
            'tickets': '/api/tickets/',
            'swagger': '/apidocs/'
        },
        'documentation': 'Visit /apidocs/ for interactive API documentation'
    }), 200


@root_bp.route('/health')
def health_check():
    """
    Health check endpoint
    ---
    tags:
      - System
    responses:
      200:
        description: Service is healthy
        schema:
          type: object
          properties:
            status:
              type: string
              example: healthy
            service:
              type: string
              example: Flight Management System API
    """
    return jsonify({
        'status': 'healthy',
        'service': 'Flight Management System API'
    }), 200
