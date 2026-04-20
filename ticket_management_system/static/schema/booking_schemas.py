"""Validation schemas for booking endpoints."""
from marshmallow import Schema, fields, validate


class PassengerSchema(Schema):
    """Schema for passenger validation."""
    passenger_fname = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    passenger_lname = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    email = email = fields.Email(
        required=False,
        allow_none=False,
        validate=validate.Length(max=255, error='email must be 255 characters or less')
    )
    passenger_passport_num = fields.Str(required=True, validate=validate.Length(min=1, max=12))
    seat_num = fields.Str(required=True, validate=validate.Length(min=1, max=4))
    seat_class = fields.Str(
        required=False,
        load_default="economy",
        validate=validate.OneOf(["economy", "business", "first"]),
    )


class BookTicketsSchema(Schema):
    """Schema for booking tickets validation."""
    user_id = fields.UUID(required=False, allow_none=True, load_default=None)
    flight_id = fields.UUID(required=True)
    booking_status = fields.Str(
        required=False,
        load_default="booked",
        validate=validate.OneOf(["booked", "paid", "cancelled", "refunded"]),
    )
    passengers = fields.List(
        fields.Nested(PassengerSchema),
        required=True,
        validate=validate.Length(min=1, max=10),
    )


class PaginationQuerySchema(Schema):
    """Schema for pagination query parameters."""
    page = fields.Int(required=False, load_default=1, validate=validate.Range(min=1))
    per_page = fields.Int(required=False, load_default=10, validate=validate.Range(min=1, max=100))
    all = fields.Bool(required=False, load_default=False)


class SeatAvailabilityQuerySchema(Schema):
    """Schema for seat availability check."""
    flight_id = fields.UUID(required=True)
    seat_num = fields.Str(required=True, validate=validate.Length(min=1, max=4))


class UpdateBookingSchema(Schema):
    """Schema for updating booking status."""
    booking_status = fields.Str(
        required=True,
        validate=validate.OneOf(["booked", "paid", "cancelled", "refunded"]),
    )
