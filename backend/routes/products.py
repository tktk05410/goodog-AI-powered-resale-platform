from flask import Blueprint, request, jsonify, g, current_app
from sqlalchemy import or_

from models import db, Product, Tag, ProductTag, Transaction
from app import log_action, token_required, allowed_file, save_uploaded_file

bp = Blueprint('products', __name__)

def auto_generate_tags(product):
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from ai_services.text_classifier import TextClassifier
    from ai_services.image_processor import ImageProcessor

    text_tags = []
    image_tags = []

    try:
        classifier = TextClassifier()
        text_result = classifier.generate_tags_with_qwen(product.title, product.description)
        text_tags = text_result.get('tags', [])
    except Exception as e:
        print(f'Text tag generation error: {e}')

    if product.image_path:
        try:
            image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], product.image_path)
            if os.path.exists(image_path):
                classifier = TextClassifier()
                image_result = ImageProcessor.recognize_with_qwen(
                    image_path,
                    classifier.api_key,
                    classifier.base_url
                )
                image_tags = image_result.get('tags', [])
        except Exception as e:
            print(f'Image tag generation error: {e}')

    category = text_tags[0] if text_tags else None
    all_tags = text_tags + [t for t in image_tags if t not in text_tags]
    if category and all_tags and all_tags[0] != category:
        all_tags = [category] + [t for t in all_tags if t != category]
    all_tags = all_tags[:8]

    for tag_name in all_tags:
        tag = Tag.query.filter_by(name=tag_name).first()
        if not tag:
            tag = Tag(name=tag_name, color='#409eff', is_ai_generated=True)
            db.session.add(tag)
            db.session.flush()

        existing = ProductTag.query.filter_by(product_id=product.id, tag_id=tag.id).first()
        if not existing:
            product_tag = ProductTag(
                product_id=product.id,
                tag_id=tag.id,
                is_ai_generated=True
            )
            db.session.add(product_tag)

    log_action('AI_AUTO_TAG', {
        'product_id': product.id,
        'tags': all_tags,
        'text_tags': text_tags,
        'image_tags': image_tags
    })

    return all_tags

@bp.route('/', methods=['GET'])
def get_products():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    type_filter = request.args.get('type')
    status_filter = request.args.get('status', 'on')
    keyword = request.args.get('keyword')

    query = Product.query

    if type_filter:
        query = query.filter(Product.type == type_filter)

    if status_filter:
        query = query.filter(Product.status == status_filter)

    if keyword:
        product_ids_with_tag = db.session.query(ProductTag.product_id).join(
            Tag, ProductTag.tag_id == Tag.id
        ).filter(
            Tag.name.like(f'%{keyword}%')
        ).subquery()

        query = query.filter(or_(
            Product.title.like(f'%{keyword}%'),
            Product.description.like(f'%{keyword}%'),
            Product.id.in_(product_ids_with_tag)
        ))

    pagination = query.order_by(Product.create_time.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'products': [p.to_dict() for p in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    })

