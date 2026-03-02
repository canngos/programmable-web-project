
import uuid
import enum
from datetime import datetime
from sqlalchemy import Enum
from sqlalchemy import DECIMAL as Decimal
from ticket_management_system.extensions import db

class Roles(enum.Enum):
    admin = 1
    user = 2

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.UUID, primary_key=True, default=uuid.uuid4)
    firstname = db.Column(db.String(60), nullable=False)
    lastname = db.Column(db.String(60), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(Enum(Roles), nullable=False, default=Roles.user)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    bookings = db.relationship("Booking", back_populates="user", lazy=True, cascade="all, delete-orphan")

class FlightStatus(enum.Enum):
    active = 1
    inactive = 2
    started = 3
    en_route = 4
    landed = 5
    cancelled = 6
    delayed = 7

class Flight(db.Model):
    __tablename__ = 'flights'

    id = db.Column(db.UUID, primary_key=True, default=uuid.uuid4)
    flight_code = db.Column(db.String(8), nullable=False, unique=True)
    origin_airport = db.Column(db.String(30), nullable=False)
    destination_airport = db.Column(db.String(30), nullable=False)
    departure_time = db.Column(db.DateTime, nullable=False)
    arrival_time = db.Column(db.DateTime, nullable=False)
    base_price = db.Column(Decimal(8, 2), nullable=False)
    status = db.Column(Enum(FlightStatus), nullable=False, default=FlightStatus.active)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    bookings = db.relationship("Booking", back_populates="flight", lazy=True, cascade="all, delete-orphan")
    tickets = db.relationship("Ticket", back_populates="flight", lazy=True, cascade="all, delete-orphan")

class BookingStatus(enum.Enum):
    booked = 1
    paid = 2
    cancelled = 3
    refunded = 4

class Booking(db.Model):
    __tablename__ = 'bookings'

    id = db.Column(db.UUID, primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.UUID, db.ForeignKey("users.id", ondelete="CASCADE"))
    flight_id = db.Column(db.UUID, db.ForeignKey("flights.id", ondelete="CASCADE"))
    total_price = db.Column(Decimal(8, 2), nullable=False)
    booking_status = db.Column(Enum(BookingStatus), nullable=False, default=BookingStatus.booked)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User", back_populates="bookings")
    flight = db.relationship("Flight", back_populates="bookings")
    tickets = db.relationship("Ticket", back_populates="booking", lazy=True, cascade="all, delete-orphan")

class SeatClass(enum.Enum):
    economy = 1
    business = 2
    first = 3

class Ticket(db.Model):
    __tablename__ = "tickets"

    id = db.Column(db.UUID, primary_key=True, default=uuid.uuid4)
    booking_id = db.Column(db.UUID, db.ForeignKey("bookings.id", ondelete="CASCADE"))
    passenger_name = db.Column(db.String(50), nullable=False)
    passenger_passport_num = db.Column(db.String(12), nullable=False)
    seat_num = db.Column(db.String(4), nullable=False)
    flight_id = db.Column(db.UUID, db.ForeignKey("flights.id", ondelete="CASCADE"))
    price = db.Column(Decimal(8, 2), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    seat_class = db.Column(Enum(SeatClass), nullable=False, default=SeatClass.economy)

    flight = db.relationship("Flight", back_populates="tickets")
    booking = db.relationship("Booking", back_populates="tickets")

    def serialize(self):
        return {
            "booking_id" : self.booking_id,
            "passenger_name" : self.passenger_name,
            "passenger_passport_num" : self.passenger_passport_num,
            "seat_num" : self.seat_num,
            "seat_class" : self.seat_class,
            "flight_id" : self.flight_id,
            "price" : self.price,
            "created_at" : self.created_at,
            "updated_at" : self.updated_at
        }

    def deserialize(self, doc):
        self.booking_id = doc["booking_id"]
        self.passenger_name = doc["passenger_name"]
        self.passenger_passport_num = doc["passenger_passport_num"]
        self.seat_num = doc["seat_num"]
        self.seat_class = doc["seat_class"]
        self.flight_id = doc["flight_id"]
        self.price = doc["price"]
        self.created_at = doc["created_at"]
        self.updated_at = doc["updated_at"]

    @staticmethod
    def json_schema():
        schema = {
            "type" : object,
            "required" : [
                "booking_id",
                "passenger_name",
                "passenger_passport_num",
                "seat_num",
                "seat_class",
                "flight_id",
                "price",
                "created_at",
                "updated_at"
            ],
        }
        props = schema["properties"] = {}
        props["booking_id"] = {
            "description" : "booking id of the ticket",
            "type" : "string"
        }
        props["passenger_name"] = {
            "description" : "name of the passenger",
            "type" : "string"
        }
        props["passenger_passport_num"] = {
            "description" : "passport number of the passenger",
            "type" : "string"
        }
        props["seat_num"] = {
            "description" : "seat number assigned to the ticket",
            "type" : "string"
        }
        props["seat_class"] = {
            "description" : "class of the seat (economy, business, first)",
            "type" : "string"
        }
        props["flight_id"] = {
            "description" : "flight id associated with the ticket",
            "type" : "string"
        }
        props["price"] = {
            "description" : "price of the ticket",
            "type" : "number"
        }
        props["created_at"] = {
            "description" : "timestamp when the ticket was created",
            "type" : "string"
        }
        props["updated_at"] = {
            "description" : "timestamp when the ticket was last updated",
            "type" : "string"
        }
        return schema
