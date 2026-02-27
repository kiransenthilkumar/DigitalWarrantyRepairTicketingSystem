# Digital Warranty & Repair Ticketing System
A compact single-file reference for this Flask project. This file replaces the separate markdown docs and contains the essential information: features, workflows, pages/routes, seed/demo credentials, and setup/run instructions.

---
## Project Summary

Flask-based web application to register products, track warranties and handle repair tickets with three roles: `admin`, `technician`, and `customer`.

Core capabilities:
- Multi-role authentication and RBAC
- Product & warranty registration with expiry tracking
- Repair ticket creation, assignment, status updates and repair notes
- Technician performance metrics and customer feedback (1–5 star)
- Admin reporting, user management and activity logs

---
## Features (high level)

- User management: registration, profiles, password change, roles
- Product registry: serial numbers, invoices, warranty duration/expiry
- Repair ticketing: auto-generated ticket numbers, images, priorities
- Repair notes & timeline per ticket
- Feedback & rating system
- Admin dashboards & reports
- Technician dashboards & performance
- Search, filtering and pagination

---
## Workflows

Customer:
1. Register / login
2. Add product with purchase date + warranty months
3. Raise a ticket for a product
4. Track ticket and view technician notes
5. Submit feedback on completed ticket

Technician:
1. View assigned tickets
2. Update ticket status (in_progress, completed, closed)
3. Add repair notes and final repair cost
4. View performance metrics and ratings

Admin:
1. View system KPIs
2. Manage users & roles
3. Assign technicians to tickets
4. Generate warranty/technician reports
5. Audit activity logs

---
## Seed Data & Demo Credentials

This repository includes `seed_data.py` which creates sample users and records when run. Default/demo credentials created by the seed script and on first run:

- Admin: `admin@example.com` / `admin123`
- Technicians: `tech1@example.com`, `tech2@example.com`, `tech3@example.com` (password `techpass`)
- Customers: `customer1@example.com` … `customer5@example.com` (password `custpass`)

To run the seed script (after env & DB initialized):

```bash
python seed_data.py
```

Security: Immediately change the admin password in production.

---

## Setup & Run Guide (quick)

Prerequisites:
- Python 3.8+
- pip

Quick start (Windows):

```powershell
cd "d:\kiran\Final Year Projects\PYTHON PROJECTS\DigitalWarrantyRepairTicketingSystem"
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# Edit .env as needed (SECRET_KEY, DATABASE_URL if using Postgres)
python app.py
```

Then open: http://localhost:5000

Default admin login: `admin@example.com` / `admin123` (change immediately).

Notes:
- First run will create SQLite DB at `instance/warranty_system.db` and default admin (unless DB exists).
- To use PostgreSQL in production, set `DATABASE_URL` in `.env` and deploy via Render/Gunicorn.

Database migration commands (if using Flask-Migrate):

```bash
flask db migrate
flask db upgrade
```

---

## Deployment (summary)

Recommended: Render or any host supporting Python + PostgreSQL.

Essential environment vars for production:
- `FLASK_ENV=production`
- `SECRET_KEY` (strong random value)
- `DATABASE_URL` (Postgres connection string)

Start command for production: `gunicorn app:app`

---

## Troubleshooting (common)

- If `ModuleNotFoundError`, ensure virtualenv is active and `pip install -r requirements.txt` completed.
- If `No such table`, run `python app.py` to initialize DB or run migrations.
- If port 5000 in use, run `flask run --port 5001` or free the port.

---

## Where to find things

- App entry: `app.py`
- Config: `config.py`
- Models: `models.py`
- Forms: `forms.py`
- Routes/blueprints: `routes/` (auth, customer, technician, admin)
- Templates: `templates/` (organized by role)
- Static assets: `static/` (css, js)

---

If you'd like I can:
- run the seed script now, or
- commit these file changes, or
- restore any deleted doc back into a single archived file.


# Digital Warranty & Repair Ticketing System

A comprehensive Flask-based web application for managing product warranties and repair tickets. This system enables customers to digitally register warranties, track products, and raise repair/service tickets while providing technicians and administrators with complete oversight of the repair process.

## 🌟 Features

### Core Modules

1. **User Management**
   - Multi-role authentication (Customer, Technician, Admin)
   - User registration and profile management
   - Password security with hashing
   - Role-based access control (RBAC)

2. **Warranty Management**
   - Digital warranty registration for products
   - Warranty expiry tracking with countdown
   - Automatic warranty status classification (Active, Expiring Soon, Expired)
   - Warranty expiration notifications

3. **Product Registry**
   - Product registration with details (name, brand, serial number)
   - Purchase date and warranty duration tracking
   - Invoice image upload support
   - Product categorization

4. **Repair Ticketing System**
   - Automatic ticket number generation (TKT-YYYYMMDD-XXXXXX)
   - Ticket creation with issue description and images
   - Priority-based ticket classification
   - Current status tracking
   - Repair cost and duration estimation

5. **Technician Dashboard**
   - Assigned ticket queue
   - Ticket status updates
   - Repair notes and documentation
   - Performance metrics (completion rate, customer ratings, total repair value)

