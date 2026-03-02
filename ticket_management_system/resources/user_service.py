import os
from datetime import datetime, timedelta, timezone

import jwt
from werkzeug.security import check_password_hash, generate_password_hash

from ticket_management_system.extensions import db
from ticket_management_system.models import Roles, User

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dummy-secret-key-for-development")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24


class UserService:
    @staticmethod
    def validate_registration_data(data):
        if not data:
            return False, "Request body must be JSON"

        required_fields = ["firstname", "lastname", "email", "password"]
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            return False, f'Missing required fields: {", ".join(missing_fields)}'

        if len(data["firstname"]) > 30:
            return False, "firstname must be 30 characters or less"
        if len(data["lastname"]) > 30:
            return False, "lastname must be 30 characters or less"
        if len(data["email"]) > 30:
            return False, "email must be 30 characters or less"
        if len(data["password"]) < 6:
            return False, "password must be at least 6 characters"

        return True, None

    @staticmethod
    def validate_role(role_str):
        if not role_str:
            return Roles.user, None

        role_str = role_str.lower()
        if role_str == "admin":
            return Roles.admin, None
        if role_str == "user":
            return Roles.user, None
        return None, 'Invalid role. Must be "admin" or "user"'

    @staticmethod
    def email_exists(email):
        return User.query.filter_by(email=email).first() is not None

    @staticmethod
    def create_user(firstname, lastname, email, password, role=Roles.user):
        password_hash = generate_password_hash(password)

        new_user = User(
            firstname=firstname,
            lastname=lastname,
            email=email,
            password_hash=password_hash,
            role=role,
        )

        db.session.add(new_user)
        db.session.commit()

        return new_user

    @staticmethod
    def generate_token(user):
        token_payload = {
            "user_id": str(user.id),
            "email": user.email,
            "role": user.role.name,
            "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS),
            "iat": datetime.now(timezone.utc),
        }

        token = jwt.encode(token_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return token

    @staticmethod
    def format_user_response(user, include_token=False):
        response = {
            "user": {
                "id": str(user.id),
                "firstname": user.firstname,
                "lastname": user.lastname,
                "email": user.email,
                "role": user.role.name,
                "created_at": user.created_at.isoformat(),
            }
        }

        if include_token:
            token = UserService.generate_token(user)
            response["token"] = token
            response["token_type"] = "Bearer"
            response["expires_in"] = JWT_EXPIRATION_HOURS * 3600

        return response

    @staticmethod
    def authenticate_user(email, password):
        user = User.query.filter_by(email=email).first()

        if not user:
            return None, "Invalid email or password"

        if not check_password_hash(user.password_hash, password):
            return None, "Invalid email or password"

        return user, None

    @staticmethod
    def verify_token(token):
        try:
            import uuid as uuid_lib

            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

            user_id = payload["user_id"]
            if isinstance(user_id, str):
                user_id = uuid_lib.UUID(user_id)

            user = User.query.filter_by(id=user_id).first()

            if not user:
                return None, "User not found"

            return user, None

        except jwt.ExpiredSignatureError:
            return None, "Token expired"
        except jwt.InvalidTokenError:
            return None, "Invalid token"

    @staticmethod
    def get_user_by_id(user_id):
        return User.query.filter_by(id=user_id).first()

    @staticmethod
    def get_paginated_users(page=1, per_page=10):
        if page < 1:
            page = 1
        if per_page < 1:
            per_page = 10
        if per_page > 100:
            per_page = 100

        pagination = User.query.paginate(page=page, per_page=per_page, error_out=False)

        users_data = [
            {
                "id": str(user.id),
                "firstname": user.firstname,
                "lastname": user.lastname,
                "email": user.email,
                "role": user.role.name,
                "created_at": user.created_at.isoformat(),
            }
            for user in pagination.items
        ]

        return {
            "users": users_data,
            "pagination": {
                "page": pagination.page,
                "per_page": pagination.per_page,
                "total_pages": pagination.pages,
                "total_items": pagination.total,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev,
                "next_page": pagination.next_num if pagination.has_next else None,
                "prev_page": pagination.prev_num if pagination.has_prev else None,
            },
        }

    @staticmethod
    def format_user_detail(user):
        return {
            "user": {
                "id": str(user.id),
                "firstname": user.firstname,
                "lastname": user.lastname,
                "email": user.email,
                "role": user.role.name,
                "created_at": user.created_at.isoformat(),
                "updated_at": user.updated_at.isoformat(),
            }
        }
