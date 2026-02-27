"""Admin routes"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import User, Product, Ticket, RepairNote, Feedback, ActivityLog
from forms import AdminUserForm, TicketStatusForm, SearchForm
from datetime import datetime, timedelta
from functools import wraps
from sqlalchemy import extract, func, case

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    """Decorator to check if user is admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.is_deleted:
            flash('Access denied', 'danger')
            return redirect(url_for('auth.login'))
        if not current_user.is_admin():
            flash('Admin access required', 'danger')
            return redirect(url_for('customer.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard"""
    # User statistics
    total_users = User.query.filter_by(is_deleted=False).count()
    customers = User.query.filter(User.role == 'customer', User.is_deleted == False).count()
    technicians = User.query.filter(User.role == 'technician', User.is_deleted == False).count()
    admins = User.query.filter(User.role == 'admin', User.is_deleted == False).count()
    
    # Warranty statistics
    total_products = Product.query.filter_by(is_deleted=False).count()
    active_warranties = Product.query.filter(
        Product.is_deleted == False,
        Product.warranty_expiry > datetime.utcnow()
    ).count()
    expired_warranties = total_products - active_warranties
    
    # Ticket statistics
    total_tickets = Ticket.query.filter_by(is_deleted=False).count()
    open_tickets = Ticket.query.filter(
        Ticket.is_deleted == False,
        Ticket.status.in_(['open', 'in_progress', 'waiting_for_parts'])
    ).count()
    completed_tickets = Ticket.query.filter(
        Ticket.is_deleted == False,
        Ticket.status.in_(['completed', 'closed'])
    ).count()
    
    # Average repair cost
    avg_repair_cost = db.session.query(func.avg(Ticket.repair_cost)).filter(
        Ticket.is_deleted == False,
        Ticket.repair_cost.isnot(None)
    ).scalar() or 0
    
    # Get recent activity
    recent_activity = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(10).all()
    
    # Get recent tickets
    recent_tickets = Ticket.query.filter_by(is_deleted=False).order_by(
        Ticket.created_at.desc()
    ).limit(10).all()
    
    return render_template('admin/dashboard.html',
        total_users=total_users,
        customers=customers,
        technicians=technicians,
        admins=admins,
        total_products=total_products,
        active_warranties=active_warranties,
        expired_warranties=expired_warranties,
        total_tickets=total_tickets,
        open_tickets=open_tickets,
        completed_tickets=completed_tickets,
        avg_repair_cost=avg_repair_cost,
        recent_activity=recent_activity,
        recent_tickets=recent_tickets
    )

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """List all users"""
    page = request.args.get('page', 1, type=int)
    role_filter = request.args.get('role', '')
    
    query = User.query.filter_by(is_deleted=False)
    
    if role_filter:
        query = query.filter_by(role=role_filter)
    
    users = query.order_by(User.created_at.desc()).paginate(page=page, per_page=15)
    
    return render_template('admin/users.html', users=users, role_filter=role_filter)

@admin_bp.route('/users/<int:user_id>')
@login_required
@admin_required
def user_detail(user_id):
    """View user details"""
    user = User.query.get_or_404(user_id)
    
    if user.is_deleted:
        flash('User not found', 'danger')
        return redirect(url_for('admin.users'))
    
    # Get user statistics
    if user.is_customer():
        products_count = Product.query.filter_by(user_id=user_id, is_deleted=False).count()
        tickets_count = Ticket.query.filter_by(customer_id=user_id, is_deleted=False).count()
        
        return render_template('admin/user_detail.html',
            user=user,
            products_count=products_count,
            tickets_count=tickets_count
        )
    elif user.is_technician():
        assigned_tickets = Ticket.query.filter_by(technician_id=user_id, is_deleted=False).count()
        completed_tickets = Ticket.query.filter(
            Ticket.technician_id == user_id,
            Ticket.is_deleted == False,
            Ticket.status.in_(['completed', 'closed'])
        ).count()
        
        avg_rating = db.session.query(func.avg(Feedback.rating)).join(
            Ticket,
            Feedback.ticket_id == Ticket.id
        ).filter(
            Ticket.technician_id == user_id,
            Ticket.is_deleted == False
        ).scalar()
        
        return render_template('admin/user_detail.html',
            user=user,
            assigned_tickets=assigned_tickets,
            completed_tickets=completed_tickets,
            avg_rating=avg_rating
        )
    
    return render_template('admin/user_detail.html', user=user)

@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """Edit user"""
    user = User.query.get_or_404(user_id)
    
    if user.is_deleted:
        flash('User not found', 'danger')
        return redirect(url_for('admin.users'))
    
    form = AdminUserForm()
    if form.validate_on_submit():
        try:
            user.full_name = form.full_name.data
            user.phone = form.phone.data
            user.role = form.role.data
            db.session.commit()
            
            # Log activity
            activity = ActivityLog(
                user_id=current_user.id,
                action='user_updated',
                resource_type='user',
                resource_id=user_id,
                changes=f'Role changed to {form.role.data}'
            )
            db.session.add(activity)
            db.session.commit()
            
            flash('User updated successfully!', 'success')
            return redirect(url_for('admin.user_detail', user_id=user_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating user: {str(e)}', 'danger')
    elif request.method == 'GET':
        form.username.data = user.username
        form.email.data = user.email
        form.full_name.data = user.full_name
        form.phone.data = user.phone
        form.role.data = user.role
    
    return render_template('admin/edit_user.html', form=form, user=user)

@admin_bp.route('/users/<int:user_id>/deactivate', methods=['POST'])
@login_required
@admin_required
def deactivate_user(user_id):
    """Deactivate user"""
    if user_id == current_user.id:
        flash('Cannot deactivate your own account', 'danger')
        return redirect(url_for('admin.user_detail', user_id=user_id))
    
    user = User.query.get_or_404(user_id)
    
    try:
        user.is_active = False
        
        activity = ActivityLog(
            user_id=current_user.id,
            action='user_deactivated',
            resource_type='user',
            resource_id=user_id
        )
        db.session.add(activity)
        db.session.commit()
        
        flash('User deactivated successfully!', 'success')
        return redirect(url_for('admin.user_detail', user_id=user_id))
    except Exception as e:
        db.session.rollback()
        flash(f'Error deactivating user: {str(e)}', 'danger')
        return redirect(url_for('admin.user_detail', user_id=user_id))

@admin_bp.route('/users/<int:user_id>/activate', methods=['POST'])
@login_required
@admin_required
def activate_user(user_id):
    """Activate user"""
    user = User.query.get_or_404(user_id)
    
    try:
        user.is_active = True
        
        activity = ActivityLog(
            user_id=current_user.id,
            action='user_activated',
            resource_type='user',
            resource_id=user_id
        )
        db.session.add(activity)
        db.session.commit()
        
        flash('User activated successfully!', 'success')
        return redirect(url_for('admin.user_detail', user_id=user_id))
    except Exception as e:
        db.session.rollback()
        flash(f'Error activating user: {str(e)}', 'danger')
        return redirect(url_for('admin.user_detail', user_id=user_id))

@admin_bp.route('/tickets')
@login_required
@admin_required
def tickets():
    """List all tickets"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    priority_filter = request.args.get('priority', '')
    
    query = Ticket.query.filter_by(is_deleted=False)
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    if priority_filter:
        query = query.filter_by(priority=priority_filter)
    
    tickets = query.order_by(Ticket.created_at.desc()).paginate(page=page, per_page=15)
    
    return render_template('admin/tickets.html',
        tickets=tickets,
        status_filter=status_filter,
        priority_filter=priority_filter
    )

@admin_bp.route('/tickets/<int:ticket_id>')
@login_required
@admin_required
def ticket_detail(ticket_id):
    """View ticket details"""
    ticket = Ticket.query.get_or_404(ticket_id)
    
    if ticket.is_deleted:
        flash('Ticket not found', 'danger')
        return redirect(url_for('admin.tickets'))
    
    customer = User.query.get(ticket.customer_id)
    product = Product.query.get(ticket.product_id)
    technician = User.query.get(ticket.technician_id) if ticket.technician_id else None
    repair_notes = RepairNote.query.filter_by(ticket_id=ticket_id).order_by(RepairNote.created_at.desc()).all()
    feedback = Feedback.query.filter_by(ticket_id=ticket_id).first()
    
    return render_template('admin/ticket_detail.html',
        ticket=ticket,
        customer=customer,
        product=product,
        technician=technician,
        repair_notes=repair_notes,
        feedback=feedback
    )

@admin_bp.route('/tickets/<int:ticket_id>/assign', methods=['GET', 'POST'])
@login_required
@admin_required
def assign_technician(ticket_id):
    """Assign technician to ticket"""
    ticket = Ticket.query.get_or_404(ticket_id)
    
    if ticket.is_deleted:
        flash('Ticket not found', 'danger')
        return redirect(url_for('admin.tickets'))
    
    technicians = User.query.filter(
        User.role == 'technician',
        User.is_active == True,
        User.is_deleted == False
    ).all()
    
    # prepare form with choices
    from forms import AssignTechnicianForm
    form = AssignTechnicianForm()
    form.technician_id.choices = [(t.id, f"{t.full_name} ({t.username})") for t in technicians]
    
    if form.validate_on_submit():
        try:
            old_tech = ticket.technician_id
            ticket.technician_id = form.technician_id.data
            ticket.status = 'in_progress'
            ticket.updated_at = datetime.utcnow()
            
            activity = ActivityLog(
                user_id=current_user.id,
                action='ticket_assigned',
                resource_type='ticket',
                resource_id=ticket_id,
                changes=f'Assigned to technician {ticket.technician_id}'
            )
            db.session.add(activity)
            db.session.commit()
            
            flash('Technician assigned successfully!', 'success')
            return redirect(url_for('admin.ticket_detail', ticket_id=ticket_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error assigning technician: {str(e)}', 'danger')
    
    return render_template('admin/assign_technician.html', ticket=ticket, form=form)

@admin_bp.route('/reports/overview')
@login_required
@admin_required
def report_overview():
    """System overview report"""
    # Get data for the last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    # Daily ticket statistics
    daily_stats = db.session.query(
        extract('day', Ticket.created_at).label('day'),
        func.count(Ticket.id).label('total'),
        func.sum(case((Ticket.status.in_(['completed', 'closed']), 1), else_=0)).label('completed')
    ).filter(
        Ticket.created_at >= thirty_days_ago,
        Ticket.is_deleted == False
    ).group_by(extract('day', Ticket.created_at)).all()
    
    # Ticket status distribution
    status_dist = db.session.query(
        Ticket.status,
        func.count(Ticket.id).label('count')
    ).filter(Ticket.is_deleted == False).group_by(Ticket.status).all()
    
    # Priority distribution
    priority_dist = db.session.query(
        Ticket.priority,
        func.count(Ticket.id).label('count')
    ).filter(Ticket.is_deleted == False).group_by(Ticket.priority).all()
    
    return render_template('admin/report_overview.html',
        daily_stats=daily_stats,
        status_dist=status_dist,
        priority_dist=priority_dist
    )

@admin_bp.route('/reports/technician')
@login_required
@admin_required
def report_technician():
    """Technician performance report"""
    technicians = User.query.filter(
        User.role == 'technician',
        User.is_deleted == False
    ).all()
    
    tech_stats = []
    for tech in technicians:
        assigned = Ticket.query.filter_by(technician_id=tech.id, is_deleted=False).count()
        completed = Ticket.query.filter(
            Ticket.technician_id == tech.id,
            Ticket.is_deleted == False,
            Ticket.status.in_(['completed', 'closed'])
        ).count()
        
        avg_rating = db.session.query(func.avg(Feedback.rating)).join(
            Ticket,
            Feedback.ticket_id == Ticket.id
        ).filter(
            Ticket.technician_id == tech.id,
            Ticket.is_deleted == False
        ).scalar()
        
        total_cost = db.session.query(func.sum(Ticket.repair_cost)).filter(
            Ticket.technician_id == tech.id,
            Ticket.is_deleted == False,
            Ticket.repair_cost.isnot(None)
        ).scalar() or 0
        
        tech_stats.append({
            'technician': tech,
            'assigned': assigned,
            'completed': completed,
            'avg_rating': avg_rating,
            'total_cost': total_cost
        })
    
    return render_template('admin/report_technician.html', tech_stats=tech_stats)

@admin_bp.route('/reports/warranty')
@login_required
@admin_required
def report_warranty():
    """Warranty status report"""
    now = datetime.utcnow()
    
    active = Product.query.filter(
        Product.is_deleted == False,
        Product.warranty_expiry > now
    ).count()
    
    expired = Product.query.filter(
        Product.is_deleted == False,
        Product.warranty_expiry <= now
    ).count()
    
    expiring_soon = Product.query.filter(
        Product.is_deleted == False,
        Product.warranty_expiry > now,
        Product.warranty_expiry <= now + timedelta(days=30)
    ).all()
    
    # Category distribution
    category_dist = db.session.query(
        Product.category,
        func.count(Product.id).label('count')
    ).filter(Product.is_deleted == False).group_by(Product.category).all()
    
    return render_template('admin/report_warranty.html',
        active=active,
        expired=expired,
        expiring_soon=expiring_soon,
        category_dist=category_dist
    )

@admin_bp.route('/activity-logs')
@login_required
@admin_required
def activity_logs():
    """View activity logs"""
    page = request.args.get('page', 1, type=int)
    action_filter = request.args.get('action', '')
    
    query = ActivityLog.query
    
    if action_filter:
        query = query.filter_by(action=action_filter)
    
    logs = query.order_by(ActivityLog.created_at.desc()).paginate(page=page, per_page=20)
    
    return render_template('admin/activity_logs.html', logs=logs, action_filter=action_filter)

@admin_bp.route('/search')
@login_required
@admin_required
def search():
    """Admin search"""
    form = SearchForm()
    results = {'users': [], 'tickets': [], 'products': []}
    
    if form.validate_on_submit() and form.search_query.data:
        search_term = f"%{form.search_query.data}%"
        
        # Search users
        results['users'] = User.query.filter(
            User.is_deleted == False,
            (User.username.ilike(search_term) |
             User.email.ilike(search_term) |
             User.full_name.ilike(search_term))
        ).limit(10).all()
        
        # Search tickets
        results['tickets'] = Ticket.query.filter(
            Ticket.is_deleted == False,
            (Ticket.ticket_number.ilike(search_term) |
             Ticket.issue_description.ilike(search_term))
        ).limit(10).all()
        
        # Search products
        results['products'] = Product.query.filter(
            Product.is_deleted == False,
            (Product.product_name.ilike(search_term) |
             Product.serial_number.ilike(search_term))
        ).limit(10).all()
    
    return render_template('admin/search.html', form=form, results=results)
