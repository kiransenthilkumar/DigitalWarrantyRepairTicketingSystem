"""Technician routes"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import Ticket, RepairNote, User, Product, Feedback, ActivityLog
from forms import TicketStatusForm, AddRepairNoteForm, SearchForm
from datetime import datetime
from functools import wraps

technician_bp = Blueprint('technician', __name__, url_prefix='/technician')

def technician_required(f):
    """Decorator to check if user is technician"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.is_deleted:
            flash('Access denied', 'danger')
            return redirect(url_for('auth.login'))
        if not current_user.is_technician() and not current_user.is_admin():
            flash('Access denied', 'danger')
            return redirect(url_for('customer.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@technician_bp.route('/')
@technician_bp.route('/dashboard')
@login_required
@technician_required
def dashboard():
    """Technician dashboard"""
    # Get ticket statistics
    assigned_tickets = Ticket.query.filter(
        Ticket.technician_id == current_user.id,
        Ticket.is_deleted == False
    ).count()
    
    in_progress_tickets = Ticket.query.filter(
        Ticket.technician_id == current_user.id,
        Ticket.is_deleted == False,
        Ticket.status == 'in_progress'
    ).count()
    
    waiting_parts = Ticket.query.filter(
        Ticket.technician_id == current_user.id,
        Ticket.is_deleted == False,
        Ticket.status == 'waiting_for_parts'
    ).count()
    
    completed_tickets = Ticket.query.filter(
        Ticket.technician_id == current_user.id,
        Ticket.is_deleted == False,
        Ticket.status.in_(['completed', 'closed'])
    ).count()
    
    # Get high priority open tickets
    high_priority_tickets = Ticket.query.filter(
        Ticket.technician_id == current_user.id,
        Ticket.is_deleted == False,
        Ticket.status.in_(['open', 'in_progress']),
        Ticket.priority.in_(['high', 'urgent'])
    ).order_by(Ticket.created_at.asc()).limit(5).all()
    
    # Get recent tickets
    recent_tickets = Ticket.query.filter(
        Ticket.technician_id == current_user.id,
        Ticket.is_deleted == False
    ).order_by(Ticket.updated_at.desc()).limit(10).all()
    
    return render_template('technician/dashboard.html',
        assigned_tickets=assigned_tickets,
        in_progress_tickets=in_progress_tickets,
        waiting_parts=waiting_parts,
        completed_tickets=completed_tickets,
        high_priority_tickets=high_priority_tickets,
        recent_tickets=recent_tickets
    )

@technician_bp.route('/tickets')
@login_required
@technician_required
def tickets():
    """List assigned tickets"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    priority_filter = request.args.get('priority', '')
    
    query = Ticket.query.filter(
        Ticket.technician_id == current_user.id,
        Ticket.is_deleted == False
    )
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    if priority_filter:
        query = query.filter_by(priority=priority_filter)
    
    tickets = query.order_by(Ticket.priority.desc(), Ticket.created_at.asc()).paginate(page=page, per_page=10)
    
    return render_template('technician/tickets.html', 
        tickets=tickets, 
        status_filter=status_filter,
        priority_filter=priority_filter
    )

@technician_bp.route('/tickets/<int:ticket_id>')
@login_required
@technician_required
def ticket_detail(ticket_id):
    """View ticket details"""
    ticket = Ticket.query.get_or_404(ticket_id)
    
    if ticket.technician_id != current_user.id and not current_user.is_admin():
        flash('Access denied', 'danger')
        return redirect(url_for('technician.tickets'))
    
    # Get repair notes
    repair_notes = RepairNote.query.filter_by(ticket_id=ticket_id).order_by(RepairNote.created_at.desc()).all()
    
    # Get customer info
    customer = User.query.get(ticket.customer_id)
    product = Product.query.get(ticket.product_id)
    
    # Get feedback if exists
    feedback = Feedback.query.filter_by(ticket_id=ticket_id).first()
    
    return render_template('technician/ticket_detail.html',
        ticket=ticket,
        repair_notes=repair_notes,
        customer=customer,
        product=product,
        feedback=feedback
    )

@technician_bp.route('/tickets/<int:ticket_id>/update-status', methods=['GET', 'POST'])
@login_required
@technician_required
def update_status(ticket_id):
    """Update ticket status"""
    ticket = Ticket.query.get_or_404(ticket_id)
    
    if ticket.technician_id != current_user.id and not current_user.is_admin():
        flash('Access denied', 'danger')
        return redirect(url_for('technician.tickets'))
    
    # do not allow changes once the ticket is completed
    if ticket.status == 'completed':
        flash('Cannot modify a completed ticket.', 'warning')
        return redirect(url_for('technician.ticket_detail', ticket_id=ticket_id))
    
    form = TicketStatusForm()
    if form.validate_on_submit():
        try:
            old_status = ticket.status

            # If technician is trying to complete a paid repair, ensure a price exists
            if form.status.data == 'completed' and not ticket.is_warranty_covered and form.repair_cost.data is None and ticket.repair_cost is None:
                flash('Please set the repair cost before marking the ticket as completed for paid repairs.', 'warning')
                return render_template('technician/update_status.html', form=form, ticket=ticket)

            ticket.status = form.status.data
            if form.repair_cost.data is not None:
                ticket.repair_cost = form.repair_cost.data
            ticket.updated_at = datetime.utcnow()

            # if moving to completed and it's a paid repair, ensure repair_cost exists
            if old_status != 'completed' and form.status.data == 'completed' and not ticket.is_warranty_covered:
                if ticket.repair_cost is None:
                    flash('Repair cost missing; cannot complete paid repair without a cost.', 'danger')
                    return render_template('technician/update_status.html', form=form, ticket=ticket)

            # Log status update
            activity = ActivityLog(
                user_id=current_user.id,
                action='ticket_status_updated',
                resource_type='ticket',
                resource_id=ticket_id,
                changes=f'Status changed from {old_status} to {form.status.data}'
            )
            
            db.session.add(activity)
            db.session.commit()
            
            flash('Ticket status updated successfully!', 'success')
            return redirect(url_for('technician.ticket_detail', ticket_id=ticket_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating status: {str(e)}', 'danger')
    elif request.method == 'GET':
        form.status.data = ticket.status
        form.repair_cost.data = ticket.repair_cost
    
    return render_template('technician/update_status.html', form=form, ticket=ticket)

@technician_bp.route('/tickets/<int:ticket_id>/add-note', methods=['GET', 'POST'])
@login_required
@technician_required
def add_note(ticket_id):
    """Add repair note"""
    ticket = Ticket.query.get_or_404(ticket_id)
    
    if ticket.technician_id != current_user.id and not current_user.is_admin():
        flash('Access denied', 'danger')
        return redirect(url_for('technician.tickets'))
    
    form = AddRepairNoteForm()
    if form.validate_on_submit():
        try:
            note = RepairNote(
                ticket_id=ticket_id,
                user_id=current_user.id,
                note_text=form.note_text.data
            )
            db.session.add(note)
            
            # Update ticket updated_at
            ticket.updated_at = datetime.utcnow()
            
            db.session.commit()
            flash('Note added successfully!', 'success')
            return redirect(url_for('technician.ticket_detail', ticket_id=ticket_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding note: {str(e)}', 'danger')
    
    return render_template('technician/add_note.html', form=form, ticket=ticket)

@technician_bp.route('/performance')
@login_required
@technician_required
def performance():
    """View technician performance metrics"""
    # Total tickets assigned
    total_tickets = Ticket.query.filter(
        Ticket.technician_id == current_user.id,
        Ticket.is_deleted == False
    ).count()
    
    # Completed tickets
    completed = Ticket.query.filter(
        Ticket.technician_id == current_user.id,
        Ticket.is_deleted == False,
        Ticket.status.in_(['completed', 'closed'])
    ).count()
    
    # Average rating from feedback
    avg_rating = db.session.query(db.func.avg(Feedback.rating)).join(
        Ticket,
        Feedback.ticket_id == Ticket.id
    ).filter(
        Ticket.technician_id == current_user.id,
        Ticket.is_deleted == False
    ).scalar()
    
    # Total repair cost
    total_cost = db.session.query(db.func.sum(Ticket.repair_cost)).filter(
        Ticket.technician_id == current_user.id,
        Ticket.is_deleted == False,
        Ticket.status.in_(['completed', 'closed']),
        Ticket.repair_cost.isnot(None)
    ).scalar() or 0
    
    completion_rate = (completed / total_tickets * 100) if total_tickets > 0 else 0
    
    # Get monthly statistics
    from sqlalchemy import extract
    monthly_stats = db.session.query(
        extract('month', Ticket.created_at).label('month'),
        db.func.count(Ticket.id).label('total'),
        db.func.sum(db.case((Ticket.status.in_(['completed', 'closed']), 1), else_=0)).label('completed')
    ).filter(
        Ticket.technician_id == current_user.id,
        Ticket.is_deleted == False
    ).group_by(extract('month', Ticket.created_at)).all()
    
    return render_template('technician/performance.html',
        total_tickets=total_tickets,
        completed=completed,
        avg_rating=avg_rating,
        total_cost=total_cost,
        completion_rate=completion_rate,
        monthly_stats=monthly_stats
    )

@technician_bp.route('/search')
@login_required
@technician_required
def search():
    """Search assigned tickets"""
    form = SearchForm()
    results = []
    
    if form.validate_on_submit() and form.search_query.data:
        search_term = f"%{form.search_query.data}%"
        
        query = Ticket.query.filter(
            Ticket.technician_id == current_user.id,
            Ticket.is_deleted == False,
            (Ticket.ticket_number.ilike(search_term) |
             Ticket.issue_description.ilike(search_term))
        )
        
        if form.status.data:
            query = query.filter_by(status=form.status.data)
        if form.priority.data:
            query = query.filter_by(priority=form.priority.data)
        
        results = query.all()
    
    return render_template('technician/search.html', form=form, results=results)
