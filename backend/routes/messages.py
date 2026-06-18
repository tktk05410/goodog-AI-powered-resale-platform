from flask import Blueprint, request, jsonify, g

from models import db, Message, User
from app import log_action, token_required

bp = Blueprint('messages', __name__)

@bp.route('/', methods=['GET'])
@token_required
def get_messages():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    with_user = request.args.get('with_user', type=int)

    query = Message.query.filter(
        (Message.from_user == g.user.id) | (Message.to_user == g.user.id)
    )

    if with_user:
        query = query.filter(
            (Message.from_user == g.user.id) & (Message.to_user == with_user) |
            (Message.from_user == with_user) & (Message.to_user == g.user.id)
        )

    pagination = query.order_by(Message.create_time.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'messages': [m.to_dict() for m in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    })

@bp.route('/conversations', methods=['GET'])
@token_required
def get_conversations():
    messages = Message.query.filter(
        (Message.from_user == g.user.id) | (Message.to_user == g.user.id)
    ).order_by(Message.create_time.desc()).all()

    user_ids = set()
    for msg in messages:
        other_user_id = msg.to_user if msg.from_user == g.user.id else msg.from_user
        user_ids.add(other_user_id)

    users = {user.id: user for user in User.query.filter(User.id.in_(user_ids)).all()}

    conversation_dict = {}
    for msg in messages:
        other_user_id = msg.to_user if msg.from_user == g.user.id else msg.from_user
        if other_user_id not in conversation_dict:
            other_user = users.get(other_user_id)
            username = other_user.username if other_user else f'用户{other_user_id}'
            conversation_dict[other_user_id] = {
                'user_id': other_user_id,
                'username': username,
                'last_message': msg.to_dict(),
                'unread_count': 0
            }

        if msg.to_user == g.user.id and not msg.is_read:
            conversation_dict[other_user_id]['unread_count'] += 1

    conversations = list(conversation_dict.values())

    return jsonify({'conversations': conversations})

@bp.route('/', methods=['POST'])
@token_required
def send_message():
    data = request.get_json()

    to_user_id = data.get('to_user')
    content = data.get('content')

    if not to_user_id or not content:
        return jsonify({'error': 'to_user and content are required'}), 400

    if to_user_id == g.user.id:
        return jsonify({'error': 'Cannot send message to yourself'}), 400

    message = Message(
        from_user=g.user.id,
        to_user=to_user_id,
        content=content
    )

    db.session.add(message)
    db.session.commit()

    log_action('MESSAGE_SEND', {
        'message_id': message.id,
        'to_user': to_user_id
    })

    return jsonify({
        'message': 'Message sent successfully',
        'data': message.to_dict()
    }), 201

@bp.route('/<int:message_id>/read', methods=['PUT'])
@token_required
def mark_as_read(message_id):
    message = Message.query.get_or_404(message_id)

    if message.to_user != g.user.id:
        return jsonify({'error': 'Access denied'}), 403

    message.is_read = True
    db.session.commit()

    return jsonify({
        'message': 'Message marked as read',
        'data': message.to_dict()
    })

@bp.route('/read-all/<int:from_user_id>', methods=['PUT'])
@token_required
def mark_all_as_read(from_user_id):
    Message.query.filter(
        Message.from_user == from_user_id,
        Message.to_user == g.user.id,
        Message.is_read == False
    ).update({'is_read': True})

    db.session.commit()

    return jsonify({'message': 'All messages marked as read'})

@bp.route('/unread-count', methods=['GET'])
@token_required
def get_unread_count():
    count = Message.query.filter(
        Message.to_user == g.user.id,
        Message.is_read == False
    ).count()

    return jsonify({'unread_count': count})