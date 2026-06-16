from flask import Blueprint, request, jsonify, g
from functools import wraps

from models import db, User, Product, SystemLog, Message
from app import token_required

bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not g.user:
            return jsonify({'error': 'Authentication required'}), 401
        if g.user.role != 'admin':
            return jsonify({'error': 'Admin permission required'}), 403
        return f(*args, **kwargs)
    return decorated

@bp.route('/stats', methods=['GET'])
@token_required
@admin_required
def get_stats():
    total_users = User.query.count()
    total_products = Product.query.count()
    total_messages = Message.query.count()
    online_products = Product.query.filter_by(status='on').count()
    sold_products = Product.query.filter_by(status='sold').count()

    return jsonify({
        'total_users': total_users,
        'total_products': total_products,
        'total_messages': total_messages,
        'online_products': online_products,
        'sold_products': sold_products
    })

@bp.route('/users', methods=['GET'])
@token_required
@admin_required
def get_users():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    pagination = User.query.order_by(User.create_time.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'users': [u.to_dict() for u in pagination.items],
        'total': pagination.total,
        'page': page,
        'pages': pagination.pages
    })

@bp.route('/users/<int:user_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == 'admin':
        return jsonify({'error': 'Cannot delete admin user'}), 400

    # 先删除用户关联的商品标签、商品等
    # 这里简化处理，直接删除（数据库外键约束可能报错，实际应设计级联删除）
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted successfully'})

@bp.route('/products', methods=['GET'])
@token_required
@admin_required
def get_all_products():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status_filter = request.args.get('status')

    query = Product.query
    if status_filter:
        query = query.filter(Product.status == status_filter)

    pagination = query.order_by(Product.create_time.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'products': [p.to_dict() for p in pagination.items],
        'total': pagination.total,
        'page': page,
        'pages': pagination.pages
    })

@bp.route('/logs', methods=['GET'])
@token_required
@admin_required
def get_logs():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    pagination = SystemLog.query.order_by(SystemLog.timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'logs': [l.to_dict() for l in pagination.items],
        'total': pagination.total,
        'page': page,
        'pages': pagination.pages
    })
