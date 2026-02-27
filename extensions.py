"""Flask extensions initialization"""
from flask import request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from whitenoise import WhiteNoise
import os

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

def init_extensions(app):
    """Initialize all extensions with the app"""
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Whitenoise for serving static files in production
    if not app.debug:
        static_folder = os.path.join(os.path.dirname(__file__), 'static')
        app.wsgi_app = WhiteNoise(app.wsgi_app, root=static_folder, autorefresh=True)
    
    # Handle proxy headers for SSL termination on Render
    @app.before_request
    def before_request():
        # Render uses X-Forwarded-Proto for HTTPS detection
        if request.headers.get('X-Forwarded-Proto') == 'https':
            app.config['SESSION_COOKIE_SECURE'] = True
        else:
            app.config['SESSION_COOKIE_SECURE'] = app.config.get('SESSION_COOKIE_SECURE', False)
