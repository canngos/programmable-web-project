"""Common utility functions used across the application."""
from flask import jsonify
from ticket_management_system.extensions import db


def format_pagination_response(data_key, data, pagination):
    """
    Format a paginated response with consistent structure.

    Args:
        data_key: Key name for the data in response (e.g., 'flights', 'users')
        data: The actual data list
        pagination: SQLAlchemy pagination object

    Returns:
        dict: Formatted response with data and pagination info
    """
    return {
        data_key: data,
        'pagination': {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total_pages': pagination.pages,
            'total_items': pagination.total,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev,
            'next_page': pagination.next_num if pagination.has_next else None,
            'prev_page': pagination.prev_num if pagination.has_prev else None
        }
    }


def handle_validation_error(err):
    """
    Handle Marshmallow ValidationError consistently.

    Args:
        err: ValidationError exception

    Returns:
        tuple: JSON response and 400 status code
    """
    return jsonify({
        'error': 'Bad Request',
        'message': 'Validation failed',
        'errors': err.messages
    }), 400


def handle_general_error(error, rollback=True):
    """
    Handle general exceptions consistently.

    Args:
        error: Exception object
        rollback: Whether to rollback database session

    Returns:
        tuple: JSON response and 500 status code
    """
    if rollback:
        db.session.rollback()

    return jsonify({
        'error': 'Internal Server Error',
        'message': str(error)
    }), 500


def handle_conflict_error(message):
    """
    Handle conflict errors (409) consistently.

    Args:
        message: Error message string

    Returns:
        tuple: JSON response and 409 status code
    """
    return jsonify({
        'error': 'Conflict',
        'message': message
    }), 409
