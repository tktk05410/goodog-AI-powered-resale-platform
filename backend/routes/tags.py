from flask import Blueprint, request, jsonify, g
from sqlalchemy import or_

from models import db, Tag, ProductTag, Product
from app import log_action, token_required

bp = Blueprint('tags', __name__)

@bp.route('/', methods=['GET'])
def get_tags():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    keyword = request.args.get('keyword')

    query = Tag.query

    if keyword:
        query = query.filter(Tag.name.like(f'%{keyword}%'))

    pagination = query.order_by(Tag.create_time.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'tags': [t.to_dict() for t in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    })

@bp.route('/<int:tag_id>', methods=['GET'])
def get_tag(tag_id):
    tag = Tag.query.get_or_404(tag_id)
    return jsonify({'tag': tag.to_dict()})

@bp.route('/', methods=['POST'])
@token_required
def create_tag():
    data = request.get_json()
    name = data.get('name')
    color = data.get('color', '#409eff')

    if not name:
        return jsonify({'error': 'Tag name is required'}), 400

    existing = Tag.query.filter_by(name=name).first()
    if existing:
        return jsonify({'error': 'Tag already exists', 'tag': existing.to_dict()}), 400

    tag = Tag(name=name, color=color)
    db.session.add(tag)
    db.session.commit()

    log_action('TAG_CREATE', {'tag_id': tag.id, 'name': name})

    return jsonify({
        'message': 'Tag created successfully',
        'tag': tag.to_dict()
    }), 201

@bp.route('/<int:tag_id>', methods=['PUT'])
@token_required
def update_tag(tag_id):
    tag = Tag.query.get_or_404(tag_id)

    data = request.get_json()
    name = data.get('name')
    color = data.get('color')

    if name and name != tag.name:
        existing = Tag.query.filter_by(name=name).first()
        if existing and existing.id != tag_id:
            return jsonify({'error': 'Tag name already exists'}), 400
        tag.name = name

    if color:
        tag.color = color

    db.session.commit()

    log_action('TAG_UPDATE', {'tag_id': tag_id})

    return jsonify({
        'message': 'Tag updated successfully',
        'tag': tag.to_dict()
    })

@bp.route('/<int:tag_id>', methods=['DELETE'])
@token_required
def delete_tag(tag_id):
    tag = Tag.query.get_or_404(tag_id)

    ProductTag.query.filter_by(tag_id=tag_id).delete()
    db.session.delete(tag)
    db.session.commit()

    log_action('TAG_DELETE', {'tag_id': tag_id})

    return jsonify({'message': 'Tag deleted successfully'})

@bp.route('/products/<int:product_id>', methods=['GET'])
def get_product_tags(product_id):
    product = Product.query.get_or_404(product_id)
    product_tags = ProductTag.query.filter_by(product_id=product_id).all()
    return jsonify({
        'tags': [pt.to_dict() for pt in product_tags]
    })

@bp.route('/products/<int:product_id>', methods=['POST'])
@token_required
def add_product_tag(product_id):
    product = Product.query.get_or_404(product_id)

    if product.user_id != g.user.id:
        return jsonify({'error': 'You can only manage tags for your own products'}), 403

    data = request.get_json()
    tag_id = data.get('tag_id')
    tag_name = data.get('tag_name')

    if tag_id:
        tag = Tag.query.get_or_404(tag_id)
    elif tag_name:
        tag = Tag.query.filter_by(name=tag_name).first()
        if not tag:
            tag = Tag(name=tag_name, color='#409eff')
            db.session.add(tag)
            db.session.flush()
    else:
        return jsonify({'error': 'tag_id or tag_name is required'}), 400

    existing = ProductTag.query.filter_by(product_id=product_id, tag_id=tag.id).first()
    if existing:
        return jsonify({'error': 'Tag already added to this product'}), 400

    product_tag = ProductTag(product_id=product_id, tag_id=tag.id, is_ai_generated=False)
    db.session.add(product_tag)
    db.session.commit()

    log_action('PRODUCT_TAG_ADD', {'product_id': product_id, 'tag_id': tag.id})

    return jsonify({
        'message': 'Tag added successfully',
        'product_tag': product_tag.to_dict()
    }), 201

@bp.route('/products/<int:product_id>/tags/<int:tag_id>', methods=['DELETE'])
@token_required
def remove_product_tag(product_id, tag_id):
    product = Product.query.get_or_404(product_id)

    if product.user_id != g.user.id:
        return jsonify({'error': 'You can only manage tags for your own products'}), 403

    product_tag = ProductTag.query.filter_by(product_id=product_id, tag_id=tag_id).first_or_404()

    db.session.delete(product_tag)
    db.session.commit()

    log_action('PRODUCT_TAG_REMOVE', {'product_id': product_id, 'tag_id': tag_id})

    return jsonify({'message': 'Tag removed successfully'})

@bp.route('/products/<int:product_id>/tags', methods=['PUT'])
@token_required
def update_product_tags(product_id):
    product = Product.query.get_or_404(product_id)

    if product.user_id != g.user.id:
        return jsonify({'error': 'You can only manage tags for your own products'}), 403

    data = request.get_json()
    tag_ids = data.get('tag_ids', [])

    ProductTag.query.filter_by(product_id=product_id).delete()

    for tag_id in tag_ids:
        tag = Tag.query.get(tag_id)
        if tag:
            product_tag = ProductTag(product_id=product_id, tag_id=tag_id, is_ai_generated=False)
            db.session.add(product_tag)

    db.session.commit()

    log_action('PRODUCT_TAGS_UPDATE', {'product_id': product_id, 'tag_ids': tag_ids})

    product_tags = ProductTag.query.filter_by(product_id=product_id).all()
    return jsonify({
        'message': 'Tags updated successfully',
        'tags': [pt.to_dict() for pt in product_tags]
    })
