"""Routes package initialization"""
from routes.auth import auth_bp
from routes.customer import customer_bp
from routes.technician import technician_bp
from routes.admin import admin_bp

def register_blueprints(app):
    """Register all blueprints with the Flask app"""
    app.register_blueprint(auth_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(technician_bp)
    app.register_blueprint(admin_bp)
