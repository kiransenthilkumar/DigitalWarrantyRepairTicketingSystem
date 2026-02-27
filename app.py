"""
Flask application factory
Digital Warranty & Repair Ticketing System
"""
from flask import Flask, render_template, redirect, url_for, send_from_directory
from config import get_config
from extensions import db, login_manager, csrf, init_extensions
from routes import register_blueprints
from models import User
import os

def create_app(config_name=None):
    """Application factory"""
    # Create Flask app
    app = Flask(__name__)
    
    # Load configuration
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    app.config.from_object(get_config(config_name))
    
    # Create instance directory if it doesn't exist
    instance_dir = os.path.join(os.path.dirname(__file__), 'instance')
    if not os.path.exists(instance_dir):
        os.makedirs(instance_dir)
    
    # Initialize extensions
    init_extensions(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Serve uploaded files from persistent storage
    @app.route('/uploads/<path:filename>')
    def serve_upload(filename):
        """Serve uploaded files from persistent storage"""
        upload_folder = app.config.get('UPLOAD_FOLDER', os.path.join(os.path.dirname(__file__), 'static', 'uploads'))
        try:
            return send_from_directory(upload_folder, filename)
        except FileNotFoundError:
            return render_template('errors/404.html'), 404
    
    # Attempt to initialize the database once.  If the file is locked,
    # missing, or otherwise inaccessible we catch the exception and log it
    # rather than let the entire application crash.  This makes `python
    # app.py` reliable even when the development reloader restarts the
    # process.
    try:
        with app.app_context():
            db.create_all()

            # Create default admin user if doesn't exist
            if User.query.filter_by(username='admin').first() is None:
                admin = User(
                    username='admin',
                    email='admin@example.com',
                    full_name='Administrator',
                    role='admin'
                )
                admin.set_password('admin123')  # Change in production!
                db.session.add(admin)
                db.session.commit()
                print("Default admin user created (Email: admin@example.com, Password: admin123)")
    except Exception as e:
        # Logging via print because logger may not be configured yet
        print(f"[warning] database initialization failed: {e}")
    
    # Register error handlers
    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    # Register context processors
    @app.context_processor
    def inject_user():
        from flask_login import current_user
        return {'current_user': current_user}

    @app.context_processor
    def inject_utilities():
        # expose helper functions to Jinja2
        from datetime import datetime
        return {'now': datetime.utcnow}
    
    # Home route
    @app.route('/')
    def index():
        """Landing page / home route"""
        from flask_login import current_user
        
        if current_user.is_authenticated:
            if current_user.is_admin():
                return redirect(url_for('admin.dashboard'))
            elif current_user.is_technician():
                return redirect(url_for('technician.dashboard'))
            else:
                return redirect(url_for('customer.dashboard'))
        
        # unauthenticated landing page
        return render_template('landing.html')
    
    return app

if __name__ == '__main__':
    app = create_app()
    # Disable the reloader to avoid repeated initialization issues; in
    # development you can still restart manually when you change code.
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    app.run(debug=debug, host='0.0.0.0', port=port, use_reloader=False)
