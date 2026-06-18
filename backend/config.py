import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'goodog-secret-key-2024'

    MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'localhost'
    MYSQL_PORT = os.environ.get('MYSQL_PORT') or 3306
    MYSQL_USER = os.environ.get('MYSQL_USER') or 'root'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or '12345'
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE') or 'goodog_date'

    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = True

    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'goodog-jwt-secret-2024'
    JWT_ACCESS_TOKEN_EXPIRES = 86400

    XUNFEI_APP_ID = os.environ.get('XUNFEI_APP_ID') or ''
    XUNFEI_API_KEY = os.environ.get('XUNFEI_API_KEY') or ''
    XUNFEI_API_SECRET = os.environ.get('XUNFEI_API_SECRET') or ''

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_ECHO = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}