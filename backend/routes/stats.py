from flask import Blueprint, request, jsonify
from sqlalchemy import func, text
from datetime import datetime, timedelta

from models import db, Product, Transaction, User, Message, SystemLog, ProductTag, Tag
from app import token_required

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'ai_services'))
from text_classifier import CATEGORY_KEYWORDS

bp = Blueprint('stats', __name__)

@bp.route('/overview', methods=['GET'])
def get_overview():
    total_users = User.query.count()
    total_products = Product.query.count()
    active_products = Product.query.filter_by(status='on').count()
    total_transactions = Transaction.query.count()
    completed_transactions = Transaction.query.filter_by(state='done').count()

    return jsonify({
        'total_users': total_users,
        'total_products': total_products,
        'active_products': active_products,
        'total_transactions': total_transactions,
        'completed_transactions': completed_transactions,
        'completion_rate': round(completed_transactions / total_transactions * 100, 2) if total_transactions > 0 else 0
    })

@bp.route('/category-distribution', methods=['GET'])
def get_category_distribution():
    products = Product.query.all()
    category_counts = {name: 0 for name in CATEGORY_KEYWORDS}
    category_counts['其他'] = 0

    # 预先加载所有商品的标签，避免N+1查询
    product_tags_map = {}
    for pt in ProductTag.query.all():
        product_tags_map.setdefault(pt.product_id, []).append(pt.tag_id)

    # 预加载所有标签名称
    tag_names = {t.id: t.name for t in Tag.query.all()}

    for product in products:
        matched = False
        tag_ids = product_tags_map.get(product.id, [])

        # 完全按照标签中的大类名称来匹配
        for tag_id in tag_ids:
            tag_name = tag_names.get(tag_id, '')
            if tag_name in CATEGORY_KEYWORDS:
                category_counts[tag_name] += 1
                matched = True
                break

        if not matched:
            category_counts['其他'] += 1

    distribution = [
        {'name': name, 'value': count}
        for name, count in category_counts.items()
        if count > 0
    ]

    return jsonify({'distribution': distribution})

@bp.route('/product-status', methods=['GET'])
def get_product_status():
    on_count = Product.query.filter_by(status='on').count()
    off_count = Product.query.filter_by(status='off').count()
    sold_count = Product.query.filter_by(status='sold').count()

    return jsonify({
        'distribution': [
            {'name': '上架中', 'value': on_count},
            {'name': '已下架', 'value': off_count},
            {'name': '已售出', 'value': sold_count}
        ]
    })

@bp.route('/transaction-states', methods=['GET'])
def get_transaction_states():
    pending = Transaction.query.filter_by(state='pending').count()
    paid = Transaction.query.filter_by(state='paid').count()
    done = Transaction.query.filter_by(state='done').count()
    canceled = Transaction.query.filter_by(state='canceled').count()

    return jsonify({
        'distribution': [
            {'name': '待付款', 'value': pending},
            {'name': '已付款', 'value': paid},
            {'name': '已完成', 'value': done},
            {'name': '已取消', 'value': canceled}
        ]
    })

@bp.route('/daily-transactions', methods=['GET'])
def get_daily_transactions():
    days = request.args.get('days', 7, type=int)

    start_date = datetime.utcnow() - timedelta(days=days)

    results = db.session.query(
        func.date(Transaction.create_time).label('date'),
        func.count(Transaction.id).label('count')
    ).filter(
        Transaction.create_time >= start_date
    ).group_by(
        func.date(Transaction.create_time)
    ).all()

    return jsonify({
        'data': [
            {'date': str(r.date), 'count': r.count}
            for r in results
        ]
    })

@bp.route('/hourly-activity', methods=['GET'])
def get_hourly_activity():
    """统计用户活跃时段（按东八区时间）"""
    # 数据库中create_time为UTC时间，查询时+8小时转换为中国本地时间
    messages = db.session.query(
        func.hour(func.date_add(Message.create_time, text("INTERVAL 8 HOUR"))).label('hour'),
        func.count(Message.id).label('count')
    ).group_by(
        func.hour(func.date_add(Message.create_time, text("INTERVAL 8 HOUR")))
    ).all()

    activity_by_hour = {i: 0 for i in range(24)}
    for hour, count in messages:
        # 确保hour在0-23范围内
        hour = int(hour) % 24
        activity_by_hour[hour] = count

    return jsonify({
        'data': [
            {'hour': hour, 'count': count}
            for hour, count in activity_by_hour.items()
        ]
    })

@bp.route('/top-products', methods=['GET'])
def get_top_products():
    limit = request.args.get('limit', 10, type=int)

    products = Product.query.order_by(Product.create_time.desc()).limit(limit).all()

    return jsonify({
        'products': [p.to_dict() for p in products]
    })

@bp.route('/active-users', methods=['GET'])
def get_active_users():
    days = request.args.get('days', 7, type=int)
    limit = request.args.get('limit', 10, type=int)

    start_date = datetime.utcnow() - timedelta(days=days)

    active_users = db.session.query(
        SystemLog.user_id,
        func.count(SystemLog.log_id).label('action_count')
    ).filter(
        SystemLog.timestamp >= start_date,
        SystemLog.user_id.isnot(None)
    ).group_by(
        SystemLog.user_id
    ).order_by(
        func.count(SystemLog.log_id).desc()
    ).limit(limit).all()

    results = []
    for user_id, action_count in active_users:
        user = User.query.get(user_id)
        if user:
            results.append({
                'user_id': user_id,
                'username': user.username,
                'action_count': action_count
            })

    return jsonify({'users': results})