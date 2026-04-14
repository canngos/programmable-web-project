"""Validation schemas for flight endpoints."""
from datetime import datetime
from marshmallow import Schema, fields, ValidationError, validates_schema, validate


class FlightSearchSchema(Schema):
    """Schema for flight search validation."""
    status = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.OneOf(["all", "active", "inactive", "started", "en_route", "landed", "cancelled", "delayed"])
    )
    origin_airport = fields.Str(required=False, allow_none=True)
    destination_airport = fields.Str(required=False, allow_none=True)
    departure_date = fields.Date(required=False, allow_none=True, format='%Y-%m-%d')
    arrival_date = fields.Date(required=False, allow_none=True, format='%Y-%m-%d')
    page = fields.Int(required=False, load_default=1, validate=validate.Range(min=1))
    per_page = fields.Int(required=False, load_default=10, validate=validate.Range(min=1, max=100))
    sort_by = fields.Str(
        required=False,
        load_default="departure_time",
        validate=validate.OneOf(["departure_time", "arrival_time", "base_price"]),
    )
    sort_order = fields.Str(
        required=False,
        load_default="asc",
        validate=validate.OneOf(["asc", "desc"]),
    )

    @validates_schema
    def validate_dates(self, data, **_kwargs):
        """Validate date parameters."""
        # Validate arrival is after departure if both provided
        if (data.get('departure_date') and data.get('arrival_date') and
                data['departure_date'] > data['arrival_date']):
            raise ValidationError('Arrival date must be on or after departure date', 'arrival_date')


class AddFlightSchema(Schema):
    """Schema for adding a new flight."""
    flight_code = fields.Str(required=True, validate=validate.Length(min=3, max=8))
    origin_airport = fields.Str(required=True, validate=validate.Length(min=3, max=30))
    destination_airport = fields.Str(required=True, validate=validate.Length(min=3, max=30))
    departure_time = fields.DateTime(required=True, format='%Y-%m-%d %H:%M:%S')
    arrival_time = fields.DateTime(required=True, format='%Y-%m-%d %H:%M:%S')
    base_price = fields.Decimal(required=True, places=2, validate=validate.Range(min=0))

    @validates_schema
    def validate_flight_data(self, data, **_kwargs):
        """Validate flight creation data."""
        now = datetime.now()

        # Validate departure time is not in the past
        if 'departure_time' in data and data['departure_time']:
            if data['departure_time'] < now:
                raise ValidationError('Departure time cannot be in the past', 'departure_time')

        # Validate arrival time is not in the past
        if 'arrival_time' in data and data['arrival_time']:
            if data['arrival_time'] < now:
                raise ValidationError('Arrival time cannot be in the past', 'arrival_time')

        # Validate arrival is after departure
        if (data.get('departure_time') and data.get('arrival_time') and
            data['arrival_time'] <= data['departure_time']):
            raise ValidationError('Arrival time must be after departure time', 'arrival_time')

        # Validate origin and destination are different
        if (data.get('origin_airport') and data.get('destination_airport') and
            data['origin_airport'].strip().lower() == data['destination_airport'].strip().lower()):
            raise ValidationError('Origin and destination airports must be different', 'destination_airport')


class UpdateFlightSchema(Schema):
    """Schema for updating an existing flight."""
    origin_airport = fields.Str(required=False, validate=validate.Length(min=3, max=30))
    destination_airport = fields.Str(required=False, validate=validate.Length(min=3, max=30))
    departure_time = fields.DateTime(required=False, format='%Y-%m-%d %H:%M:%S')
    arrival_time = fields.DateTime(required=False, format='%Y-%m-%d %H:%M:%S')
    base_price = fields.Decimal(required=False, places=2, validate=validate.Range(min=0))
    status = fields.Str(
        required=False,
        validate=validate.OneOf(["active", "inactive", "started", "en_route", "landed", "cancelled", "delayed"])
    )

    @validates_schema
    def validate_flight_data(self, data, **_kwargs):
        """Validate flight update data."""
        # At least one field must be provided
        if not data:
            raise ValidationError('At least one field must be provided for update')

        now = datetime.now()

        # Validate departure time is not in the past
        if 'departure_time' in data and data['departure_time']:
            if data['departure_time'] < now:
                raise ValidationError('Departure time cannot be in the past', 'departure_time')

        # Validate arrival time is not in the past
        if 'arrival_time' in data and data['arrival_time']:
            if data['arrival_time'] < now:
                raise ValidationError('Arrival time cannot be in the past', 'arrival_time')

        # Validate arrival is after departure
        if (data.get('departure_time') and data.get('arrival_time') and
            data['arrival_time'] <= data['departure_time']):
            raise ValidationError('Arrival time must be after departure time', 'arrival_time')

        # Validate origin and destination are different
        if (data.get('origin_airport') and data.get('destination_airport') and
            data['origin_airport'].strip().lower() == data['destination_airport'].strip().lower()):
            raise ValidationError('Origin and destination airports must be different', 'destination_airport')

