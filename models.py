"""Database models using SQLAlchemy ORM"""
from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from enum import Enum
import uuid

class UserRole(Enum):
    """User role enumeration"""
    CUSTOMER = 'customer'
    TECHNICIAN = 'technician'
    ADMIN = 'admin'

class User(UserMixin, db.Model):
    """User model for authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.Text, nullable=True)
    role = db.Column(db.String(20), nullable=False, default='customer')  # customer, technician, admin
    
    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)  # Soft delete
    
    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    products = db.relationship('Product', backref='owner', lazy='dynamic', foreign_keys='Product.user_id')
    tickets = db.relationship('Ticket', backref='customer', lazy='dynamic', foreign_keys='Ticket.customer_id')
    assigned_tickets = db.relationship('Ticket', backref='assigned_technician', lazy='dynamic', foreign_keys='Ticket.technician_id')
    repair_notes = db.relationship('RepairNote', backref='created_by_user', lazy='dynamic')
    feedback = db.relationship('Feedback', backref='user', lazy='dynamic')
    activity_logs = db.relationship('ActivityLog', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
    def check_password(self, password):
        """Check if password matches"""
        return check_password_hash(self.password_hash, password)
    
    def is_technician(self):
        """Check if user is technician"""
        return self.role == 'technician'
    
    def is_admin(self):
        """Check if user is admin"""
        return self.role == 'admin'
    
    def is_customer(self):
        """Check if user is customer"""
        return self.role == 'customer'
    
    def __repr__(self):
        return f'<User {self.username}>'

class Product(db.Model):
    """Product warranty model"""
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(200), nullable=False)
    brand = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False, default='other')  # laptop, mobile, etc
    serial_number = db.Column(db.String(100), nullable=False, unique=True, index=True)
    purchase_date = db.Column(db.DateTime, nullable=False)
    warranty_months = db.Column(db.Integer, nullable=False)
    warranty_expiry = db.Column(db.DateTime, nullable=False, index=True)
    
    description = db.Column(db.Text, nullable=True)
    invoice_image = db.Column(db.String(255), nullable=True)  # Will store file path or Cloudinary URL
    
    # Soft delete
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign key
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Relationships
    tickets = db.relationship('Ticket', backref='product', lazy='dynamic')
    
    @property
    def warranty_status(self):
        """Get warranty status"""
        if self.is_deleted:
            return 'deleted'
        if self.warranty_expiry < datetime.utcnow():
            return 'expired'
        days_remaining = (self.warranty_expiry - datetime.utcnow()).days
        if days_remaining < 30:
            return 'expiring_soon'
        return 'active'
    
    @property
    def days_remaining(self):
        """Calculate days remaining in warranty"""
        if self.warranty_expiry < datetime.utcnow():
            return 0
        return (self.warranty_expiry - datetime.utcnow()).days
    
    def __repr__(self):
        return f'<Product {self.product_name}>'

class Ticket(db.Model):
    """Repair ticket model"""
    __tablename__ = 'tickets'
    
    id = db.Column(db.Integer, primary_key=True)
    ticket_number = db.Column(db.String(50), unique=True, nullable=False, index=True)  # Auto generated
    
    # Foreign keys
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    technician_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    
    # Issue and description
    issue_description = db.Column(db.Text, nullable=False)
    issue_images = db.Column(db.Text, nullable=True)  # JSON list of image URLs
    
    # Status and priority
    status = db.Column(db.String(50), nullable=False, default='open', index=True)  
    # open, in_progress, waiting_for_parts, completed, closed, rejected
    priority = db.Column(db.String(20), nullable=False, default='medium')  # low, medium, high, urgent
    
    # Repair details
    repair_cost = db.Column(db.Float, nullable=True)
    repair_duration_hours = db.Column(db.Integer, nullable=True)
    is_warranty_covered = db.Column(db.Boolean, default=True, nullable=False)  # False if warranty expired and customer paid
    is_paid = db.Column(db.Boolean, default=False, nullable=False)  # mark when mock payment processed
    
    # Soft delete
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    repair_notes = db.relationship('RepairNote', backref='ticket', lazy='dynamic', cascade='all, delete-orphan')
    feedback = db.relationship('Feedback', backref='ticket', uselist=False, cascade='all, delete-orphan')
    
    def generate_ticket_number(self):
        """Generate unique ticket number"""
        self.ticket_number = f"TKT-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    
    @property
    def warranty_status(self):
        """Get warranty status at time of ticket creation"""
        if self.product.warranty_expiry < datetime.utcnow():
            return 'expired'
        days_remaining = (self.product.warranty_expiry - datetime.utcnow()).days
        if days_remaining < 30:
            return 'expiring_soon'
        return 'active'
    
    @property
    def can_claim_warranty(self):
        """Check if ticket can be claimed under warranty"""
        if self.product.warranty_expiry < datetime.utcnow():
            return False
        return True
    
    def __repr__(self):
        return f'<Ticket {self.ticket_number}>'

class RepairNote(db.Model):
    """Repair notes added by technicians"""
    __tablename__ = 'repair_notes'
    
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    note_text = db.Column(db.Text, nullable=False)
    note_type = db.Column(db.String(50), default='update')  # update, diagnosis, warning, etc
    
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<RepairNote {self.ticket_id}>'

class Feedback(db.Model):
    """Customer feedback on completed repairs"""
    __tablename__ = 'feedback'
    
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'), nullable=False, unique=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    comment = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<Feedback Ticket:{self.ticket_id}>'

class ActivityLog(db.Model):
    """Admin activity log for audit trail"""
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    action = db.Column(db.String(100), nullable=False)  # e.g., 'user_created', 'ticket_assigned'
    resource_type = db.Column(db.String(50), nullable=False)  # e.g., 'user', 'ticket'
    resource_id = db.Column(db.Integer, nullable=True)
    changes = db.Column(db.Text, nullable=True)  # JSON of what changed
    
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<ActivityLog {self.action}>'

class WarrantyExpiterNotification(db.Model):
    """Track warranty expiry notifications"""
    __tablename__ = 'warranty_notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    notification_type = db.Column(db.String(50), default='30_days')  # 30_days, 7_days, expired
    sent_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    read_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<Notification {self.product_id}>'
