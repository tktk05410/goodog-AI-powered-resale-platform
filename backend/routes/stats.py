from flask import Blueprint, request, jsonify
from sqlalchemy import func, text
from datetime import datetime, timedelta
import os
import requests
import json

from models import db, Product, Transaction, User, Message, SystemLog, ProductTag, Tag, TrendAnalysis
from app import token_required, log_action

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'ai_services'))
from text_classifier import CATEGORY_KEYWORDS

def _call_qwen_for_trend(prompt_content):
    api_key = os.environ.get('QWEN_API_KEY', '')
    base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    if not api_key:
        return None
    try:
        url = f"{base_url}/chat/completions"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }
        data = {
            'model': 'qwen3.7-plus',
            'messages': [
                {
                    'role': 'system',
                    'content': '你是电商平台数据分析师。根据平台统计数据生成一段约150字的趋势分析，语言简洁专业，纯文本输出，不要加标题、序号、换行和markdown格式。'
                },
                {
                    'role': 'user',
                    'content': prompt_content
                }
            ],
            'temperature': 0.7,
            'max_tokens': 300
        }
        response = requests.post(url, json=data, headers=headers, timeout=60)
        result = response.json()
        if 'choices' in result and len(result['choices']) > 0:
            return result['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f'Qwen trend analysis error: {e}')
    return None

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


@bp.route('/trend-analysis', methods=['GET'])
def get_trend_analysis():
    """根据平台数据调用AI模型生成趋势分析，按月缓存"""
    now = datetime.utcnow()
    current_month = now.strftime('%Y-%m')

    # 1. 检查本月是否已有分析结果
    cached = TrendAnalysis.query.filter_by(year_month=current_month).first()
    if cached:
        return jsonify({'analysis': cached.analysis, 'cached': True, 'month': current_month})

    # 2. 成交量数据（最近7天）
    days = 7
    start_date = now - timedelta(days=days)
    daily_results = db.session.query(
        func.date(Transaction.create_time).label('date'),
        func.count(Transaction.id).label('count')
    ).filter(
        Transaction.create_time >= start_date
    ).group_by(
        func.date(Transaction.create_time)
    ).all()
    total_tx_week = sum(r.count for r in daily_results)

    # 3. 交易完成率
    total_transactions = Transaction.query.count()
    completed_transactions = Transaction.query.filter_by(state='done').count()
    completion_rate = round(completed_transactions / total_transactions * 100, 2) if total_transactions > 0 else 0

    # 4. 商品类别分布Top3
    products = Product.query.all()
    product_tags_map = {}
    for pt in ProductTag.query.all():
        product_tags_map.setdefault(pt.product_id, []).append(pt.tag_id)
    tag_names = {t.id: t.name for t in Tag.query.all()}
    category_counts = {name: 0 for name in CATEGORY_KEYWORDS}
    category_counts['其他'] = 0
    for product in products:
        matched = False
        for tag_id in product_tags_map.get(product.id, []):
            tag_name = tag_names.get(tag_id, '')
            if tag_name in CATEGORY_KEYWORDS:
                category_counts[tag_name] += 1
                matched = True
                break
        if not matched:
            category_counts['其他'] += 1
    top_categories = sorted(
        [{'name': k, 'value': v} for k, v in category_counts.items() if v > 0],
        key=lambda x: x['value'],
        reverse=True
    )[:3]

    # 5. 商品状态
    on_count = Product.query.filter_by(status='on').count()
    sold_count = Product.query.filter_by(status='sold').count()
    off_count = Product.query.filter_by(status='off').count()

    # 6. 用户活跃时段Top3
    messages = db.session.query(
        func.hour(func.date_add(Message.create_time, text("INTERVAL 8 HOUR"))).label('hour'),
        func.count(Message.id).label('count')
    ).group_by(
        func.hour(func.date_add(Message.create_time, text("INTERVAL 8 HOUR")))
    ).all()
    hourly_activity = {int(hour) % 24: count for hour, count in messages}
    top_hours = sorted(
        [{'hour': h, 'count': c} for h, c in hourly_activity.items() if c > 0],
        key=lambda x: x['count'],
        reverse=True
    )[:3]

    category_str = ', '.join(['{}({}件)'.format(c['name'], c['value']) for c in top_categories])
    hour_str = ', '.join(['{}:00({}次)'.format(h['hour'], h['count']) for h in top_hours])

    prompt = (
        "平台最近7天共产生{}笔交易，整体交易完成率为{}%。".format(total_tx_week, completion_rate) +
        "商品类别前三名：{}。".format(category_str) +
        "当前商品状态：上架中{}件、已售出{}件、已下架{}件。".format(on_count, sold_count, off_count) +
        "用户活跃高峰时段：{}。".format(hour_str) +
        "请基于以上数据生成一段约150字的运营趋势分析。"
    )

    analysis = _call_qwen_for_trend(prompt)
    source = 'ai'
    if analysis is None:
        # 兜底：没有API key时生成固定模板
        source = 'fallback'
        top_cat_names = '、'.join([c['name'] for c in top_categories])
        top_hour_names = '、'.join(['{}:00'.format(h['hour']) for h in top_hours])
        analysis = (
            "近7天平台交易活跃，累计成交{}笔，整体完成率{}%。".format(total_tx_week, completion_rate) +
            "从品类看，{}为主要流通类目。".format(top_cat_names) +
            "用户活跃集中在{}等时段，".format(top_hour_names) +
            "建议运营方在高峰时段加强商品推荐与促销活动，以提升转化效率。"
        )

    # 7. 保存本月分析结果
    try:
        new_analysis = TrendAnalysis(
            year_month=current_month,
            analysis=analysis,
            source=source
        )
        db.session.add(new_analysis)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f'Save trend analysis error: {e}')

    log_action('STATS_TREND_ANALYSIS', {'length': len(analysis), 'month': current_month, 'source': source})

    return jsonify({'analysis': analysis, 'cached': False, 'month': current_month})