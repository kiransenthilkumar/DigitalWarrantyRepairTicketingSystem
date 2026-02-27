"""Seed sample data into the warranty system database
Run: python seed_data.py
"""
from app import create_app
from extensions import db
from models import User, Product, Ticket, RepairNote, Feedback, ActivityLog
from datetime import datetime, timedelta
import random

app = create_app()

with app.app_context():
    db.create_all()

    # Create admin if not exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', email='admin@example.com', full_name='Administrator', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)

    # Create technicians
    techs = []
    for i in range(1,4):
        username = f'tech{i}'
        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(username=username, email=f'{username}@example.com', full_name=f'Tech {i}', role='technician')
            user.set_password('techpass')
            db.session.add(user)
        techs.append(user)

    # Create customers
    customers = []
    for i in range(1,6):
        username = f'customer{i}'
        email = f'{username}@example.com'
        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(username=username, email=email, full_name=f'Customer {i}', role='customer')
            user.set_password('custpass')
            db.session.add(user)
        customers.append(user)

    db.session.commit()

    # Create products for each customer
    brands = ['Dell','Samsung','Apple','HP','LG']
    categories = ['Laptop','Mobile','TV','Appliance']
    products = []
    for idx, cust in enumerate(customers, start=1):
        serial = f'SN{1000+idx}'
        prod = Product.query.filter_by(serial_number=serial).first()
        if not prod:
            purchase_date = datetime.utcnow() - timedelta(days=random.randint(30, 400))
            warranty_months = random.choice([12,24,36])
            warranty_expiry = purchase_date + timedelta(days=30*warranty_months)
            prod = Product(product_name=f'{brands[idx%len(brands)]} Device {idx}', brand=brands[idx%len(brands)], category=categories[idx%len(categories)], serial_number=serial, purchase_date=purchase_date, warranty_months=warranty_months, warranty_expiry=warranty_expiry, description='Sample seeded product', user_id=cust.id)
            db.session.add(prod)
        products.append(prod)

    db.session.commit()

    # Create tickets - include a mix of statuses and ensure at least one expired product ticket
    tickets = []
    for idx, p in enumerate(products, start=1):
        t = Ticket(
            product_id=p.id,
            customer_id=p.user_id,
            issue_description='Device not powering on or intermittent failures.',
            priority=random.choice(['low','medium','high'])
        )
        t.generate_ticket_number()
        # force one expired ticket for the first product
        if idx == 1:
            # expired product with completed, unpaid ticket for testing payment flow
            t.status = 'completed'
            t.technician_id = random.choice(techs).id
            t.is_warranty_covered = False
            t.is_paid = False
            t.repair_cost = round(random.uniform(150, 400), 2)
        elif idx == 2:
            # keep an example paid completed ticket
            t.status = 'completed'
            t.technician_id = random.choice(techs).id
            t.is_warranty_covered = False
            t.is_paid = True
        else:
            t.status = random.choice(['open','in_progress','completed'])
            if t.status != 'open':
                t.technician_id = random.choice(techs).id
            # determine warranty coverage based on product expiry
            t.is_warranty_covered = p.warranty_expiry > datetime.utcnow()
            if t.status == 'completed' and not t.is_warranty_covered:
                t.is_paid = True
        db.session.add(t)
        tickets.append(t)

    # make sure tickets have ids before using them in related objects
    db.session.flush()

    # Add repair notes and feedback for some tickets
    for t in tickets:
        if t.technician_id:
            note = RepairNote(ticket_id=t.id, user_id=t.technician_id, note_text='Initial diagnostic performed. Needs parts replacement.', note_type='diagnosis')
            db.session.add(note)
        if t.status == 'completed':
            fb = Feedback(ticket_id=t.id, user_id=t.customer_id, rating=random.randint(3,5), comment='Service completed satisfactorily')
            db.session.add(fb)

    # Activity logs
    log = ActivityLog(user_id=admin.id if admin else 1, action='seed_data', resource_type='script', resource_id=None, changes='{"note": "Seed data created"}')
    db.session.add(log)

    db.session.commit()
    print('Seed data created successfully')