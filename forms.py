"""WTForms for form handling and validation"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, EmailField, TextAreaField, SelectField, IntegerField, FloatField, DateTimeField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length, Optional, NumberRange
from models import User, Product
from datetime import datetime

class RegistrationForm(FlaskForm):
    """User registration form"""
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=80, message='Username must be between 3 and 80 characters')
    ])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    full_name = StringField('Full Name', validators=[DataRequired(), Length(min=3, max=120)])
    phone = StringField('Phone Number', validators=[Optional(), Length(min=10, max=20)])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6, message='Password must be at least 6 characters')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    role = SelectField('Role', choices=[('customer', 'Customer'), ('technician', 'Technician')], default='customer')
    
    def validate_username(self, field):
        """Check if username already exists"""
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already taken.')
    
    def validate_email(self, field):
        """Check if email already exists"""
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

class LoginForm(FlaskForm):
    """User login form"""
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = SelectField('Remember Me', choices=[('1', 'Yes'), ('0', 'No')], default='0')

class ProductForm(FlaskForm):
    """Product registration form"""
    product_name = StringField('Product Name', validators=[DataRequired(), Length(min=3, max=200)])
    brand = StringField('Brand', validators=[DataRequired(), Length(min=2, max=100)])
    category = SelectField('Category', choices=[
        ('laptop', 'Laptop'),
        ('desktop', 'Desktop'),
        ('mobile', 'Mobile Phone'),
        ('tablet', 'Tablet'),
        ('smartwatch', 'Smartwatch'),
        ('headphones', 'Headphones'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    serial_number = StringField('Serial Number', validators=[DataRequired(), Length(min=3, max=100)])
    purchase_date = DateTimeField('Purchase Date', format='%Y-%m-%d', validators=[DataRequired()])
    warranty_months = IntegerField('Warranty (Months)', validators=[DataRequired(), NumberRange(min=1, max=120)])
    description = TextAreaField('Product Description', validators=[Optional()])
    invoice_image = FileField('Invoice Image', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])

class TicketForm(FlaskForm):
    """Raise repair ticket form"""
    product_id = SelectField('Select Product', coerce=int, validators=[DataRequired()])
    issue_description = TextAreaField('Issue Description', validators=[
        DataRequired(),
        Length(min=10, message='Description must be at least 10 characters')
    ])
    priority = SelectField('Priority', choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], default='medium', validators=[DataRequired()])
    repair_type = SelectField('Repair Type', choices=[
        ('warranty', 'Covered Under Warranty'),
        ('paid', 'Paid Repair (Warranty Expired)')
    ], default='warranty', validators=[DataRequired()], description='Select warranty coverage type')
    product_images = FileField('Product Images (Multiple)', render_kw={'multiple': True})

class TicketStatusForm(FlaskForm):
    """Update ticket status (for technicians)"""
    status = SelectField('Status', choices=[
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('waiting_for_parts', 'Waiting for Parts'),
        ('completed', 'Completed'),
        ('closed', 'Closed'),
        ('rejected', 'Rejected')
    ], validators=[DataRequired()])
    repair_cost = FloatField('Repair Cost', validators=[Optional(), NumberRange(min=0)])


class PaymentForm(FlaskForm):
    """Simple form used for mock payment to include CSRF and UPI ID"""
    upi_id = StringField('UPI ID', validators=[DataRequired(), Length(min=3, max=100)])

class AddRepairNoteForm(FlaskForm):
    """Add repair note form"""
    note_text = TextAreaField('Repair Note', validators=[
        DataRequired(),
        Length(min=5, message='Note must be at least 5 characters')
    ])

class FeedbackForm(FlaskForm):
    """Customer feedback form"""
    rating = SelectField('Rating', choices=[
        ('5', '5 Stars - Excellent'),
        ('4', '4 Stars - Good'),
        ('3', '3 Stars - Average'),
        ('2', '2 Stars - Poor'),
        ('1', '1 Star - Very Poor')
    ], coerce=int, validators=[DataRequired()])
    comment = TextAreaField('Additional Comments', validators=[Optional(), Length(max=500)])

class EditProfileForm(FlaskForm):
    """Edit user profile"""
    full_name = StringField('Full Name', validators=[DataRequired(), Length(min=3, max=120)])
    phone = StringField('Phone Number', validators=[Optional(), Length(min=10, max=20)])
    address = TextAreaField('Address', validators=[Optional()])
    
class ChangePasswordForm(FlaskForm):
    """Change password form"""
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=6, message='Password must be at least 6 characters')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('new_password', message='Passwords must match')
    ])

class AdminUserForm(FlaskForm):
    """Admin form to manage users"""
    username = StringField('Username', validators=[DataRequired()])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    full_name = StringField('Full Name', validators=[DataRequired()])
    phone = StringField('Phone', validators=[Optional()])
    role = SelectField('Role', choices=[
        ('customer', 'Customer'),
        ('technician', 'Technician'),
        ('admin', 'Admin')
    ], validators=[DataRequired()])

class SearchForm(FlaskForm):
    """Search form for tickets and products"""
    search_query = StringField('Search', validators=[Optional()])
    status = SelectField('Status', choices=[('', 'All')] + [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('waiting_for_parts', 'Waiting for Parts'),
        ('completed', 'Completed'),
        ('closed', 'Closed')
    ], validators=[Optional()])
    priority = SelectField('Priority', choices=[('', 'All')] + [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], validators=[Optional()])


class AssignTechnicianForm(FlaskForm):
    """Form used by admin to assign a technician to a ticket"""
    technician_id = SelectField('Technician', coerce=int, validators=[DataRequired()])

