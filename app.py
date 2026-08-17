import os
import sqlite3
import random
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
import joblib
import numpy as np

app = Flask(__name__)
app.secret_key = 'smartpost_secret_key_2026_production_grade'

DB_DIR = os.path.join(app.root_path, 'database')
DB_PATH = os.path.join(DB_DIR, 'smartpost.db')
MODEL_PATH = os.path.join(app.root_path, 'model', 'delivery_delay_model.pkl')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create Tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT NOT NULL,
            address TEXT NOT NULL,
            city TEXT NOT NULL,
            state TEXT NOT NULL,
            postal_code TEXT NOT NULL,
            id_proof_type TEXT NOT NULL,
            id_proof_number TEXT NOT NULL,
            registration_date TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            username TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT NOT NULL,
            designation TEXT NOT NULL,
            branch TEXT NOT NULL,
            joining_date TEXT NOT NULL,
            status TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service_code TEXT UNIQUE NOT NULL,
            service_name TEXT NOT NULL,
            description TEXT NOT NULL,
            base_fee REAL NOT NULL,
            per_kg_fee REAL NOT NULL,
            estimated_days INTEGER NOT NULL,
            delivery_category TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shipments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tracking_number TEXT UNIQUE NOT NULL,
            sender_name TEXT NOT NULL,
            sender_phone TEXT NOT NULL,
            sender_address TEXT NOT NULL,
            sender_city TEXT NOT NULL,
            sender_state TEXT NOT NULL,
            sender_postal_code TEXT NOT NULL,
            receiver_name TEXT NOT NULL,
            receiver_phone TEXT NOT NULL,
            receiver_address TEXT NOT NULL,
            receiver_city TEXT NOT NULL,
            receiver_state TEXT NOT NULL,
            receiver_postal_code TEXT NOT NULL,
            service_type TEXT NOT NULL,
            item_type TEXT NOT NULL,
            weight REAL NOT NULL,
            quantity INTEGER NOT NULL,
            declared_value REAL NOT NULL,
            base_charge REAL NOT NULL,
            weight_charge REAL NOT NULL,
            service_charge REAL NOT NULL,
            additional_charge REAL NOT NULL,
            total_amount REAL NOT NULL,
            booking_date TEXT NOT NULL,
            expected_delivery_date TEXT NOT NULL,
            status TEXT NOT NULL,
            current_location TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shipment_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tracking_number TEXT NOT NULL,
            status TEXT NOT NULL,
            location TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            remarks TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tracking_number TEXT NOT NULL,
            amount REAL NOT NULL,
            payment_mode TEXT NOT NULL,
            payment_status TEXT NOT NULL,
            payment_date TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            tracking_number TEXT NOT NULL,
            complaint_type TEXT NOT NULL,
            description TEXT NOT NULL,
            priority TEXT NOT NULL,
            status TEXT NOT NULL,
            created_date TEXT NOT NULL,
            resolution TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            status TEXT NOT NULL,
            created_date TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tracking_number TEXT,
            service_type TEXT NOT NULL,
            weight REAL NOT NULL,
            distance REAL NOT NULL,
            risk_level TEXT NOT NULL,
            confidence REAL NOT NULL,
            prediction_result TEXT NOT NULL,
            created_date TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contact_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            message TEXT NOT NULL,
            created_date TEXT NOT NULL
        )
    ''')

    # Seed Default Admin & Employee Users
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        admin_pass = generate_password_hash('admin123')
        emp_pass = generate_password_hash('employee123')
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute("INSERT INTO users (username, password_hash, role, name, email, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                       ('admin', admin_pass, 'Admin', 'Chief Postmaster Admin', 'admin@smartpost.gov', now_str))
        cursor.execute("INSERT INTO users (username, password_hash, role, name, email, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                       ('employee', emp_pass, 'Employee', 'Postal Assistant Employee', 'employee@smartpost.gov', now_str))

    # Seed Services
    cursor.execute("SELECT COUNT(*) FROM services")
    if cursor.fetchone()[0] == 0:
        services_data = [
            ('ORD01', 'Ordinary Post', 'Standard economical mail transmission across domestic locations.', 15.00, 10.00, 5, 'Domestic Mail'),
            ('SPD02', 'Speed Post', 'Priority express delivery service with time-bound fulfillment.', 35.00, 20.00, 2, 'Express Mail'),
            ('REG03', 'Registered Post', 'Secure mail transmission with proof of booking and delivery record.', 25.00, 15.00, 4, 'Secure Mail'),
            ('PCL04', 'Parcel Delivery', 'Reliable medium-to-heavy package transport across regional hubs.', 30.00, 18.00, 4, 'Package Parcel'),
            ('EXP05', 'Express Parcel', 'Fast door-to-door parcel delivery for high priority items.', 50.00, 25.00, 2, 'Express Parcel'),
            ('INT06', 'International Parcel', 'Global postal dispatch to over 190 countries worldwide.', 100.00, 50.00, 7, 'International')
        ]
        cursor.executemany("INSERT INTO services (service_code, service_name, description, base_fee, per_kg_fee, estimated_days, delivery_category) VALUES (?, ?, ?, ?, ?, ?, ?)", services_data)

    # Seed Sample Customers
    cursor.execute("SELECT COUNT(*) FROM customers")
    if cursor.fetchone()[0] == 0:
        customers_data = [
            ('Alexander Wright', '+1 (555) 234-5678', 'alex.wright@email.com', '742 Evergreen Terrace', 'Springfield', 'OR', '97477', 'Driver License', 'DL-98765432', '2026-01-10 10:30:00'),
            ('Beatrice Vance', '+1 (555) 345-6789', 'b.vance@email.com', '124 Conch Street', 'Bikini Bottom', 'CA', '90210', 'National ID', 'NID-88219412', '2026-01-15 11:45:00'),
            ('Charles Montgomery', '+1 (555) 456-7890', 'cmontgomery@email.com', '1000 Mammon Lane', 'Springfield', 'OR', '97478', 'Passport', 'PASS-44129851', '2026-02-01 09:15:00'),
            ('Diana Prince', '+1 (555) 567-8901', 'diana.p@email.com', '45 Gateway Boulevard', 'Metropolis', 'NY', '10001', 'Passport', 'PASS-99882211', '2026-02-10 14:20:00'),
            ('Ethan Hunt', '+1 (555) 678-9012', 'ethan.hunt@email.com', '88 Mission Avenue', 'San Francisco', 'CA', '94102', 'Driver License', 'DL-11223344', '2026-03-05 16:00:00')
        ]
        cursor.executemany("INSERT INTO customers (full_name, phone, email, address, city, state, postal_code, id_proof_type, id_proof_number, registration_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", customers_data)

    # Seed Sample Employees
    cursor.execute("SELECT COUNT(*) FROM employees")
    if cursor.fetchone()[0] == 0:
        employees_data = [
            ('EMP-1001', 'Robert Davis', 'admin', '+1 (555) 111-2233', 'admin@smartpost.gov', 'Postmaster', 'Central General Post Office', '2024-01-15', 'ACTIVE'),
            ('EMP-1002', 'Sophia Martinez', 'employee', '+1 (555) 222-3344', 'employee@smartpost.gov', 'Postal Assistant', 'Central General Post Office', '2024-03-10', 'ACTIVE'),
            ('EMP-1003', 'Marcus Aurelius', 'marcus_a', '+1 (555) 333-4455', 'marcus@smartpost.gov', 'Supervisor', 'Northern Distribution Center', '2024-05-01', 'ACTIVE'),
            ('EMP-1004', 'Elena Rostova', 'elena_r', '+1 (555) 444-5566', 'elena@smartpost.gov', 'Counter Clerk', 'Metro City Branch', '2024-08-20', 'ACTIVE'),
            ('EMP-1005', 'David Miller', 'david_m', '+1 (555) 555-6677', 'david@smartpost.gov', 'Delivery Staff', 'Southside Depot', '2025-01-12', 'ACTIVE')
        ]
        cursor.executemany("INSERT INTO employees (employee_code, name, username, phone, email, designation, branch, joining_date, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", employees_data)

    # Seed Sample Shipments & Tracking & Payments
    cursor.execute("SELECT COUNT(*) FROM shipments")
    if cursor.fetchone()[0] == 0:
        shipments_seed = [
            ('SP202608010001', 'Alexander Wright', '+1 (555) 234-5678', '742 Evergreen Terrace', 'Springfield', 'OR', '97477',
             'Beatrice Vance', '+1 (555) 345-6789', '124 Conch Street', 'Bikini Bottom', 'CA', '90210',
             'Speed Post', 'Document', 0.5, 1, 100.0, 35.0, 10.0, 5.0, 0.0, 50.0,
             '2026-08-01 09:30:00', '2026-08-03 17:00:00', 'DELIVERED', 'Bikini Bottom Delivery Office'),

            ('SP202608050002', 'Charles Montgomery', '+1 (555) 456-7890', '1000 Mammon Lane', 'Springfield', 'OR', '97478',
             'Diana Prince', '+1 (555) 567-8901', '45 Gateway Boulevard', 'Metropolis', 'NY', '10001',
             'Express Parcel', 'Parcel', 4.2, 1, 450.0, 50.0, 105.0, 10.0, 0.0, 165.0,
             '2026-08-05 11:15:00', '2026-08-07 17:00:00', 'IN TRANSIT', 'Midwest Regional Sorting Hub'),

            ('SP202608100003', 'Ethan Hunt', '+1 (555) 678-9012', '88 Mission Avenue', 'San Francisco', 'CA', '94102',
             'Alexander Wright', '+1 (555) 234-5678', '742 Evergreen Terrace', 'Springfield', 'OR', '97477',
             'Registered Post', 'Letter', 0.2, 1, 50.0, 25.0, 3.0, 5.0, 0.0, 33.0,
             '2026-08-10 14:00:00', '2026-08-14 17:00:00', 'OUT FOR DELIVERY', 'Springfield West Delivery Post'),

            ('SP202608120004', 'Beatrice Vance', '+1 (555) 345-6789', '124 Conch Street', 'Bikini Bottom', 'CA', '90210',
             'Ethan Hunt', '+1 (555) 678-9012', '88 Mission Avenue', 'San Francisco', 'CA', '94102',
             'Parcel Delivery', 'Package', 8.5, 2, 800.0, 30.0, 153.0, 8.0, 8.0, 199.0,
             '2026-08-12 16:45:00', '2026-08-16 17:00:00', 'BOOKED', 'Central General Post Office'),

            ('SP202608140005', 'Diana Prince', '+1 (555) 567-8901', '45 Gateway Boulevard', 'Metropolis', 'NY', '10001',
             'Charles Montgomery', '+1 (555) 456-7890', '1000 Mammon Lane', 'Springfield', 'OR', '97478',
             'International Parcel', 'Package', 12.0, 1, 1500.0, 100.0, 600.0, 30.0, 15.0, 745.0,
             '2026-08-14 08:30:00', '2026-08-21 17:00:00', 'POSSIBLE DELAY', 'Customs Clearance Facility')
        ]
        
        cursor.executemany('''
            INSERT INTO shipments (tracking_number, sender_name, sender_phone, sender_address, sender_city, sender_state, sender_postal_code,
                                   receiver_name, receiver_phone, receiver_address, receiver_city, receiver_state, receiver_postal_code,
                                   service_type, item_type, weight, quantity, declared_value, base_charge, weight_charge, service_charge,
                                   additional_charge, total_amount, booking_date, expected_delivery_date, status, current_location)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', shipments_seed)

        # Seed tracking history
        tracking_events = [
            ('SP202608010001', 'BOOKED', 'Central Post Office', '2026-08-01 09:30:00', 'Shipment registered and payment verified.'),
            ('SP202608010001', 'ACCEPTED', 'Central Sorting Hub', '2026-08-01 12:00:00', 'Item received at origin sorting center.'),
            ('SP202608010001', 'DISPATCHED', 'Transit Hub', '2026-08-01 18:30:00', 'Dispatched via Express Air Route.'),
            ('SP202608020001', 'ARRIVED', 'Bikini Bottom Hub', '2026-08-02 08:15:00', 'Package processed at destination hub.'),
            ('SP202608030001', 'OUT FOR DELIVERY', 'Bikini Bottom Delivery Office', '2026-08-03 09:00:00', 'Assigned to delivery executive.'),
            ('SP202608030001', 'DELIVERED', 'Bikini Bottom Delivery Office', '2026-08-03 14:20:00', 'Signed and received by Beatrice Vance.'),

            ('SP202608050002', 'BOOKED', 'Springfield GPO', '2026-08-05 11:15:00', 'Parcel booked successfully.'),
            ('SP202608050002', 'DISPATCHED', 'Springfield Logistics Center', '2026-08-05 16:00:00', 'In transit to Metropolis hub.'),
            ('SP202608060002', 'IN TRANSIT', 'Midwest Regional Sorting Hub', '2026-08-06 10:45:00', 'Scanned at regional transit junction.'),

            ('SP202608100003', 'BOOKED', 'San Francisco Office', '2026-08-10 14:00:00', 'Registered post acceptance completed.'),
            ('SP202608110003', 'DISPATCHED', 'West Coast Transit Hub', '2026-08-11 09:00:00', 'En route to Springfield.'),
            ('SP202608130003', 'ARRIVED', 'Springfield West Office', '2026-08-13 15:30:00', 'Processed at local station.'),
            ('SP202608140003', 'OUT FOR DELIVERY', 'Springfield West Delivery Post', '2026-08-14 08:00:00', 'Out for recipient delivery.'),

            ('SP202608120004', 'BOOKED', 'Central General Post Office', '2026-08-12 16:45:00', 'Booking confirmed. Awaiting dispatch clearance.'),

            ('SP202608140005', 'BOOKED', 'Metropolis International Desk', '2026-08-14 08:30:00', 'International parcel received.'),
            ('SP202608150005', 'POSSIBLE DELAY', 'Customs Clearance Facility', '2026-08-15 11:00:00', 'AI Risk Flag: High workload & weather alert flagged delay risk.')
        ]
        cursor.executemany("INSERT INTO shipment_tracking (tracking_number, status, location, updated_at, remarks) VALUES (?, ?, ?, ?, ?)", tracking_events)

        # Seed Payments
        payments_seed = [
            ('SP202608010001', 50.0, 'Credit Card', 'COMPLETED', '2026-08-01 09:30:00'),
            ('SP202608050002', 165.0, 'UPI / Digital', 'COMPLETED', '2026-08-05 11:15:00'),
            ('SP202608100003', 33.0, 'Cash', 'COMPLETED', '2026-08-10 14:00:00'),
            ('SP202608120004', 199.0, 'Debit Card', 'COMPLETED', '2026-08-12 16:45:00'),
            ('SP202608140005', 745.0, 'Net Banking', 'COMPLETED', '2026-08-14 08:30:00')
        ]
        cursor.executemany("INSERT INTO payments (tracking_number, amount, payment_mode, payment_status, payment_date) VALUES (?, ?, ?, ?, ?)", payments_seed)

    # Seed Complaints
    cursor.execute("SELECT COUNT(*) FROM complaints")
    if cursor.fetchone()[0] == 0:
        complaints_data = [
            ('Charles Montgomery', 'SP202608050002', 'Delayed Shipment', 'Tracking hasn’t updated for 24 hours at Midwest Regional Hub.', 'HIGH', 'IN REVIEW', '2026-08-06 14:00:00', 'Support contacted logistics team for priority trace.'),
            ('Ethan Hunt', 'SP202608100003', 'Payment Issue', 'Duplicate charge appeared on digital invoice.', 'MEDIUM', 'RESOLVED', '2026-08-11 10:20:00', 'Refund processed for extra fee.'),
            ('Beatrice Vance', 'SP202608010001', 'Damaged Parcel', 'Outer box had slight dent upon delivery.', 'LOW', 'CLOSED', '2026-08-04 16:30:00', 'Inspected and verified inner document unharmed.'),
            ('Diana Prince', 'SP202608140005', 'Delayed Shipment', 'International custom clearance flag requires clarification.', 'CRITICAL', 'OPEN', '2026-08-15 13:45:00', None),
            ('Alexander Wright', 'SP202608120004', 'Other', 'Inquiry regarding package pickup scheduling.', 'LOW', 'OPEN', '2026-08-15 17:10:00', None)
        ]
        cursor.executemany("INSERT INTO complaints (customer_name, tracking_number, complaint_type, description, priority, status, created_date, resolution) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", complaints_data)

    # Seed Notifications
    cursor.execute("SELECT COUNT(*) FROM notifications")
    if cursor.fetchone()[0] == 0:
        notifs_data = [
            ('New Booking Received', 'Shipment SP202608140005 created successfully by Metropolis Desk.', 'UNREAD', '2026-08-14 08:31:00'),
            ('AI Delay Risk Alert', 'Shipment SP202608140005 flagged with High Delay Risk by AI engine.', 'UNREAD', '2026-08-15 11:02:00'),
            ('Shipment Delivered', 'Speed Post SP202608010001 delivered successfully to recipient.', 'READ', '2026-08-03 14:21:00'),
            ('New Complaint Logged', 'Critical complaint filed for tracking SP202608140005.', 'UNREAD', '2026-08-15 13:46:00'),
            ('System Update', 'SmartPost database and AI models synchronized successfully.', 'READ', '2026-08-16 00:00:00')
        ]
        cursor.executemany("INSERT INTO notifications (title, message, status, created_date) VALUES (?, ?, ?, ?)", notifs_data)

    # Seed Predictions
    cursor.execute("SELECT COUNT(*) FROM predictions")
    if cursor.fetchone()[0] == 0:
        preds_data = [
            ('SP202608140005', 'International Parcel', 12.0, 1800.0, 'HIGH', 0.88, 'POSSIBLE DELAY', '2026-08-15 11:00:00'),
            ('SP202608010001', 'Speed Post', 0.5, 350.0, 'LOW', 0.94, 'ON TIME', '2026-08-01 09:35:00'),
            ('SP202608050002', 'Express Parcel', 4.2, 950.0, 'MEDIUM', 0.76, 'POSSIBLE DELAY', '2026-08-05 11:20:00')
        ]
        cursor.executemany("INSERT INTO predictions (tracking_number, service_type, weight, distance, risk_level, confidence, prediction_result, created_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", preds_data)

    conn.commit()
    conn.close()