6. **Admin Dashboard**
   - Comprehensive system overview
   - User management and role assignment
   - Ticket assignment to technicians
   - Activity logging and audit trails
   - Advanced reporting (status distribution, technician performance, warranty statistics)
   - Global search functionality

## 🏗️ Project Structure

```
DigitalWarrantyRepairTicketingSystem/
├── app.py                          # Flask application factory
├── config.py                       # Configuration management (Dev/Prod/Test)
├── extensions.py                   # Flask extensions initialization
├── models.py                       # SQLAlchemy ORM models
├── forms.py                        # WTForms validation classes
├── requirements.txt                # Python dependencies
├── Procfile                        # Render deployment configuration
├── .env.example                    # Environment variables template
├── .gitignore                      # Git ignore rules
│
├── routes/                         # Route handlers (blueprints)
│   ├── __init__.py                 # Blueprint registration
│   ├── auth.py                     # Authentication routes
│   ├── customer.py                 # Customer feature routes
│   ├── technician.py               # Technician feature routes
│   └── admin.py                    # Admin feature routes
│
├── templates/                      # Jinja2 HTML templates
│   ├── base.html                   # Master template
│   ├── auth/
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── profile.html
│   │   ├── edit_profile.html
│   │   └── change_password.html
│   ├── customer/
│   │   ├── dashboard.html
│   │   ├── products.html
│   │   ├── add_product.html
│   │   ├── product_detail.html
│   │   ├── tickets.html
│   │   ├── raise_ticket.html
│   │   ├── ticket_detail.html
│   │   ├── add_feedback.html
│   │   └── search.html
│   ├── admin/
│   │   ├── dashboard.html
│   │   ├── users.html
│   │   ├── user_detail.html
│   │   ├── edit_user.html
│   │   ├── tickets.html
│   │   ├── ticket_detail.html
│   │   ├── assign_technician.html
│   │   ├── activity_logs.html
│   │   ├── report_overview.html
│   │   ├── report_technician.html
│   │   ├── report_warranty.html
│   │   └── search.html
│   ├── technician/
│   │   ├── dashboard.html
│   │   ├── tickets.html
│   │   ├── ticket_detail.html
│   │   ├── update_status.html
│   │   ├── add_note.html
│   │   ├── performance.html
│   │   └── search.html
│   └── errors/
│       ├── 404.html
│       ├── 403.html
│       └── 500.html
│
├── static/                         # Static assets
│   ├── css/
│   │   └── style.css               # Custom Bootstrap styling
│   └── js/
│       └── main.js                 # JavaScript utilities
│
├── instance/                       # Instance-specific files (not in git)
│   └── warranty_system.db          # SQLite database
│
└── migrations/                     # Database migrations (Flask-Migrate)
```

## 🗄️ Database Models

### User
- User authentication and profile information
- Roles: customer, technician, admin
- Password hashing with Werkzeug security
- Soft delete support with is_deleted flag

### Product
- Product details and warranty information
- Links to customer through user_id
- Automatic warranty expiry calculation
- Warranty status properties (active, expiring_soon, expired)

### Ticket
- Repair ticket information
- Links to Product and Customer (User)
- Technician assignment support
- Multiple images and repair notes
- Priority levels (low, medium, high, critical)
- Status tracking (open, in_progress, completed, closed, cancelled)

### RepairNote
- Technician notes and updates on tickets
- Links to Ticket and User (author)
- Timestamped for audit trail

### Feedback
- Customer ratings on completed repairs
- 1-5 star rating system
- Optional comment field
- Links to Ticket and User

### ActivityLog
- Audit trail of admin actions
- Tracks action type, resource, and changes
- JSON field for detailed change tracking

