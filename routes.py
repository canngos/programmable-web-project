# routes.py
from flask import Blueprint, jsonify, request
from models import db, User, Booking
from datetime import datetime

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return jsonify({
        'message': 'Flask PostgreSQL API',
        'endpoints': {
            'users': '/users/',
            'bookings': '/bookings/'
        }
    })

@main_bp.route('/users/', methods=['GET', 'POST'])
def sensors():
    if request.method == 'POST':
        data = request.json
        user = User(
            firstname=data['firstname'],
            lastname=data['lastname'],
            password_hash=data['password_hash'],
            email=data['email'],
            role=data['role'],
            created_at=data['created_at']
        )
        db.session.add(user)
        db.session.commit()
        return jsonify({'message': 'User created', 'id': user.id}), 201
    
    users = User.query.all()
    return jsonify([{
        'id': s.id,
        'firstname': s.firstname,
        'lastname': s.lastname,
        'email': s.email,
        'role' : s.role,
        'created_at' : s.created_at
    } for s in users])

