from flask import Blueprint, request, jsonify, g

from models import db, User
from app import log_action, token_required

bp = Blueprint('users', __name__)

@bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({
        'user': {
            'id': user.id,
            'username': user.username,
            'student_id': user.student_id,
            'credit_score': user.credit_score,
            'create_time': user.create_time.strftime('%Y-%m-%d %H:%M:%S') if user.create_time else None
        }
    })

@bp.route('/profile', methods=['GET'])
@token_required
def get_profile():
    return jsonify({'user': g.user.to_dict()})

@bp.route('/profile', methods=['PUT'])
@token_required
def update_profile():
    data = request.get_json()

    if data.get('student_id'):
        existing = User.query.filter(
            User.student_id == data['student_id'],
            User.id != g.user.id
        ).first()
        if existing:
            return jsonify({'error': 'Student ID already in use'}), 400
        g.user.student_id = data['student_id']

    db.session.commit()

    log_action('PROFILE_UPDATE', {'user_id': g.user.id})

    return jsonify({
        'message': 'Profile updated successfully',
        'user': g.user.to_dict()
    })

@bp.route('/credit-score/<int:user_id>', methods=['GET'])
def get_credit_score(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({
        'user_id': user.id,
        'username': user.username,
        'credit_score': user.credit_score
    })

@bp.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    limit = request.args.get('limit', 10, type=int)
    users = User.query.order_by(User.credit_score.desc()).limit(limit).all()

    return jsonify({
        'leaderboard': [
            {
                'rank': idx + 1,
                'user_id': u.id,
                'username': u.username,
                'credit_score': u.credit_score
            }
            for idx, u in enumerate(users)
        ]
    })