# Run DB initialization at application startup
init_db()

# Decorators for auth
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('login'))
        if session.get('role') != 'Admin':
            flash('Access Denied: Admin privileges required for this section.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Dynamic tracking number generator
def generate_tracking_number():
    date_str = datetime.now().strftime('%Y%m%d')
    rand_seq = random.randint(1000, 9999)
    return f"SP{date_str}{rand_seq}"

# Postage calculation helper
def calculate_postage_fees(service_type, weight, declared_value, is_international=False):
    service_rates = {
        'Ordinary Post': {'base': 15.00, 'per_kg': 10.00, 'service': 5.00},
        'Speed Post': {'base': 35.00, 'per_kg': 20.00, 'service': 10.00},
        'Registered Post': {'base': 25.00, 'per_kg': 15.00, 'service': 8.00},
        'Parcel': {'base': 30.00, 'per_kg': 18.00, 'service': 8.00},
        'Express Parcel': {'base': 50.00, 'per_kg': 25.00, 'service': 15.00},
        'International Parcel': {'base': 100.00, 'per_kg': 50.00, 'service': 30.00}
    }
    
    rate = service_rates.get(service_type, service_rates['Ordinary Post'])
    
    base_charge = rate['base']
    weight_charge = round(weight * rate['per_kg'], 2)
    service_charge = rate['service']
    
    additional_charge = 0.0
    if declared_value > 500:
        additional_charge += round(declared_value * 0.01, 2)
    if is_international or service_type == 'International Parcel':
        additional_charge += 25.00
        
    total_amount = round(base_charge + weight_charge + service_charge + additional_charge, 2)
    
    return {
        'base_charge': base_charge,
        'weight_charge': weight_charge,
        'service_charge': service_charge,
        'additional_charge': additional_charge,
        'total_amount': total_amount
    }

# ==================== ROUTES ====================

@app.route('/')
def landing():
    conn = get_db_connection()
    services = conn.execute("SELECT * FROM services LIMIT 6").fetchall()
    conn.close()
    return render_template('landing.html', services=services, current_theme='theme-landing')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        role = request.form.get('role', '').strip()
        
        if not username or not password or not role:
            flash('Please fill in all required login fields.', 'danger')
            return render_template('login.html', current_theme='theme-login')
            
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ? AND role = ?", (username, role)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['name'] = user['name']
            flash(f"Welcome back, {user['name']}!", 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username, password, or role selection.', 'danger')
            
    return render_template('login.html', current_theme='theme-login')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    
    total_customers = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    total_shipments = conn.execute("SELECT COUNT(*) FROM shipments").fetchone()[0]
    delivered_shipments = conn.execute("SELECT COUNT(*) FROM shipments WHERE status = 'DELIVERED'").fetchone()[0]
    pending_shipments = conn.execute("SELECT COUNT(*) FROM shipments WHERE status IN ('BOOKED', 'ACCEPTED', 'DISPATCHED', 'IN TRANSIT', 'ARRIVED', 'OUT FOR DELIVERY', 'POSSIBLE DELAY')").fetchone()[0]
    in_transit_shipments = conn.execute("SELECT COUNT(*) FROM shipments WHERE status = 'IN TRANSIT'").fetchone()[0]
    total_revenue = conn.execute("SELECT COALESCE(SUM(total_amount), 0) FROM shipments").fetchone()[0]
    open_complaints = conn.execute("SELECT COUNT(*) FROM complaints WHERE status IN ('OPEN', 'IN REVIEW')").fetchone()[0]
    
    today_date = datetime.now().strftime('%Y-%m-%d')
    today_bookings = conn.execute("SELECT COUNT(*) FROM shipments WHERE booking_date LIKE ?", (f"{today_date}%",)).fetchone()[0]
    
    recent_shipments = conn.execute("""
        SELECT tracking_number, sender_name, receiver_name, service_type, receiver_city, status, booking_date
        FROM shipments ORDER BY id DESC LIMIT 6
    """).fetchall()
    
    # Status distribution for charts
    status_counts = conn.execute("""
        SELECT status, COUNT(*) as count FROM shipments GROUP BY status
    """).fetchall()
    
    status_data = {row['status']: row['count'] for row in status_counts}
    
    conn.close()
    
    return render_template('dashboard.html',
                           current_theme='theme-dashboard',
                           total_customers=total_customers,
                           total_shipments=total_shipments,
                           delivered_shipments=delivered_shipments,
                           pending_shipments=pending_shipments,
                           in_transit_shipments=in_transit_shipments,
                           total_revenue=total_revenue,
                           open_complaints=open_complaints,
                           today_bookings=today_bookings,
                           recent_shipments=recent_shipments,
                           status_data=status_data)

@app.route('/customers')
@login_required
def customers():
    search = request.args.get('search', '').strip()
    conn = get_db_connection()
    if search:
        customers_list = conn.execute("""
            SELECT * FROM customers 
            WHERE full_name LIKE ? OR phone LIKE ? OR email LIKE ? OR city LIKE ?
            ORDER BY id DESC
        """, (f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%")).fetchall()
    else:
        customers_list = conn.execute("SELECT * FROM customers ORDER BY id DESC").fetchall()
    conn.close()
    return render_template('customers.html', customers=customers_list, search=search, current_theme='theme-customers')

@app.route('/customers/add', methods=['GET', 'POST'])
@login_required
def add_customer():
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        address = request.form.get('address', '').strip()
        city = request.form.get('city', '').strip()
        state = request.form.get('state', '').strip()
        postal_code = request.form.get('postal_code', '').strip()
        id_proof_type = request.form.get('id_proof_type', '').strip()
        id_proof_number = request.form.get('id_proof_number', '').strip()
        
        if not full_name or not phone or not email or not address or not city or not state or not postal_code:
            flash('Please fill in all mandatory customer fields.', 'danger')
            return render_template('customer_form.html', customer=None, action='Add', current_theme='theme-customers')
            
        reg_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn = get_db_connection()
        conn.execute("""
            INSERT INTO customers (full_name, phone, email, address, city, state, postal_code, id_proof_type, id_proof_number, registration_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (full_name, phone, email, address, city, state, postal_code, id_proof_type, id_proof_number, reg_date))
        conn.commit()
        conn.close()
        
        flash(f'Customer {full_name} registered successfully!', 'success')
        return redirect(url_for('customers'))
        
    return render_template('customer_form.html', customer=None, action='Add', current_theme='theme-customers')

@app.route('/customers/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_customer(id):
    conn = get_db_connection()
    customer = conn.execute("SELECT * FROM customers WHERE id = ?", (id,)).fetchone()
    
    if not customer:
        conn.close()
        flash('Customer record not found.', 'danger')
        return redirect(url_for('customers'))
        
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        address = request.form.get('address', '').strip()
        city = request.form.get('city', '').strip()
        state = request.form.get('state', '').strip()
        postal_code = request.form.get('postal_code', '').strip()
        id_proof_type = request.form.get('id_proof_type', '').strip()
        id_proof_number = request.form.get('id_proof_number', '').strip()
        
        conn.execute("""
            UPDATE customers SET full_name = ?, phone = ?, email = ?, address = ?, city = ?, state = ?, postal_code = ?, id_proof_type = ?, id_proof_number = ?
            WHERE id = ?
        """, (full_name, phone, email, address, city, state, postal_code, id_proof_type, id_proof_number, id))
        conn.commit()
        conn.close()
        
        flash(f'Customer {full_name} details updated.', 'success')
        return redirect(url_for('customers'))
        
    conn.close()
    return render_template('customer_form.html', customer=customer, action='Edit', current_theme='theme-customers')

@app.route('/customers/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_customer(id):
    conn = get_db_connection()
    conn.execute("DELETE FROM customers WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash('Customer removed from system database.', 'info')
    return redirect(url_for('customers'))

@app.route('/booking', methods=['GET', 'POST'])
@login_required
def booking():
    conn = get_db_connection()
    services_list = conn.execute("SELECT * FROM services").fetchall()
    customers_list = conn.execute("SELECT * FROM customers ORDER BY full_name").fetchall()
    
    if request.method == 'POST':
        # Sender info
        sender_name = request.form.get('sender_name', '').strip()
        sender_phone = request.form.get('sender_phone', '').strip()
        sender_address = request.form.get('sender_address', '').strip()
        sender_city = request.form.get('sender_city', '').strip()
        sender_state = request.form.get('sender_state', '').strip()
        sender_postal_code = request.form.get('sender_postal_code', '').strip()
        
        # Receiver info
        receiver_name = request.form.get('receiver_name', '').strip()
        receiver_phone = request.form.get('receiver_phone', '').strip()
        receiver_address = request.form.get('receiver_address', '').strip()
        receiver_city = request.form.get('receiver_city', '').strip()
        receiver_state = request.form.get('receiver_state', '').strip()
        receiver_postal_code = request.form.get('receiver_postal_code', '').strip()
        
        # Shipment info
        service_type = request.form.get('service_type', '').strip()
        item_type = request.form.get('item_type', '').strip()
        weight = float(request.form.get('weight', 0.5))
        quantity = int(request.form.get('quantity', 1))
        declared_value = float(request.form.get('declared_value', 0.0))
        payment_mode = request.form.get('payment_mode', 'Cash')
        
        if not sender_name or not receiver_name or not service_type or weight <= 0:
            flash('Validation error: Please complete all required sender, receiver, and shipment details.', 'danger')
            conn.close()
            return render_template('booking.html', services=services_list, customers=customers_list, current_theme='theme-booking')
            
        # Calculate postage
        is_intl = (service_type == 'International Parcel')
        fees = calculate_postage_fees(service_type, weight, declared_value, is_international=is_intl)
        
        tracking_num = generate_tracking_number()
        now_dt = datetime.now()
        booking_date = now_dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Estimate delivery date based on service type
        service_days = 4
        serv_row = conn.execute("SELECT estimated_days FROM services WHERE service_name = ?", (service_type,)).fetchone()
        if serv_row:
            service_days = serv_row['estimated_days']
        exp_delivery = (now_dt + timedelta(days=service_days)).strftime('%Y-%m-%d 17:00:00')
        
        # Insert Shipment
        conn.execute("""
            INSERT INTO shipments (
                tracking_number, sender_name, sender_phone, sender_address, sender_city, sender_state, sender_postal_code,
                receiver_name, receiver_phone, receiver_address, receiver_city, receiver_state, receiver_postal_code,
                service_type, item_type, weight, quantity, declared_value, base_charge, weight_charge, service_charge,
                additional_charge, total_amount, booking_date, expected_delivery_date, status, current_location
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            tracking_num, sender_name, sender_phone, sender_address, sender_city, sender_state, sender_postal_code,
            receiver_name, receiver_phone, receiver_address, receiver_city, receiver_state, receiver_postal_code,
            service_type, item_type, weight, quantity, declared_value, fees['base_charge'], fees['weight_charge'],
            fees['service_charge'], fees['additional_charge'], fees['total_amount'], booking_date, exp_delivery,
            'BOOKED', sender_city + ' Central Office'
        ))
        
        # Insert initial tracking event
        conn.execute("""
            INSERT INTO shipment_tracking (tracking_number, status, location, updated_at, remarks)
            VALUES (?, ?, ?, ?, ?)
        """, (tracking_num, 'BOOKED', sender_city + ' Central Office', booking_date, 'Shipment booked and postage fee received.'))
        
        # Insert payment record
        conn.execute("""
            INSERT INTO payments (tracking_number, amount, payment_mode, payment_status, payment_date)
            VALUES (?, ?, ?, ?, ?)
        """, (tracking_num, fees['total_amount'], payment_mode, 'COMPLETED', booking_date))
        
        # Add system notification
        conn.execute("""
            INSERT INTO notifications (title, message, status, created_date)
            VALUES (?, ?, ?, ?)
        """, ('New Postal Booking', f'Shipment {tracking_num} ({service_type}) booked by {sender_name}. Total: ${fees["total_amount"]}', 'UNREAD', booking_date))
        
        conn.commit()
        conn.close()
        
        flash(f'Postal booking successful! Tracking Number: {tracking_num}', 'success')
        return redirect(url_for('booking_success', tracking_number=tracking_num))
        
    conn.close()
    return render_template('booking.html', services=services_list, customers=customers_list, current_theme='theme-booking')

@app.route('/booking/success/<tracking_number>')
@login_required
def booking_success(tracking_number):
    conn = get_db_connection()
    shipment = conn.execute("SELECT * FROM shipments WHERE tracking_number = ?", (tracking_number,)).fetchone()
    payment = conn.execute("SELECT * FROM payments WHERE tracking_number = ?", (tracking_number,)).fetchone()
    conn.close()
    
    if not shipment:
        flash('Shipment record not found.', 'danger')
        return redirect(url_for('booking'))
        
    return render_template('booking_success.html', shipment=shipment, payment=payment, current_theme='theme-booking')

@app.route('/shipments')
@login_required
def shipments():
    status_filter = request.args.get('status', '').strip()
    search = request.args.get('search', '').strip()
    
    conn = get_db_connection()
    query = "SELECT * FROM shipments WHERE 1=1"
    params = []
    
    if status_filter:
        query += " AND status = ?"
        params.append(status_filter)
    if search:
        query += " AND (tracking_number LIKE ? OR sender_name LIKE ? OR receiver_name LIKE ? OR receiver_city LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%"])
        
    query += " ORDER BY id DESC"
    shipments_list = conn.execute(query, params).fetchall()
    conn.close()
    
    return render_template('shipments.html', shipments=shipments_list, status_filter=status_filter, search=search, current_theme='theme-dashboard')

@app.route('/shipments/<tracking_number>')
@login_required
def shipment_details(tracking_number):
    conn = get_db_connection()
    shipment = conn.execute("SELECT * FROM shipments WHERE tracking_number = ?", (tracking_number,)).fetchone()
    tracking_history = conn.execute("SELECT * FROM shipment_tracking WHERE tracking_number = ? ORDER BY id ASC", (tracking_number,)).fetchall()
    payment = conn.execute("SELECT * FROM payments WHERE tracking_number = ?", (tracking_number,)).fetchone()
    conn.close()
    
    if not shipment:
        flash('Shipment record not found.', 'danger')
        return redirect(url_for('shipments'))
        
    return render_template('shipment_details.html', shipment=shipment, tracking_history=tracking_history, payment=payment, current_theme='theme-dashboard')

@app.route('/shipments/<tracking_number>/status', methods=['POST'])
@login_required
def update_shipment_status(tracking_number):
    new_status = request.form.get('status', '').strip()
    location = request.form.get('location', '').strip()
    remarks = request.form.get('remarks', '').strip()
    
    if not new_status or not location:
        flash('Please select a valid status and enter current location.', 'danger')
        return redirect(url_for('shipment_details', tracking_number=tracking_number))
        
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = get_db_connection()
    
    # Update main shipment table
    conn.execute("UPDATE shipments SET status = ?, current_location = ? WHERE tracking_number = ?", (new_status, location, tracking_number))
    
    # Record tracking event
    conn.execute("""
        INSERT INTO shipment_tracking (tracking_number, status, location, updated_at, remarks)
        VALUES (?, ?, ?, ?, ?)
    """, (tracking_number, new_status, location, now_str, remarks))
    
    # Add notification
    conn.execute("""
        INSERT INTO notifications (title, message, status, created_date)
        VALUES (?, ?, ?, ?)
    """, (f'Shipment Status Updated ({new_status})', f'Shipment {tracking_number} updated to {new_status} at {location}.', 'UNREAD', now_str))
    
    conn.commit()
    conn.close()
    
    flash(f'Shipment status updated to {new_status}.', 'success')
    return redirect(url_for('shipment_details', tracking_number=tracking_number))

@app.route('/tracking', methods=['GET', 'POST'])
def tracking():
    tracking_number = request.args.get('tracking_number', '').strip()
    if request.method == 'POST':
        tracking_number = request.form.get('tracking_number', '').strip()
        
    shipment = None
    history = []
    searched = False
    
    if tracking_number:
        searched = True
        conn = get_db_connection()
        shipment = conn.execute("SELECT * FROM shipments WHERE tracking_number = ?", (tracking_number,)).fetchone()
        if shipment:
            history = conn.execute("SELECT * FROM shipment_tracking WHERE tracking_number = ? ORDER BY id ASC", (tracking_number,)).fetchall()
        conn.close()
        
    return render_template('tracking.html', shipment=shipment, history=history, tracking_number=tracking_number, searched=searched, current_theme='theme-tracking')

@app.route('/services')
def services():
    conn = get_db_connection()
    services_list = conn.execute("SELECT * FROM services").fetchall()
    conn.close()
    return render_template('services.html', services=services_list, current_theme='theme-services')

@app.route('/prediction', methods=['GET', 'POST'])
def prediction():
    prediction_result = None
    
    if request.method == 'POST':
        try:
            service_type_val = int(request.form.get('service_type', 1))
            weight = float(request.form.get('weight', 1.0))
            distance = float(request.form.get('distance', 100))
            processing_days = int(request.form.get('processing_days', 3))
            destination_type = int(request.form.get('destination_type', 0))
            previous_delay_rate = float(request.form.get('previous_delay_rate', 0.1))
            workload = int(request.form.get('workload', 5))
            weather_risk = int(request.form.get('weather_risk', 0))
            holiday_period = int(request.form.get('holiday_period', 0))
            tracking_num = request.form.get('tracking_number', '').strip()
            
            # Predict using model
            if os.path.exists(MODEL_PATH):
                import pandas as pd
                model = joblib.load(MODEL_PATH)
                feature_names = ['service_type', 'weight', 'distance', 'processing_days', 
                                 'destination_type', 'previous_delay_rate', 'workload', 
                                 'weather_risk', 'holiday_period']
                features = pd.DataFrame([[service_type_val, weight, distance, processing_days,
                                         destination_type, previous_delay_rate, workload,
                                         weather_risk, holiday_period]], columns=feature_names)
                
                pred_class = model.predict(features)[0]
                probabilities = model.predict_proba(features)[0]
                confidence = round(float(probabilities[pred_class]) * 100, 2)
                
                res_str = "POSSIBLE DELAY" if pred_class == 1 else "ON TIME"
                
                if pred_class == 1:
                    risk_level = "HIGH" if confidence > 80 else "MEDIUM"
                    recommendation = "Current shipment conditions indicate elevated delay risk. Consider prioritizing transit routing, expediting customs clearance, or selecting speed post dispatch."
                else:
                    risk_level = "LOW"
                    recommendation = "Current shipment conditions indicate a high likelihood of on-time delivery. Operational logistics are optimal."
                    
                prediction_result = {
                    'result': res_str,
                    'confidence': confidence,
                    'risk_level': risk_level,
                    'recommendation': recommendation
                }
                
                # Store prediction log in SQLite
                now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                serv_names = {1: 'Ordinary Post', 2: 'Speed Post', 3: 'Registered Post', 4: 'Parcel', 5: 'Express Parcel', 6: 'International Parcel'}
                serv_name = serv_names.get(service_type_val, 'Ordinary Post')
                
                conn = get_db_connection()
                conn.execute("""
                    INSERT INTO predictions (tracking_number, service_type, weight, distance, risk_level, confidence, prediction_result, created_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (tracking_num if tracking_num else 'N/A', serv_name, weight, distance, risk_level, confidence, res_str, now_str))
                conn.commit()
                conn.close()
            else:
                flash('AI Model file not found. Please run train_model.py first.', 'warning')
        except Exception as e:
            flash(f'Prediction calculation error: {str(e)}', 'danger')
            
    return render_template('prediction.html', prediction_result=prediction_result, current_theme='theme-ai')

@app.route('/employees')
@login_required
@admin_required
def employees():
    search = request.args.get('search', '').strip()
    conn = get_db_connection()
    if search:
        employees_list = conn.execute("""
            SELECT * FROM employees 
            WHERE name LIKE ? OR employee_code LIKE ? OR designation LIKE ? OR branch LIKE ?
            ORDER BY id DESC
        """, (f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%")).fetchall()
    else:
        employees_list = conn.execute("SELECT * FROM employees ORDER BY id DESC").fetchall()
    conn.close()
    return render_template('employees.html', employees=employees_list, search=search, current_theme='theme-employees')

@app.route('/employees/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_employee():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        designation = request.form.get('designation', '').strip()
        branch = request.form.get('branch', '').strip()
        
        if not name or not username or not password or not designation:
            flash('Please complete all required employee fields.', 'danger')
            return render_template('employee_form.html', current_theme='theme-employees')
            
        emp_code = f"EMP-{random.randint(1000, 9999)}"
        joining_date = datetime.now().strftime('%Y-%m-%d')
        
        conn = get_db_connection()
        try:
            # Create employee record
            conn.execute("""
                INSERT INTO employees (employee_code, name, username, phone, email, designation, branch, joining_date, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (emp_code, name, username, phone, email, designation, branch, joining_date, 'ACTIVE'))
            
            # Also create login user record
            pass_hash = generate_password_hash(password)
            conn.execute("""
                INSERT INTO users (username, password_hash, role, name, email, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (username, pass_hash, 'Employee', name, email, joining_date))
            
            conn.commit()
            flash(f'Employee {name} ({emp_code}) created successfully.', 'success')
            return redirect(url_for('employees'))
        except sqlite3.IntegrityError:
            flash('Username or Employee code already exists.', 'danger')
        finally:
            conn.close()
            
    return render_template('employee_form.html', current_theme='theme-employees')

@app.route('/employees/status/<int:id>', methods=['POST'])
@login_required
@admin_required
def toggle_employee_status(id):
    conn = get_db_connection()
    emp = conn.execute("SELECT status FROM employees WHERE id = ?", (id,)).fetchone()
    if emp:
        new_status = 'INACTIVE' if emp['status'] == 'ACTIVE' else 'ACTIVE'
        conn.execute("UPDATE employees SET status = ? WHERE id = ?", (new_status, id))
        conn.commit()
        flash(f'Employee status updated to {new_status}.', 'info')
    conn.close()
    return redirect(url_for('employees'))

@app.route('/complaints')
@login_required
def complaints():
    status_filter = request.args.get('status', '').strip()
    conn = get_db_connection()
    
    if status_filter:
        complaints_list = conn.execute("SELECT * FROM complaints WHERE status = ? ORDER BY id DESC", (status_filter,)).fetchall()
    else:
        complaints_list = conn.execute("SELECT * FROM complaints ORDER BY id DESC").fetchall()
        
    conn.close()
    return render_template('complaints.html', complaints=complaints_list, status_filter=status_filter, current_theme='theme-complaints')

@app.route('/complaints/add', methods=['GET', 'POST'])
@login_required
def add_complaint():
    if request.method == 'POST':
        customer_name = request.form.get('customer_name', '').strip()
        tracking_number = request.form.get('tracking_number', '').strip()
        complaint_type = request.form.get('complaint_type', '').strip()
        description = request.form.get('description', '').strip()
        priority = request.form.get('priority', 'MEDIUM').strip()
        
        if not customer_name or not complaint_type or not description:
            flash('Please fill in all required complaint fields.', 'danger')
            return render_template('complaint_form.html', current_theme='theme-complaints')
            
        created_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        conn = get_db_connection()
        conn.execute("""
            INSERT INTO complaints (customer_name, tracking_number, complaint_type, description, priority, status, created_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (customer_name, tracking_number if tracking_number else 'N/A', complaint_type, description, priority, 'OPEN', created_date))
        
        conn.execute("""
            INSERT INTO notifications (title, message, status, created_date)
            VALUES (?, ?, ?, ?)
        """, ('New Customer Complaint', f'Complaint logged by {customer_name} for tracking {tracking_number}. Priority: {priority}', 'UNREAD', created_date))
        
        conn.commit()
        conn.close()
        
        flash('Complaint registered successfully and assigned ticket number.', 'success')
        return redirect(url_for('complaints'))
        
    return render_template('complaint_form.html', current_theme='theme-complaints')

@app.route('/complaints/<int:id>/update', methods=['POST'])
@login_required
def update_complaint(id):
    status = request.form.get('status', '').strip()
    resolution = request.form.get('resolution', '').strip()
    
    conn = get_db_connection()
    conn.execute("UPDATE complaints SET status = ?, resolution = ? WHERE id = ?", (status, resolution, id))
    conn.commit()
    conn.close()
    
    flash('Complaint ticket updated successfully.', 'success')
    return redirect(url_for('complaints'))

@app.route('/notifications')
@login_required
def notifications():
    conn = get_db_connection()
    notifs = conn.execute("SELECT * FROM notifications ORDER BY id DESC").fetchall()
    # Mark unread as read when opening notification center
    conn.execute("UPDATE notifications SET status = 'READ' WHERE status = 'UNREAD'")
    conn.commit()
    conn.close()
    return render_template('notifications.html', notifications=notifs, current_theme='theme-notifications')

@app.route('/reports')
@login_required
def reports():
    conn = get_db_connection()
    
    total_customers = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    total_shipments = conn.execute("SELECT COUNT(*) FROM shipments").fetchone()[0]
    delivered_shipments = conn.execute("SELECT COUNT(*) FROM shipments WHERE status = 'DELIVERED'").fetchone()[0]
    pending_shipments = conn.execute("SELECT COUNT(*) FROM shipments WHERE status != 'DELIVERED'").fetchone()[0]
    total_revenue = conn.execute("SELECT COALESCE(SUM(total_amount), 0) FROM shipments").fetchone()[0]
    total_complaints = conn.execute("SELECT COUNT(*) FROM complaints").fetchone()[0]
    
    # Service breakdown
    service_stats = conn.execute("""
        SELECT service_type, COUNT(*) as count, SUM(total_amount) as revenue
        FROM shipments GROUP BY service_type
    """).fetchall()
    
    # Status breakdown
    status_stats = conn.execute("""
        SELECT status, COUNT(*) as count FROM shipments GROUP BY status
    """).fetchall()
    
    # AI Prediction breakdown
    prediction_stats = conn.execute("""
        SELECT prediction_result, COUNT(*) as count FROM predictions GROUP BY prediction_result
    """).fetchall()
    
    conn.close()
    
    return render_template('reports.html',
                           current_theme='theme-reports',
                           total_customers=total_customers,
                           total_shipments=total_shipments,
                           delivered_shipments=delivered_shipments,
                           pending_shipments=pending_shipments,
                           total_revenue=total_revenue,
                           total_complaints=total_complaints,
                           service_stats=service_stats,
                           status_stats=status_stats,
                           prediction_stats=prediction_stats)

@app.route('/about')
def about():
    return render_template('about.html', current_theme='theme-about')

@app.route('/contact', methods=['POST'])
def contact():
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    message = request.form.get('message', '').strip()
    
    if name and email and message:
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn = get_db_connection()
        conn.execute("INSERT INTO contact_messages (name, email, message, created_date) VALUES (?, ?, ?, ?)",
                     (name, email, message, now_str))
        conn.commit()
        conn.close()
        flash('Thank you for contacting SmartPost! Your message has been received.', 'success')
    else:
        flash('Please fill in all contact form fields.', 'danger')
        
    return redirect(url_for('landing'))

# ==================== REST API ENDPOINTS ====================

@app.route('/api/dashboard', methods=['GET'])
def api_dashboard():
    conn = get_db_connection()
    total_customers = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    total_shipments = conn.execute("SELECT COUNT(*) FROM shipments").fetchone()[0]
    total_revenue = conn.execute("SELECT COALESCE(SUM(total_amount), 0) FROM shipments").fetchone()[0]
    open_complaints = conn.execute("SELECT COUNT(*) FROM complaints WHERE status IN ('OPEN', 'IN REVIEW')").fetchone()[0]
    conn.close()
    return jsonify({
        'total_customers': total_customers,
        'total_shipments': total_shipments,
        'total_revenue': total_revenue,
        'open_complaints': open_complaints
    })

@app.route('/api/customers', methods=['GET'])
def api_customers():
    conn = get_db_connection()
    customers = [dict(row) for row in conn.execute("SELECT * FROM customers").fetchall()]
    conn.close()
    return jsonify({'status': 'success', 'data': customers})

@app.route('/api/shipments', methods=['GET'])
def api_shipments():
    conn = get_db_connection()
    shipments = [dict(row) for row in conn.execute("SELECT * FROM shipments").fetchall()]
    conn.close()
    return jsonify({'status': 'success', 'data': shipments})

@app.route('/api/shipments/<tracking_number>', methods=['GET'])
def api_shipment_detail(tracking_number):
    conn = get_db_connection()
    shipment = conn.execute("SELECT * FROM shipments WHERE tracking_number = ?", (tracking_number,)).fetchone()
    if not shipment:
        conn.close()
        return jsonify({'status': 'error', 'message': 'Tracking number not found'}), 404
        
    history = [dict(row) for row in conn.execute("SELECT * FROM shipment_tracking WHERE tracking_number = ?", (tracking_number,)).fetchall()]
    conn.close()
    return jsonify({'status': 'success', 'shipment': dict(shipment), 'history': history})

@app.route('/api/services', methods=['GET'])
def api_services():
    conn = get_db_connection()
    services = [dict(row) for row in conn.execute("SELECT * FROM services").fetchall()]
    conn.close()
    return jsonify({'status': 'success', 'data': services})

@app.route('/api/complaints', methods=['GET'])
def api_complaints():
    conn = get_db_connection()
    complaints = [dict(row) for row in conn.execute("SELECT * FROM complaints").fetchall()]
    conn.close()
    return jsonify({'status': 'success', 'data': complaints})

@app.route('/api/notifications', methods=['GET'])
def api_notifications():
    conn = get_db_connection()
    notifications = [dict(row) for row in conn.execute("SELECT * FROM notifications ORDER BY id DESC LIMIT 10").fetchall()]
    conn.close()
    return jsonify({'status': 'success', 'data': notifications})

@app.route('/api/predictions', methods=['GET'])
def api_predictions():
    conn = get_db_connection()
    predictions = [dict(row) for row in conn.execute("SELECT * FROM predictions ORDER BY id DESC").fetchall()]
    conn.close()
    return jsonify({'status': 'success', 'data': predictions})

@app.route('/api/predict-delay', methods=['POST'])
def api_predict_delay():
    data = request.get_json(silent=True) or {}
    
    required_keys = ['service_type', 'weight', 'distance', 'processing_days', 'destination_type', 'previous_delay_rate', 'workload', 'weather_risk', 'holiday_period']
    for key in required_keys:
        if key not in data:
            return jsonify({'status': 'error', 'message': f'Missing required feature parameter: {key}'}), 400
            
    try:
        service_type = int(data['service_type'])
        weight = float(data['weight'])
        distance = float(data['distance'])
        processing_days = int(data['processing_days'])
        destination_type = int(data['destination_type'])
        previous_delay_rate = float(data['previous_delay_rate'])
        workload = int(data['workload'])
        weather_risk = int(data['weather_risk'])
        holiday_period = int(data['holiday_period'])
        
        if not os.path.exists(MODEL_PATH):
            return jsonify({'status': 'error', 'message': 'AI Model file not trained or missing'}), 500
            
        import pandas as pd
        model = joblib.load(MODEL_PATH)
        feature_names = ['service_type', 'weight', 'distance', 'processing_days', 
                         'destination_type', 'previous_delay_rate', 'workload', 
                         'weather_risk', 'holiday_period']
        features = pd.DataFrame([[service_type, weight, distance, processing_days, 
                                 destination_type, previous_delay_rate, workload, 
                                 weather_risk, holiday_period]], columns=feature_names)
        
        pred_class = model.predict(features)[0]
        probabilities = model.predict_proba(features)[0]
        confidence = round(float(probabilities[pred_class]) * 100, 2)
        
        prediction = "POSSIBLE DELAY" if pred_class == 1 else "ON TIME"
        risk_level = "HIGH" if (pred_class == 1 and confidence > 80) else ("MEDIUM" if pred_class == 1 else "LOW")
        
        if pred_class == 1:
            recommendation = "Current shipment conditions indicate elevated delay risk. Consider prioritizing processing."
        else:
            recommendation = "Current shipment conditions indicate a lower likelihood of delay."
            
        return jsonify({
            'status': 'success',
            'prediction': prediction,
            'confidence': confidence,
            'risk_level': risk_level,
            'recommendation': recommendation
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

# Error Handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', current_theme='theme-landing'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html', current_theme='theme-landing'), 500

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
