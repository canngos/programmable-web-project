from marshmallow import Schema, fields, validates, ValidationError, validate


class UserProfileUpdateSchema(Schema):
    firstname = fields.Str(
        required=False,
        allow_none=False,
        validate=[
            validate.Length(min=1, max=30, error='firstname must be between 1 and 30 characters'),
        ]
    )
    lastname = fields.Str(
        required=False,
        allow_none=False,
        validate=[
            validate.Length(min=1, max=30, error='lastname must be between 1 and 30 characters'),
        ]
    )
    email = fields.Email(
        required=False,
        allow_none=False,
        validate=validate.Length(max=255, error='email must be 255 characters or less')
    )
    password = fields.Str(
        required=False,
        allow_none=False,
        validate=validate.Length(min=6, error='password must be at least 6 characters')
    )

    @validates('firstname')
    def validate_firstname_not_empty(self, value, **kwargs):
        if value and not value.strip():
            raise ValidationError('firstname cannot be empty or only whitespace')

    @validates('lastname')
    def validate_lastname_not_empty(self, value, **kwargs):
        if value and not value.strip():
            raise ValidationError('lastname cannot be empty or only whitespace')


class UserRegistrationSchema(Schema):
    firstname = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=30, error='firstname must be between 1 and 30 characters')
    )
    lastname = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=30, error='lastname must be between 1 and 30 characters')
    )
    email = fields.Email(
        required=True,
        validate=validate.Length(max=255, error='email must be 255 characters or less')
    )
    password = fields.Str(
        required=True,
        validate=validate.Length(min=6, error='password must be at least 6 characters')
    )
    role = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.OneOf(['admin', 'user'], error='role must be either "admin" or "user"')
    )
