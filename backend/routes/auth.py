from flask import Blueprint, request, jsonify, g
import bcrypt
import jwt
from datetime import datetime, timedelta
from flask import current_app

from models import db, User
from app import log_action

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password are required'}), 400

    username = data['username']
    password = data['password']
    student_id = data.get('student_id')

    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 409

    if student_id and User.query.filter_by(student_id=student_id).first():
        return jsonify({'error': 'Student ID already registered'}), 409

    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    user = User(
        username=username,
        password_hash=password_hash,
        student_id=student_id
    )

    db.session.add(user)
    db.session.commit()

    log_action('USER_REGISTER', {'username': username})

    token = generate_token(user.id)

    return jsonify({
        'message': 'User registered successfully',
        'token': token,
        'user': user.to_dict()
    }), 201

@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password are required'}), 400

    username = data['username']
    password = data['password']

    user = User.query.filter_by(username=username).first()

    if not user or not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
        return jsonify({'error': 'Invalid username or password'}), 401

    log_action('USER_LOGIN', {'username': username})

    token = generate_token(user.id)

    return jsonify({
        'message': 'Login successful',
        'token': token,
        'user': user.to_dict()
    })

@bp.route('/me', methods=['GET'])
def get_current_user():
    auth_header = request.headers.get('Authorization')

    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Token is missing'}), 401

    token = auth_header.split(' ')[1]

    try:
        payload = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        user = User.query.get(payload['user_id'])

        if not user:
            return jsonify({'error': 'User not found'}), 404

        return jsonify({'user': user.to_dict()})

    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401

@bp.route('/change-password', methods=['POST'])
def change_password():
    data = request.get_json()

    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Token is missing'}), 401

    token = auth_header.split(' ')[1]

    try:
        payload = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        user = User.query.get(payload['user_id'])

        if not user:
            return jsonify({'error': 'User not found'}), 404

        old_password = data.get('old_password')
        new_password = data.get('new_password')

        if not bcrypt.checkpw(old_password.encode('utf-8'), user.password_hash.encode('utf-8')):
            return jsonify({'error': 'Old password is incorrect'}), 401

        user.password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        db.session.commit()

        log_action('PASSWORD_CHANGE', {'user_id': user.id})

        return jsonify({'message': 'Password changed successfully'})

    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401

def generate_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(seconds=86400),
        'iat': datetime.utcnow()
    }
    token = jwt.encode(payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')
    return token