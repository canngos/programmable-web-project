from marshmallow import Schema, fields, validate


class PassengerSchema(Schema):
    passenger_name = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    passenger_passport_num = fields.Str(required=True, validate=validate.Length(min=1, max=12))
    seat_num = fields.Str(required=True, validate=validate.Length(min=1, max=4))
    seat_class = fields.Str(
        required=False,
        load_default="economy",
        validate=validate.OneOf(["economy", "business", "first"]),
    )


class BookTicketsSchema(Schema):
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
    page = fields.Int(required=False, load_default=1, validate=validate.Range(min=1))
    per_page = fields.Int(required=False, load_default=10, validate=validate.Range(min=1, max=100))
    all = fields.Bool(required=False, load_default=False)


class SeatAvailabilityQuerySchema(Schema):
    flight_id = fields.UUID(required=True)
    seat_num = fields.Str(required=True, validate=validate.Length(min=1, max=4))


class UpdateBookingSchema(Schema):
    booking_status = fields.Str(
        required=True,
        validate=validate.OneOf(["booked", "paid", "cancelled", "refunded"]),
    )