### WarrantyExpirerNotification
- Warranty expiration alerts
- Tracks notification sending and reading

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- pip (Python package installer)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd DigitalWarrantyRepairTicketingSystem
   ```

2. **Create virtual environment:**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database:**
   ```bash
   python app.py  # Creates tables and default admin user
   ```

6. **Run the application:**
   ```bash
   flask run
   ```
   Application will be available at http://localhost:5000

## 🔐 Default Credentials

The system creates a default admin user on first run:
- **Email:** admin@example.com
- **Password:** admin123
- **Role:** Admin

⚠️ **Security Note:** Change admin password immediately after first login in production.

## 📝 User Roles

### Customer
- Register products and warranties
- View warranty status and expiry
- Create and track repair tickets
- Submit feedback on repairs
- View repair progress and notes

### Technician
- View assigned tickets
- Update ticket status
- Add repair notes and documentation
- View customer feedback and ratings
- Access performance metrics

### Admin
- Full system access
- User management (create, edit, deactivate)
- Technician assignment to tickets
- Comprehensive reporting
- Activity logging and auditing
- Global search functionality

## 🛠️ Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Framework | Flask | 3.0.0 |
| ORM | SQLAlchemy | 2.0.23 |
| Auth | Flask-Login | 0.6.3 |
| Forms | WTForms + Flask-WTF | 3.1.1 + 1.2.1 |
| Database | SQLite (Dev) / PostgreSQL (Prod) | - |
| Frontend | Bootstrap | 5.3.0 |
| Templating | Jinja2 | Built-in |
| Server | Gunicorn | 21.2.0 |
| Security | Werkzeug | 3.0.1 |

## 📊 Key Features Explained

### Automatic Ticket Number Generation
```
Format: TKT-YYYYMMDD-XXXXXX
Example: TKT-20240115-A7F2B1
```
- Date-based prefix for easy sorting
- Unique 6-character suffix for million+ tickets
- Improves audit trail clarity

### Warranty Tracking
- Automatic expiry calculation from purchase date + warranty duration
- Visual status indicators (Active/Expiring Soon/Expired)
- Days remaining countdown
- Notification system for expiring warranties

### Role-Based Access Control
- Decorator-based route protection
- User roles determine available features
- Soft delete for data preservation
- Activity logging for admin actions

### Performance Metrics
Technicians can view:
- Completion rate (completed/assigned tickets)
- Average customer rating (1-5 star)
- Total repair value
- Recent activity

### Search & Filters
- Full-text search for users, tickets, products
- Filter by status, priority, date range
- Global search from admin dashboard
- Person-specific search for technicians

## 🔄 Workflow Example

**Customer Journey:**
1. Register → Create account
2. Register Product → Add warranty info
3. Report Issue → Create ticket with images
4. Track Progress → View technician's repair notes
5. Rate Repair → Submit 1-5 star feedback

**Technician Workflow:**
1. View Tickets → See assigned queue
2. Accept Ticket → Mark as in-progress
3. Document Work → Add repair notes with timestamps
4. Complete Ticket → Update status and repair cost
5. View Rating → See customer feedback

**Admin Oversight:**
1. Monitor System → View dashboard KPIs
2. Manage Users → Create/edit users and roles
3. Assign Work → Distribute tickets to technicians
4. View Reports → Generate system statistics
5. Audit Activity → Review action logs

## 🌐 Deployment

### Render Deployment

1. **Prepare code:**
   ```bash
   git push <your-repo>
   ```

2. **Create Render service:**
   - Connect GitHub repository
   - Set environment to Python 3.9+
   - Set start command: `gunicorn app:app`

3. **Configure environment variables on Render:**
   - `FLASK_ENV=production`
   - `SECRET_KEY=<your-secret-key>`
   - `DATABASE_URL=<postgresql-url>`
   - Other variables as needed

4. **Deploy:**
   - Push to git triggers automatic deployment
   - Monitor logs for deployment status

### PostgreSQL Setup for Production
```
1. Create PostgreSQL database on Neon or similar provider
2. Update DATABASE_URL in environment variables
3. Application will create tables on first run
```

## 📈 API Routes Summary

### Authentication Routes
- `POST /register` - User registration
- `POST /login` - User login
- `GET /logout` - User logout
- `GET /profile` - View profile
- `GET/POST /edit-profile` - Edit profile
- `GET/POST /change-password` - Change password

### Customer Routes (15+ endpoints)
- Warranty and product management
- Ticket creation and tracking
- Feedback submission
- Search functionality

### Technician Routes (9+ endpoints)
- Ticket assignment viewing
- Status updates
- Repair notes
- Performance metrics

### Admin Routes (16+ endpoints)
- User management
- Ticket administration
- Technician assignment
- Comprehensive reporting
- Activity auditing

## 🧪 Testing

Run the application in development:
```bash
export FLASK_ENV=development  # or set FLASK_ENV=development on Windows
flask run
```

Access different roles:
- Admin: admin@example.com / admin123
- Create customers/technicians through registration

## 📚 Additional Documentation

### Making Changes to the Database Schema
Database schema is defined in `models.py`. After making changes:
```bash
flask db migrate
flask db upgrade
```

### Customizing Styling
- Main stylesheet: `static/css/style.css`
- Bootstrap 5 classes used throughout
- CSS variables for consistent theming

### Form Validation
- All forms in `forms.py` include CSRF protection via Flask-WTF
- Custom validators for duplicate checking (username, email, serial number)
- Email validation through email_validator library

## 🐛 Troubleshooting

**Issue: "ModuleNotFoundError"**
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt`

**Issue: "Database is locked"**
- SQLite development only - stop Flask app
- For production, use PostgreSQL

**Issue: "Missing templates" error**
- Check template file names match those used in `render_template()`
- Ensure templates are in `templates/` directory

## 🤝 Contributing

Future enhancement areas:
- Cloudinary integration for image storage
- Chart.js for advanced dashboards
- Email notifications for updates
- JWT authentication support
- Mobile app integration
- Advanced analytics

## 📄 License

This project is designed for academic purposes.

## 📧 Support

For issues or questions, refer to the code comments or contact the development team.

---

**Version:** 1.0.0  
**Last Updated:** January 2024  
**Framework:** Flask 3.0.0  
**Python:** 3.8+









.\quickstart.bat