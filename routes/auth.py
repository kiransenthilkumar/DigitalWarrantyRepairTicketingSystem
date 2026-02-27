"""Authentication routes"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db, login_manager
from models import User
from forms import RegistrationForm, LoginForm, ChangePasswordForm, EditProfileForm
from datetime import datetime

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    return User.query.get(int(user_id))

@auth_bp.route('/')
def index():
    """Redirect to login from auth blueprint"""
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('customer.dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            # Create new user
            user = User(
                username=form.username.data,
                email=form.email.data,
                full_name=form.full_name.data,
                phone=form.phone.data,
                role=form.role.data
            )
            user.set_password(form.password.data)
            
            db.session.add(user)
            db.session.commit()
            
            flash(f'Account created successfully! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating account: {str(e)}', 'danger')
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        # Redirect based on role
        if current_user.is_admin():
            return redirect(url_for('admin.dashboard'))
        elif current_user.is_technician():
            return redirect(url_for('technician.dashboard'))
        else:
            return redirect(url_for('customer.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password', 'danger')
            return redirect(url_for('auth.login'))
        
        if not user.is_active or user.is_deleted:
            flash('Your account is inactive or has been deleted', 'danger')
            return redirect(url_for('auth.login'))
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Login user
        login_user(user, remember=form.remember.data == '1')
        
        # Redirect based on role
        next_page = request.args.get('next')
        if next_page and next_page.startswith('/'):
            return redirect(next_page)
        
        if user.is_admin():
            return redirect(url_for('admin.dashboard'))
        elif user.is_technician():
            return redirect(url_for('technician.dashboard'))
        else:
            return redirect(url_for('customer.dashboard'))
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile')
@login_required
def profile():
    """View user profile"""
    return render_template('auth/profile.html', user=current_user)

@auth_bp.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit user profile"""
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.full_name = form.full_name.data
        current_user.phone = form.phone.data
        current_user.address = form.address.data
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('auth.profile'))
    elif request.method == 'GET':
        form.full_name.data = current_user.full_name
        form.phone.data = current_user.phone
        form.address.data = current_user.address
    
    return render_template('auth/edit_profile.html', form=form)

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change password"""
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Current password is incorrect', 'danger')
        else:
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Password changed successfully!', 'success')
            return redirect(url_for('auth.profile'))
    
    return render_template('auth/change_password.html', form=form)