@bp.route('/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get_or_404(product_id)
    return jsonify({'product': product.to_dict()})

@bp.route('/', methods=['POST'])
@token_required
def create_product():
    title = request.form.get('title')
    description = request.form.get('description')
    type_val = request.form.get('type')
    price = request.form.get('price')
    image = request.files.get('image')

    if not title or not description or not type_val:
        return jsonify({'error': 'Title, description and type are required'}), 400

    if type_val not in ['sell', 'buy']:
        return jsonify({'error': 'Type must be sell or buy'}), 400

    image_path = None
    if image:
        image_path = save_uploaded_file(image)
        if not image_path:
            return jsonify({'error': 'Invalid image file'}), 400

    product = Product(
        title=title,
        description=description,
        type=type_val,
        price=float(price) if price else None,
        image_path=image_path,
        user_id=g.user.id
    )

    db.session.add(product)
    db.session.commit()

    # Handle tags from frontend or auto-generate
    tags_json = request.form.get('tags')
    if tags_json:
        import json
        try:
            tags_data = json.loads(tags_json)
            for tag_data in tags_data:
                tag_id = tag_data.get('id')
                tag_name = tag_data.get('name')
                is_ai = tag_data.get('is_ai_generated', False)

                if tag_id:
                    existing = ProductTag.query.filter_by(product_id=product.id, tag_id=tag_id).first()
                    if not existing:
                        db.session.add(ProductTag(product_id=product.id, tag_id=tag_id, is_ai_generated=is_ai))
                elif tag_name:
                    tag = Tag.query.filter_by(name=tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name, color='#409eff', is_ai_generated=is_ai)
                        db.session.add(tag)
                        db.session.flush()
                    existing = ProductTag.query.filter_by(product_id=product.id, tag_id=tag.id).first()
                    if not existing:
                        db.session.add(ProductTag(product_id=product.id, tag_id=tag.id, is_ai_generated=is_ai))
            db.session.commit()
        except Exception as e:
            print(f'Tag creation error: {e}')
            auto_generate_tags(product)
            db.session.commit()
    else:
        auto_generate_tags(product)
        db.session.commit()

    log_action('PRODUCT_CREATE', {
        'product_id': product.id,
        'title': title,
        'type': type_val
    })

    return jsonify({
        'message': 'Product created successfully',
        'product': product.to_dict()
    }), 201

@bp.route('/<int:product_id>', methods=['PUT'])
@token_required
def update_product(product_id):
    product = Product.query.get_or_404(product_id)

    if product.user_id != g.user.id and g.user.role != 'admin':
        return jsonify({'error': 'You can only update your own products'}), 403

    title = request.form.get('title', product.title)
    description = request.form.get('description', product.description)
    price = request.form.get('price', product.price)
    status = request.form.get('status', product.status)
    tags_json = request.form.get('tags')
    image = request.files.get('image')

    product.title = title
    product.description = description
    product.price = float(price) if price else product.price
    product.status = status

    if image:
        image_path = save_uploaded_file(image)
        if image_path:
            product.image_path = image_path

    # Handle tags update
    if tags_json:
        import json
        try:
            tags_data = json.loads(tags_json)
            # tags_data is a list of {id: x, name: y} or {name: y}
            
            # Get current tag IDs
            current_product_tags = ProductTag.query.filter_by(product_id=product_id).all()
            current_tag_ids = {pt.tag_id for pt in current_product_tags}
            
            new_tag_ids = set()
            
            for tag_data in tags_data:
                tag_id = tag_data.get('id')
                tag_name = tag_data.get('name')
                
                if tag_id:
                    new_tag_ids.add(tag_id)
                    # Check if association exists
                    existing = ProductTag.query.filter_by(product_id=product_id, tag_id=tag_id).first()
                    if not existing:
                        product_tag = ProductTag(product_id=product_id, tag_id=tag_id, is_ai_generated=False)
                        db.session.add(product_tag)
                elif tag_name:
                    tag = Tag.query.filter_by(name=tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name, color='#409eff')
                        db.session.add(tag)
                        db.session.flush()
                    new_tag_ids.add(tag.id)
                    existing = ProductTag.query.filter_by(product_id=product_id, tag_id=tag.id).first()
                    if not existing:
                        product_tag = ProductTag(product_id=product_id, tag_id=tag.id, is_ai_generated=False)
                        db.session.add(product_tag)
            
            # Remove tags that are no longer selected
            tags_to_remove = current_tag_ids - new_tag_ids
            for tag_id in tags_to_remove:
                pt = ProductTag.query.filter_by(product_id=product_id, tag_id=tag_id).first()
                if pt:
                    db.session.delete(pt)
        except Exception as e:
            print(f'Tag update error: {e}')

    db.session.commit()

    log_action('PRODUCT_UPDATE', {'product_id': product.id})

    return jsonify({
        'message': 'Product updated successfully',
        'product': product.to_dict()
    })

@bp.route('/<int:product_id>', methods=['DELETE'])
@token_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)

    if product.user_id != g.user.id and g.user.role != 'admin':
        return jsonify({'error': 'You can only delete your own products'}), 403

    # 先删除关联的交易和标签记录，避免外键约束问题
    Transaction.query.filter_by(product_id=product_id).delete()
    ProductTag.query.filter_by(product_id=product_id).delete()
    db.session.commit()

    db.session.delete(product)
    db.session.commit()

    log_action('PRODUCT_DELETE', {'product_id': product_id})

    return jsonify({'message': 'Product deleted successfully'})

@bp.route('/my', methods=['GET'])
@token_required
def get_my_products():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    pagination = Product.query.filter_by(user_id=g.user.id).order_by(
        Product.create_time.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'products': [p.to_dict() for p in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    })