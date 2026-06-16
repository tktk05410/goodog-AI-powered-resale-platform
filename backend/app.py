import os
import sys
import hashlib
import datetime
from functools import wraps
from flask import Flask, request, jsonify, g, send_from_directory, current_app
import jwt
from dotenv import load_dotenv

# 加载环境变量
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

from config import config
from models import db, User, Product, Transaction, Message, SystemLog, Tag, ProductTag

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    db.init_app(app)

    with app.app_context():
        db.create_all()

    register_blueprints(app)
    register_hooks(app)
    register_error_handlers(app)

    return app

def register_blueprints(app):
    from routes import auth, products, transactions, messages, users, ai, logs, stats, tags, admin

    app.register_blueprint(auth.bp, url_prefix='/api/auth')
    app.register_blueprint(products.bp, url_prefix='/api/products')
    app.register_blueprint(transactions.bp, url_prefix='/api/transactions')
    app.register_blueprint(messages.bp, url_prefix='/api/messages')
    app.register_blueprint(users.bp, url_prefix='/api/users')
    app.register_blueprint(ai.bp, url_prefix='/api/ai')
    app.register_blueprint(logs.bp, url_prefix='/api/logs')
    app.register_blueprint(stats.bp, url_prefix='/api/stats')
    app.register_blueprint(tags.bp, url_prefix='/api/tags')
    app.register_blueprint(admin.bp, url_prefix='/api/admin')

def register_hooks(app):
    @app.before_request
    def before_request():
        g.start_time = datetime.datetime.utcnow()
        g.user = None

        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            try:
                payload = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
                g.user = User.query.get(payload['user_id'])
            except jwt.ExpiredSignatureError:
                pass
            except jwt.InvalidTokenError:
                pass

    @app.after_request
    def after_request(response):
        if hasattr(g, 'start_time'):
            duration = (datetime.datetime.utcnow() - g.start_time).total_seconds() * 1000
            response.headers['X-Response-Time'] = f'{duration:.2f}ms'
        return response

def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({'error': 'Bad Request', 'message': str(e)}), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({'error': 'Unauthorized', 'message': 'Authentication required'}), 401

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({'error': 'Forbidden', 'message': 'Access denied'}), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Not Found', 'message': 'Resource not found'}), 404

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return jsonify({'error': 'Internal Server Error', 'message': 'An unexpected error occurred'}), 500

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not g.user:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated

def log_action(action, detail=None):
    try:
        log = SystemLog(
            user_id=g.user.id if g.user else None,
            action=action,
            detail=detail
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f'Failed to log action: {e}')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

def save_uploaded_file(file):
    if file and allowed_file(file.filename):
        filename = hashlib.md5((file.filename + str(datetime.datetime.utcnow())).encode()).hexdigest()
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f'{filename}.{ext}'
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return filename
    return None

if __name__ == '__main__':
    app = create_app('development')
    app.run(host='0.0.0.0', port=5000, debug=True)