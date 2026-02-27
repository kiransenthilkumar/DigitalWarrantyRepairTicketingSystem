"""Customer routes"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from extensions import db
import os
from werkzeug.utils import secure_filename
from models import Product, Ticket, RepairNote, Feedback, User, ActivityLog
from forms import PaymentForm
from forms import ProductForm, TicketForm, FeedbackForm, SearchForm
from datetime import datetime, timedelta
from functools import wraps

customer_bp = Blueprint('customer', __name__, url_prefix='/customer')

def customer_required(f):
    """Decorator to check if user is customer"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.is_deleted:
            flash('Access denied', 'danger')
            return redirect(url_for('auth.login'))
        if current_user.is_admin():
            return redirect(url_for('admin.dashboard'))
        if current_user.is_technician():
            return redirect(url_for('technician.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@customer_bp.route('/')
@customer_bp.route('/dashboard')
@login_required
@customer_required
def dashboard():
    """Customer dashboard"""
    # Get warranty statistics
    total_products = Product.query.filter_by(user_id=current_user.id, is_deleted=False).count()
    
    active_warranties = Product.query.filter(
        Product.user_id == current_user.id,
        Product.is_deleted == False,
        Product.warranty_expiry > datetime.utcnow()
    ).count()
    
    expired_warranties = total_products - active_warranties
    
    # Get ticket statistics
    open_tickets = Ticket.query.filter(
        Ticket.customer_id == current_user.id,
        Ticket.is_deleted == False,
        Ticket.status.in_(['open', 'in_progress', 'waiting_for_parts'])
    ).count()
    
    completed_tickets = Ticket.query.filter(
        Ticket.customer_id == current_user.id,
        Ticket.is_deleted == False,
        Ticket.status.in_(['completed', 'closed'])
    ).count()
    
    # Get recent tickets
    recent_tickets = Ticket.query.filter(
        Ticket.customer_id == current_user.id,
        Ticket.is_deleted == False
    ).order_by(Ticket.created_at.desc()).limit(5).all()
    
    # Get expiring soon products
    expiring_soon = Product.query.filter(
        Product.user_id == current_user.id,
        Product.is_deleted == False,
        Product.warranty_expiry > datetime.utcnow(),
        Product.warranty_expiry <= datetime.utcnow() + timedelta(days=30)
    ).all()
    
    return render_template('customer/dashboard.html',
        total_products=total_products,
        active_warranties=active_warranties,
        expired_warranties=expired_warranties,
        open_tickets=open_tickets,
        completed_tickets=completed_tickets,
        recent_tickets=recent_tickets,
        expiring_soon=expiring_soon
    )

@customer_bp.route('/products')
@login_required
@customer_required
def products():
    """List all products"""
    page = request.args.get('page', 1, type=int)
    products = Product.query.filter_by(user_id=current_user.id, is_deleted=False).paginate(page=page, per_page=10)
    
    return render_template('customer/products.html', products=products)

@customer_bp.route('/products/add', methods=['GET', 'POST'])
@login_required
@customer_required
def add_product():
    """Add new product"""
    form = ProductForm()
    if form.validate_on_submit():
        try:
            # Calculate warranty expiry
            warranty_expiry = form.purchase_date.data + timedelta(days=30*form.warranty_months.data)
            
            product = Product(
                product_name=form.product_name.data,
                brand=form.brand.data,
                category=form.category.data,
                serial_number=form.serial_number.data,
                purchase_date=form.purchase_date.data,
                warranty_months=form.warranty_months.data,
                warranty_expiry=warranty_expiry,
                description=form.description.data,
                user_id=current_user.id
            )
            
            # Handle invoice image if uploaded
            if form.invoice_image.data:
                upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'products')
                os.makedirs(upload_folder, exist_ok=True)
                raw = form.invoice_image.data
                filename = secure_filename(f"invoice_{current_user.id}_{int(datetime.utcnow().timestamp())}.{raw.filename.split('.')[-1]}")
                save_path = os.path.join(upload_folder, filename)
                raw.save(save_path)
                # Store relative path to serve via static
                product.invoice_image = f"uploads/products/{filename}"
            
            db.session.add(product)
            db.session.commit()
            
            flash('Product added successfully!', 'success')
            return redirect(url_for('customer.products'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding product: {str(e)}', 'danger')
    
    return render_template('customer/add_product.html', form=form)


@customer_bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
@customer_required
def edit_product(product_id):
    """Edit an existing product"""
    product = Product.query.get_or_404(product_id)
    if product.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('customer.products'))

    form = ProductForm()
    if form.validate_on_submit():
        # ensure serial number stays unique when changed
        if product.serial_number != form.serial_number.data:
            existing = Product.query.filter_by(serial_number=form.serial_number.data).first()
            if existing and existing.id != product.id:
                flash('Another product with that serial number already exists.', 'danger')
                return redirect(url_for('customer.edit_product', product_id=product.id))
        try:
            product.product_name = form.product_name.data
            product.brand = form.brand.data
            product.category = form.category.data
            product.serial_number = form.serial_number.data
            product.purchase_date = form.purchase_date.data
            product.warranty_months = form.warranty_months.data
            product.warranty_expiry = form.purchase_date.data + timedelta(days=30*form.warranty_months.data)
            product.description = form.description.data

            # Handle invoice image replacement (only if a new file was uploaded)
            if form.invoice_image.data and hasattr(form.invoice_image.data, 'filename'):
                upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'products')
                os.makedirs(upload_folder, exist_ok=True)
                raw = form.invoice_image.data
                filename = secure_filename(f"invoice_{current_user.id}_{int(datetime.utcnow().timestamp())}.{raw.filename.split('.')[-1]}")
                save_path = os.path.join(upload_folder, filename)
                raw.save(save_path)
                # Optionally remove old file
                try:
                    if product.invoice_image:
                        old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], product.invoice_image.replace('uploads/', '').replace('/', os.sep))
                        if os.path.exists(old_path):
                            os.remove(old_path)
                except Exception:
                    pass
                product.invoice_image = f"uploads/products/{filename}"

            db.session.commit()
            flash('Product updated successfully!', 'success')
            return redirect(url_for('customer.product_detail', product_id=product.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating product: {str(e)}', 'danger')
    elif request.method == 'GET':
        # Pre-populate form fields on GET request
        form.product_name.data = product.product_name
        form.brand.data = product.brand
        form.category.data = product.category
        form.serial_number.data = product.serial_number
        form.purchase_date.data = product.purchase_date.date() if product.purchase_date else None
        form.warranty_months.data = product.warranty_months
        form.description.data = product.description

    return render_template('customer/edit_product.html', form=form, product=product)


@customer_bp.route('/products/<int:product_id>/delete', methods=['POST'])
@login_required
@customer_required
def delete_product(product_id):
    """Soft-delete a product"""
    product = Product.query.get_or_404(product_id)
    if product.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('customer.products'))

    try:
        # Soft delete
        product.is_deleted = True
        db.session.commit()
        flash('Product deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting product: {str(e)}', 'danger')

    return redirect(url_for('customer.products'))

@customer_bp.route('/products/<int:product_id>')
@login_required
@customer_required
def product_detail(product_id):
    """View product details"""
    product = Product.query.get_or_404(product_id)
    
    if product.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('customer.products'))
    
    # Get related tickets
    tickets = Ticket.query.filter(
        Ticket.product_id == product_id,
        Ticket.is_deleted == False
    ).order_by(Ticket.created_at.desc()).all()
    
    return render_template('customer/product_detail.html', product=product, tickets=tickets)

