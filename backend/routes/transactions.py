from flask import Blueprint, request, jsonify, g

from models import db, Transaction, Product
from app import log_action, token_required

bp = Blueprint('transactions', __name__)

@bp.route('/', methods=['GET'])
@token_required
def get_transactions():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    role = request.args.get('role')
    state = request.args.get('state')

    query = Transaction.query

    if role == 'buyer':
        query = query.filter(Transaction.buyer_id == g.user.id)
    elif role == 'seller':
        query = query.filter(Transaction.seller_id == g.user.id)
    else:
        query = query.filter(
            (Transaction.buyer_id == g.user.id) | (Transaction.seller_id == g.user.id)
        )

    if state:
        query = query.filter(Transaction.state == state)

    pagination = query.order_by(Transaction.create_time.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    transactions = []
    for t in pagination.items:
        t_dict = t.to_dict()
        t_dict['product'] = t.product.to_dict() if t.product else None
        t_dict['buyer'] = t.buyer.to_dict() if t.buyer else None
        t_dict['seller'] = t.seller.to_dict() if t.seller else None
        transactions.append(t_dict)

    return jsonify({
        'transactions': transactions,
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    })

@bp.route('/<int:transaction_id>', methods=['GET'])
@token_required
def get_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)

    if transaction.buyer_id != g.user.id and transaction.seller_id != g.user.id:
        return jsonify({'error': 'Access denied'}), 403

    t_dict = transaction.to_dict()
    t_dict['product'] = transaction.product.to_dict() if transaction.product else None
    t_dict['buyer'] = transaction.buyer.to_dict() if transaction.buyer else None
    t_dict['seller'] = transaction.seller.to_dict() if transaction.seller else None

    return jsonify({'transaction': t_dict})

@bp.route('/', methods=['POST'])
@token_required
def create_transaction():
    data = request.get_json()

    product_id = data.get('product_id')
    if not product_id:
        return jsonify({'error': 'Product ID is required'}), 400

    product = Product.query.get_or_404(product_id)

    if product.user_id == g.user.id:
        return jsonify({'error': 'You cannot buy your own product'}), 400

    if product.status != 'on':
        return jsonify({'error': 'Product is not available'}), 400

    existing = Transaction.query.filter_by(
        product_id=product_id,
        buyer_id=g.user.id
    ).filter(Transaction.state.in_(['pending', 'paid'])).first()

    if existing:
        return jsonify({'error': 'You already have a pending transaction for this product'}), 400

    transaction = Transaction(
        product_id=product_id,
        buyer_id=g.user.id,
        seller_id=product.user_id
    )

    db.session.add(transaction)
    db.session.commit()

    log_action('TRANSACTION_CREATE', {
        'transaction_id': transaction.id,
        'product_id': product_id
    })

    return jsonify({
        'message': 'Transaction created successfully',
        'transaction': transaction.to_dict()
    }), 201

@bp.route('/<int:transaction_id>/pay', methods=['POST'])
@token_required
def pay_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)

    if transaction.buyer_id != g.user.id:
        return jsonify({'error': 'Only buyer can pay'}), 403

    if transaction.state != 'pending':
        return jsonify({'error': 'Transaction cannot be paid in current state'}), 400

    transaction.state = 'paid'
    db.session.commit()

    log_action('TRANSACTION_PAY', {'transaction_id': transaction_id})

    return jsonify({
        'message': 'Payment successful',
        'transaction': transaction.to_dict()
    })

@bp.route('/<int:transaction_id>/confirm', methods=['POST'])
@token_required
def confirm_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)

    if transaction.seller_id != g.user.id:
        return jsonify({'error': 'Only seller can confirm'}), 403

    if transaction.state != 'paid':
        return jsonify({'error': 'Transaction must be paid first'}), 400

    transaction.state = 'done'
    transaction.product.status = 'sold'
    db.session.commit()

    log_action('TRANSACTION_CONFIRM', {'transaction_id': transaction_id})

    return jsonify({
        'message': 'Transaction completed successfully',
        'transaction': transaction.to_dict()
    })

@bp.route('/<int:transaction_id>/cancel', methods=['POST'])
@token_required
def cancel_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)

    if transaction.buyer_id != g.user.id and transaction.seller_id != g.user.id:
        return jsonify({'error': 'Access denied'}), 403

    if transaction.state in ['done', 'canceled']:
        return jsonify({'error': 'Transaction cannot be canceled in current state'}), 400

    transaction.state = 'canceled'
    db.session.commit()

    log_action('TRANSACTION_CANCEL', {'transaction_id': transaction_id})

    return jsonify({
        'message': 'Transaction canceled',
        'transaction': transaction.to_dict()
    })