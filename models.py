# models.py
from datetime import datetime
from app import db

class User(db.Model):
    __tablename__ = 'users'  # Explicit table name (good practice)
    
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(30), nullable=False)
    lastname = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(30), nullable=False)
    password_hash = db.Column(db.String(30), nullable=False)
    role = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Define relationship - note the string reference and class name
    bookings = db.relationship("Booking", back_populates="user", lazy=True)

class Booking(db.Model):
    __tablename__ = 'bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))  # Note: users.id not user.id
    # flight_id = db.Column(db.Integer, db.ForeignKey())    # Commented because flight table has not been created yet
    total_price = db.Column(db.Float, nullable=False)
    booking_status = db.Column(db.String(15), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Define relationship
    user = db.relationship("User", back_populates="bookings")