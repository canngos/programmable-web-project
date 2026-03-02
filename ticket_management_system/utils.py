from functools import wraps

from flask import jsonify, request

from ticket_management_system.models import Roles
from ticket_management_system.resources.user_service import UserService


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if "Authorization" in request.headers:
            auth_header = request.headers["Authorization"]
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return (
                    jsonify(
                        {
                            "error": "Invalid authorization header format",
                            "message": "Use format: Bearer <token>",
                        }
                    ),
                    401,
                )

        if not token:
            return (
                jsonify(
                    {
                        "error": "Authentication required",
                        "message": "No token provided",
                    }
                ),
                401,
            )

        current_user, error = UserService.verify_token(token)

        if error:
            return (
                jsonify(
                    {
                        "error": "Token expired"
                        if "expired" in error.lower()
                        else "Invalid token",
                        "message": error,
                    }
                ),
                401,
            )

        return f(current_user, *args, **kwargs)

    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        if current_user.role != Roles.admin:
            return (
                jsonify(
                    {
                        "error": "Forbidden",
                        "message": "Admin privileges required",
                    }
                ),
                403,
            )

        return f(current_user, *args, **kwargs)

    return decorated

