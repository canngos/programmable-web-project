
from datetime import datetime
from app import db
import uuid
import enum
from sqlalchemy import Enum
from sqlalchemy import DECIMAL as Decimal

class Roles(enum.Enum):
    admin = 1
    user = 2

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.UUID, primary_key=True, default=uuid.uuid4)
    firstname = db.Column(db.String(30), nullable=False)
    lastname = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(30), nullable=False, unique=True)
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
