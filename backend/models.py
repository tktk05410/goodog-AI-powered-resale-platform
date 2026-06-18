from datetime import datetime, timezone, timedelta
from flask_sqlalchemy import SQLAlchemy

def utc_to_local(utc_dt):
    if utc_dt is None:
        return None
    local_tz = timezone(timedelta(hours=8))
    local_dt = utc_dt.replace(tzinfo=timezone.utc).astimezone(local_tz)
    return local_dt.strftime('%Y-%m-%d %H:%M:%S')

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(64), nullable=False)
    student_id = db.Column(db.String(20), unique=True)
    credit_score = db.Column(db.Integer, default=100)
    face_encoding = db.Column(db.LargeBinary, nullable=True)
    role = db.Column(db.Enum('user', 'admin'), default='user')
    create_time = db.Column(db.DateTime, default=datetime.utcnow)

    products = db.relationship('Product', backref='publisher', lazy='dynamic')
    sent_messages = db.relationship('Message', foreign_keys='Message.from_user', backref='sender', lazy='dynamic')
    received_messages = db.relationship('Message', foreign_keys='Message.to_user', backref='receiver', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'student_id': self.student_id,
            'credit_score': self.credit_score,
            'role': self.role,
            'create_time': utc_to_local(self.create_time)
        }

class Product(db.Model):
    __tablename__ = 'product'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    type = db.Column(db.Enum('sell', 'buy'), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=True)
    image_path = db.Column(db.String(255), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.Enum('on', 'off', 'sold'), default='on')
    create_time = db.Column(db.DateTime, default=datetime.utcnow)

    transactions = db.relationship('Transaction', backref='product', lazy='dynamic')
    tags = db.relationship('ProductTag', backref='product', lazy='dynamic')

    def to_dict(self):
        tags = [pt.tag.to_dict() for pt in self.tags.all()] if hasattr(self, 'tags') else []
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'type': self.type,
            'price': float(self.price) if self.price else None,
            'image_path': self.image_path,
            'user_id': self.user_id,
            'status': self.status,
            'create_time': utc_to_local(self.create_time),
            'publisher': self.publisher.username if self.publisher else None,
            'tags': tags
        }

class Transaction(db.Model):
    __tablename__ = 'transaction'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    state = db.Column(db.Enum('pending', 'paid', 'done', 'canceled'), default='pending')
    create_time = db.Column(db.DateTime, default=datetime.utcnow)

    buyer = db.relationship('User', foreign_keys=[buyer_id])
    seller = db.relationship('User', foreign_keys=[seller_id])

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'buyer_id': self.buyer_id,
            'seller_id': self.seller_id,
            'state': self.state,
            'create_time': utc_to_local(self.create_time)
        }

class Message(db.Model):
    __tablename__ = 'message'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    from_user = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    to_user = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    ai_summary = db.Column(db.String(200), nullable=True)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'from_user': self.from_user,
            'to_user': self.to_user,
            'content': self.content,
            'is_read': self.is_read,
            'ai_summary': self.ai_summary,
            'create_time': utc_to_local(self.create_time)
        }

class SystemLog(db.Model):
    __tablename__ = 'system_log'

    log_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=True)
    action = db.Column(db.String(100), nullable=False)
    detail = db.Column(db.JSON, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'log_id': self.log_id,
            'user_id': self.user_id,
            'action': self.action,
            'detail': self.detail,
            'timestamp': utc_to_local(self.timestamp)
        }

class Tag(db.Model):
    __tablename__ = 'tag'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    color = db.Column(db.String(20), default='#409eff')
    is_ai_generated = db.Column(db.Boolean, default=False)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)

    products = db.relationship('ProductTag', backref='tag', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color,
            'is_ai_generated': self.is_ai_generated,
            'create_time': utc_to_local(self.create_time)
        }

class ProductTag(db.Model):
    __tablename__ = 'product_tag'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    tag_id = db.Column(db.Integer, db.ForeignKey('tag.id'), nullable=False)
    is_ai_generated = db.Column(db.Boolean, default=False)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('product_id', 'tag_id', name='uq_product_tag'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'tag_id': self.tag_id,
            'tag': self.tag.to_dict() if self.tag else None,
            'is_ai_generated': self.is_ai_generated,
            'create_time': utc_to_local(self.create_time)
        }


class TrendAnalysis(db.Model):
    __tablename__ = 'trend_analysis'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    year_month = db.Column(db.String(7), unique=True, nullable=False)
    analysis = db.Column(db.Text, nullable=False)
    source = db.Column(db.String(20), default='ai')
    create_time = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'year_month': self.year_month,
            'analysis': self.analysis,
            'source': self.source,
            'create_time': utc_to_local(self.create_time)
        }