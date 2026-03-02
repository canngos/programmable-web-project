from functools import wraps

from flask import jsonify, request

from ticket_management_system.models import Roles
from ticket_management_system.resources.user_service import UserService
from ticket_management_system.exceptions import (
    TokenExpiredError,
    InvalidTokenError,
    UserNotFoundError
)


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

        # Verify token using service (now raises exceptions instead of returning tuple)
        try:
            current_user = UserService.verify_token(token)
        except TokenExpiredError as e:
            return (
                jsonify(
                    {
                        "error": "Token expired",
                        "message": e.message,
                    }
                ),
                401,
            )
        except (InvalidTokenError, UserNotFoundError) as e:
            return (
                jsonify(
                    {
                        "error": "Invalid token",
                        "message": e.message,
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

