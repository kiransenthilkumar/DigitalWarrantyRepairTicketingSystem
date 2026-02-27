"""Flask configuration"""
import os
from datetime import timedelta

class Config:
    """Base configuration"""
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database - use absolute path for SQLite
    if 'DATABASE_URL' in os.environ:
        SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
    else:
        # Create absolute path to instance directory
        basedir = os.path.abspath(os.path.dirname(__file__))
        instance_path = os.path.join(basedir, 'instance')
        db_path = os.path.join(instance_path, 'warranty_system.db')
        # Convert to proper SQLite URI format (forward slashes)
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + db_path.replace('\\', '/')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session config
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = True  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Upload configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    # Use persistent storage on Render (/var/data), fall back to local for development
    if os.path.exists('/var/data'):
        UPLOAD_FOLDER = '/var/data/uploads'
    else:
        UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'pdf'}
    
    # Pagination
    ITEMS_PER_PAGE = 10
    
    # Email configuration (for notifications)
    MAIL_SERVER = os.getenv('MAIL_SERVER', '')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', True)
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@warranty.local')

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False

class ProductionConfig(Config):
    """Production configuration for Render"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    # Use PostgreSQL in production
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://user:pass@localhost/warranty_db'
    )

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(env=None):
    """Get configuration based on environment"""
    if env is None:
        env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])
