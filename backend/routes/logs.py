from flask import Blueprint, request, jsonify, g

from models import db, SystemLog
from app import log_action, token_required

bp = Blueprint('logs', __name__)

@bp.route('/', methods=['GET'])
@token_required
def get_logs():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    action = request.args.get('action')
    user_id = request.args.get('user_id', type=int)

    query = SystemLog.query

    if action:
        query = query.filter(SystemLog.action == action)

    if user_id:
        query = query.filter(SystemLog.user_id == user_id)

    pagination = query.order_by(SystemLog.timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'logs': [log.to_dict() for log in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    })

@bp.route('/actions', methods=['GET'])
def get_distinct_actions():
    actions = db.session.query(SystemLog.action).distinct().all()

    return jsonify({
        'actions': [a[0] for a in actions]
    })

@bp.route('/user/<int:user_id>', methods=['GET'])
@token_required
def get_user_logs(user_id):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    pagination = SystemLog.query.filter_by(user_id=user_id).order_by(
        SystemLog.timestamp.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'logs': [log.to_dict() for log in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    })