@customer_bp.route('/tickets')
@login_required
@customer_required
def tickets():
    """List all tickets"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    
    query = Ticket.query.filter(
        Ticket.customer_id == current_user.id,
        Ticket.is_deleted == False
    )
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    tickets = query.order_by(Ticket.created_at.desc()).paginate(page=page, per_page=10)
    
    # determine which of the paginated tickets already have feedback
    ticket_ids = [t.id for t in tickets.items]
    if ticket_ids:
        existing = Feedback.query.filter(Feedback.ticket_id.in_(ticket_ids)).all()
        feedback_ids = {f.ticket_id for f in existing}
    else:
        feedback_ids = set()

    return render_template('customer/tickets.html', tickets=tickets, status_filter=status_filter,
                           feedback_ids=feedback_ids)

@customer_bp.route('/tickets/raise', methods=['GET', 'POST'])
@login_required
@customer_required
def raise_ticket():
    """Raise new repair ticket"""
    form = TicketForm()
    
    # Populate products dropdown
    form.product_id.choices = [
        (p.id, f'{p.product_name} ({p.serial_number})')
        for p in Product.query.filter_by(user_id=current_user.id, is_deleted=False).all()
    ]
    
    if form.validate_on_submit():
        try:
            product = Product.query.get(form.product_id.data)
            
            if not product or product.user_id != current_user.id:
                flash('Invalid product selected', 'danger')
                return redirect(url_for('customer.raise_ticket'))
            
            # Check warranty status
            warranty_expired = product.warranty_expiry < datetime.utcnow()
            repair_type = form.repair_type.data
            
            # Validate repair type selection
            if warranty_expired and repair_type == 'warranty':
                flash('This product warranty has expired. Please select "Paid Repair" option.', 'warning')
                return redirect(url_for('customer.raise_ticket'))
            
            if not warranty_expired and repair_type == 'paid':
                flash('Your product warranty is still active. Select "Covered Under Warranty" to avoid charges.', 'info')
            
            # Create ticket
            ticket = Ticket(
                customer_id=current_user.id,
                product_id=form.product_id.data,
                issue_description=form.issue_description.data,
                priority=form.priority.data,
                is_warranty_covered=(repair_type == 'warranty' and not warranty_expired)
            )
            ticket.generate_ticket_number()
            
            db.session.add(ticket)
            db.session.commit()
            
            coverage = 'Warranty Covered' if ticket.is_warranty_covered else 'Paid Repair'
            flash(f'Repair ticket {ticket.ticket_number} created successfully! ({coverage})', 'success')
            return redirect(url_for('customer.ticket_detail', ticket_id=ticket.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating ticket: {str(e)}', 'danger')
    
    return render_template('customer/raise_ticket.html', form=form)

@customer_bp.route('/tickets/<int:ticket_id>')
@login_required
@customer_required
def ticket_detail(ticket_id):
    """View ticket details"""
    ticket = Ticket.query.get_or_404(ticket_id)
    
    if ticket.customer_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('customer.tickets'))
    
    # Get repair notes
    repair_notes = RepairNote.query.filter_by(ticket_id=ticket_id).order_by(RepairNote.created_at.desc()).all()
    
    # Get feedback if exists
    feedback = Feedback.query.filter_by(ticket_id=ticket_id).first()
    
    return render_template('customer/ticket_detail.html', ticket=ticket, repair_notes=repair_notes, feedback=feedback)


@customer_bp.route('/tickets/<int:ticket_id>/pay', methods=['GET', 'POST'])
@login_required
@customer_required
def pay_ticket(ticket_id):
    """Mock UPI payment for paid repairs after completion"""
    ticket = Ticket.query.get_or_404(ticket_id)
    if ticket.customer_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('customer.tickets'))

    if ticket.status not in ['completed', 'closed']:
        flash('Payment is only available after repair is completed.', 'warning')
        return redirect(url_for('customer.ticket_detail', ticket_id=ticket_id))

    if ticket.is_warranty_covered:
        flash('This ticket is covered by warranty. No payment required.', 'info')
        return redirect(url_for('customer.ticket_detail', ticket_id=ticket_id))

    if ticket.is_paid:
        flash('Payment already processed for this ticket.', 'info')
        return redirect(url_for('customer.ticket_detail', ticket_id=ticket_id))

    form = PaymentForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                # mock payment processing
                ticket.is_paid = True
                ticket.status = 'closed'
                ticket.updated_at = datetime.utcnow()

                act = ActivityLog(
                    user_id=current_user.id,
                    action='payment_processed',
                    resource_type='ticket',
                    resource_id=ticket_id,
                    changes=f'Customer paid amount={ticket.repair_cost} via {form.upi_id.data}'
                )
                db.session.add(act)
                db.session.commit()
                flash('Payment successful (mock). Thank you!', 'success')
                return redirect(url_for('customer.ticket_detail', ticket_id=ticket_id))
            except Exception as e:
                db.session.rollback()
                flash(f'Payment failed: {str(e)}', 'danger')
        else:
            # show form with validation errors
            return render_template('customer/pay_ticket.html', ticket=ticket, form=form)

    form = PaymentForm()
    return render_template('customer/pay_ticket.html', ticket=ticket, form=form)

@customer_bp.route('/tickets/<int:ticket_id>/feedback', methods=['GET', 'POST'])
@login_required
@customer_required
def add_feedback(ticket_id):
    """Add feedback to completed ticket"""
    ticket = Ticket.query.get_or_404(ticket_id)
    
    if ticket.customer_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('customer.tickets'))
    
    if ticket.status not in ['completed', 'closed']:
        flash('Can only add feedback to completed tickets', 'warning')
        return redirect(url_for('customer.ticket_detail', ticket_id=ticket_id))
    
    # Check if feedback already exists
    existing_feedback = Feedback.query.filter_by(ticket_id=ticket_id).first()
    if existing_feedback:
        flash('Feedback already exists for this ticket', 'info')
        return redirect(url_for('customer.ticket_detail', ticket_id=ticket_id))
    
    form = FeedbackForm()
    if form.validate_on_submit():
        try:
            feedback = Feedback(
                ticket_id=ticket_id,
                user_id=current_user.id,
                rating=form.rating.data,
                comment=form.comment.data
            )
            db.session.add(feedback)
            db.session.commit()
            flash('Feedback added successfully!', 'success')
            return redirect(url_for('customer.ticket_detail', ticket_id=ticket_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding feedback: {str(e)}', 'danger')
    
    return render_template('customer/add_feedback.html', form=form, ticket=ticket)

@customer_bp.route('/search')
@login_required
@customer_required
def search():
    """Search products and tickets"""
    form = SearchForm()
    results = {'products': [], 'tickets': []}
    
    if form.validate_on_submit() and form.search_query.data:
        search_term = f"%{form.search_query.data}%"
        
        # Search products
        results['products'] = Product.query.filter(
            Product.user_id == current_user.id,
            Product.is_deleted == False,
            (Product.product_name.ilike(search_term) | 
             Product.brand.ilike(search_term) |
             Product.serial_number.ilike(search_term))
        ).all()
        
        # Search tickets
        results['tickets'] = Ticket.query.filter(
            Ticket.customer_id == current_user.id,
            Ticket.is_deleted == False,
            (Ticket.ticket_number.ilike(search_term) |
             Ticket.issue_description.ilike(search_term))
        ).all()
    
    return render_template('customer/search.html', form=form, results=results)
