# SmartPost – AI-Powered Post Office Management and Smart Delivery System

**SmartPost** is a complete, production-ready, web-based Post Office Management Application designed to digitize postal operations, automate postage calculations, issue dynamic shipment tracking numbers, and utilize Artificial Intelligence to forecast delivery delay risks in real time.

## LIVE DEMO : https://smartpost-1d44.onrender.com

## PROTOTYPE : https://drive.google.com/file/d/1WMJqDU2JESB-EQt4bqNn1YHXWO_O6slf/view?usp=drive_link

---

## 🚀 Key Features

1. **Landing Page**: Public portal featuring modern post office visuals, service cards, system overview, and working navigation to login.
2. **Role-Based Authentication**: Secure session-based login system for **Admin** and **Employee** roles with hashed passwords (`werkzeug.security`).
3. **Dashboard & Analytics**: Real-time statistics cards (Total Customers, Total Shipments, Delivered, Pending, In Transit, Total Revenue, Complaints, Today's Bookings) powered by Chart.js.
4. **Customer Management**: Full CRUD operations to register, edit, search, and manage postal senders/receivers with ID proof verification.
5. **Postal Booking System**: Seamless parcel booking with dynamic tracking number generation (`SP` + YYYYMMDD + sequence).
6. **Automated Postage Calculator**: Real-time fee computation based on service tier, package weight, international status, and declared item value.
7. **Official Receipt & Printing**: Formatted printable receipt module with `window.print()` functionality.
8. **Shipment Management**: Complete dispatch log allowing staff to update shipment statuses (`BOOKED`, `DISPATCHED`, `IN TRANSIT`, `DELIVERED`, `POSSIBLE DELAY`).
9. **Dynamic Tracking & Timeline**: Public and internal parcel tracker with vertical progress journey built from database audit logs.
10. **AI Delivery Delay Prediction**: Machine Learning inference engine (`RandomForestClassifier`) estimating delay probability, model confidence score, risk rating, and operational recommendations.
11. **Employee Management**: Admin-only staff directory supporting designation assignments and account activation/deactivation.
12. **Complaint Management**: Customer grievance ticketing system with priority escalation and resolution logs.
13. **Notification Feed**: Automated real-time logs for bookings, status updates, AI delay flags, and complaint tickets.
14. **Operational Reports**: Analytical operation summaries with exportable metrics and status distribution charts.
15. **Bespoke Page Color Themes**: 13 distinct visual color palettes tailored specifically for each major module.

---

## 🎨 Page Color Themes Specification

Each module features a unique CSS color theme:
- **Landing Page**: Deep Postal Red (`#7f1d1d`), Burgundy, Warm Cream, Gold (`.theme-landing`)
- **Login Page**: Dark Teal (`#042f2e`), Deep Green, Soft Mint (`.theme-login`)
- **Dashboard**: Dark Lavender (`#1e1b4b`), Deep Purple, Soft Violet (`.theme-dashboard`)
- **Customer Management**: Dark Pink (`#4c0519`), Burgundy Pink, Rose (`.theme-customers`)
- **Postal Booking**: Dark Violet (`#2e1065`), Purple, Magenta (`.theme-booking`)
- **Shipment Tracking**: Rich Brown (`#291e12`), Coffee, Copper/Gold (`.theme-tracking`)
- **Postal Services**: Dark Emerald Green (`#022c22`), Forest Green, Mint (`.theme-services`)
- **AI Delivery Prediction**: Dark Indigo (`#0f172a`), Navy-Purple, Electric Cyan (`.theme-ai`)
- **Employee Management**: Dark Charcoal (`#18181b`), Slate, Muted Orange (`.theme-employees`)
- **Complaints**: Dark Maroon (`#450a0a`), Wine, Crimson (`.theme-complaints`)
- **Notifications**: Dark Olive (`#1a2e05`), Moss Green, Warm Yellow (`.theme-notifications`)
- **Reports**: Dark Copper (`#451a03`), Terracotta, Bronze (`.theme-reports`)
- **About Page**: Dark Cyan/Teal (`#083344`), Deep Turquoise, Soft Aqua (`.theme-about`)

---

## 🛠️ Technology Stack

- **Frontend**: HTML5, Vanilla CSS3 (Custom CSS Grid/Flexbox design system with 13 page themes), Vanilla JavaScript (DOM manipulation, auto postage calculations, Chart.js wrappers).
- **Backend**: Python Flask (WSGI web framework, session management, route protection decorators).
- **AI/ML Core**: Python `scikit-learn` (`RandomForestClassifier`), `pandas`, `numpy`, `joblib`.
- **Database**: SQLite3 (`database/smartpost.db`) initialized automatically with parameterized SQL queries.
- **Charts**: Chart.js via CDN.

---

## ⚙️ Installation & Running

Follow these step-by-step terminal commands to set up and start the application:

### Step 1: Install Dependencies
```bash
python -m pip install -r requirements.txt
```

### Step 2: Train the AI Delivery Delay Model
```bash
python train_model.py
```
*Expected Output:*
```
Generating synthetic shipment dataset...
Training dataset size: 2000
Testing dataset size: 500
Model accuracy: 89.20%
Model saved successfully to model/delivery_delay_model.pkl
```

### Step 3: Run the Flask Web Application
```bash
python app.py
```

Open your browser and navigate to:
[http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 🔑 Default Credentials

The database initializes automatically with default user credentials on first run:

- **Admin Account**:
  - **Username**: `admin`
  - **Password**: `admin123`
  - **Role**: `Admin`

- **Employee Account**:
  - **Username**: `employee`
  - **Password**: `employee123`
  - **Role**: `Employee`

---

## 🤖 AI Methodology & Postage Calculation

### AI Delivery Delay Model
The ML model evaluates 9 key shipment attributes:
- `service_type` (1 to 6)
- `weight` (kg)
- `distance` (km)
- `processing_days`
- `destination_type` (Urban, Semi-Urban, Rural, Remote)
- `previous_delay_rate`
- `workload` (1-10 index)
- `weather_risk` (Low, Medium, High)
- `holiday_period` (0 or 1)

Output returns:
- **Classification**: `ON TIME` or `POSSIBLE DELAY`
- **Confidence**: Model probability percentage (e.g. `88.5%`)
- **Risk Level**: `LOW`, `MEDIUM`, or `HIGH`
- **Recommendation**: Actionable operational guidance.

### Postage Calculation Rules
Total Postage Fee = Base Charge + Weight Charge + Service Charge + Additional Surcharge
- **Ordinary Post**: Base $15.00 + $10.00/kg
- **Speed Post**: Base $35.00 + $20.00/kg
- **Registered Post**: Base $25.00 + $15.00/kg
- **Parcel**: Base $30.00 + $18.00/kg
- **Express Parcel**: Base $50.00 + $25.00/kg
- **International Parcel**: Base $100.00 + $50.00/kg + $25.00 Surcharge
- **Value Surcharge**: +1% of declared item value if declared value exceeds $500.

---

## 📡 REST API Endpoints

- `GET /api/dashboard` - Dashboard stats overview
- `GET /api/customers` - List all registered customers
- `GET /api/shipments` - List all shipments
- `GET /api/shipments/<tracking_number>` - Retrieve shipment details & tracking timeline
- `GET /api/services` - Service rates catalog
- `GET /api/complaints` - List customer complaints
- `GET /api/notifications` - System notification logs
- `GET /api/predictions` - AI prediction history
- `POST /api/predict-delay` - API endpoint for ML delay inference

### Sample API Request (`POST /api/predict-delay`):
```json
{
  "service_type": 2,
  "weight": 4.5,
  "distance": 850,
  "processing_days": 2,
  "destination_type": 1,
  "previous_delay_rate": 0.15,
  "workload": 8,
  "weather_risk": 1,
  "holiday_period": 0
}
```

### Sample API Response:
```json
{
  "status": "success",
  "prediction": "POSSIBLE DELAY",
  "confidence": 84.5,
  "risk_level": "HIGH",
  "recommendation": "Current shipment conditions indicate elevated delay risk. Consider prioritizing processing."
}
```

---

## 📋 Project Demonstration Flow

1. Open `http://127.0.0.1:5000` to view the Landing Page.
2. Click **GET STARTED** to navigate to the Login Page (`/login`).
3. Login using `admin` / `admin123`.
4. Review the **Dashboard** analytics cards, status chart, and quick action bar.
5. Navigate to **Customers** (`/customers`) and register a new sender.
6. Open **Postal Booking** (`/booking`), select sender, fill receiver & parcel specs, and click **Confirm & Issue Booking**.
7. Review the generated receipt page with unique tracking number (e.g. `SP202608160001`).
8. Click **Track Shipment** or visit `/tracking`, enter the tracking number, and observe the live vertical timeline.
9. Navigate to **Shipments** (`/shipments`), open shipment details, and record a status update.
10. Open **AI Prediction** (`/prediction`), input shipment features, and click **Predict Delivery Risk**.
11. Navigate to **Reports** (`/reports`) and test the **Print Report** button (`window.print()`).
12. Click **Logout** to end the session.
