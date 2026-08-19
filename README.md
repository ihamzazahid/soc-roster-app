# 🛡️ SOC 24/7 Shift Roster & Operations Platform (`soc-roster-app`)

An enterprise-grade, containerized Flask application designed for Security Operations Centers (SOCs) to automate **24/7 shift scheduling**, manage analyst hierarchies, track leave requests, maintain external on-call directories, and provide real-time operational visibility through an interactive dashboard.

---

## 🚀 Features

### 🔄 Intelligent 24/7 Shift Scheduling

* Automated generation of continuous SOC coverage
* Three 8-hour shift rotations:

  * **Morning:** 07:00 – 15:00
  * **Evening:** 15:00 – 23:00
  * **Night:** 23:00 – 07:00
* Ensures zero coverage gaps across all days of the year

### 🛡️ Analyst Tier Enforcement

* Supports analyst hierarchy:

  * L1 Analyst
  * L2 Analyst
  * L3 Analyst
  * SOC Lead
* Enforces mandatory senior analyst oversight during operational shifts

### 😴 Fatigue & Compliance Controls

* Prevents invalid back-to-back assignments
* Avoids Morning shifts immediately following Night shifts
* Promotes fair workload distribution

### 🏖️ Leave Management

* Submit, approve, and track leave requests
* Automatically excludes unavailable analysts from schedules
* Dynamically recalculates rosters after leave approval

### 📞 External On-Call Directory

* Manage third-party escalation contacts
* Define active duty windows and escalation paths
* Quick access during incidents

### 📊 Real-Time SOC Dashboard

* View currently active analysts by shift
* Track roster metrics and staffing coverage
* Monitor escalation contacts and operational readiness

---

## 📂 Project Structure

```text
soc-roster-app/
├── app/
│   ├── services/
│   │   └── roster_generator.py
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css
│   │   └── js/
│   │       └── roster.js
│   ├── templates/
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── leave.html
│   │   ├── login.html
│   │   ├── oncall.html
│   │   ├── roster.html
│   │   ├── shift_tracker.html
│   │   └── users.html
│   ├── models.py
│   ├── routes.py
│   ├── scheduler.py
│   ├── utils.py
│   └── __init__.py
├── config.py
├── docker-compose.yml
├── Dockerfile
├── README.md
├── requirements.txt
├── run.py
└── seed.py
```

---

## 🏗️ Technology Stack

* **Backend:** Flask
* **Database:** PostgreSQL
* **ORM:** SQLAlchemy
* **Frontend:** HTML, CSS, JavaScript, Jinja2
* **Authentication:** Flask Login
* **Containerization:** Docker & Docker Compose

---

## ⚙️ Environment Configuration

Create a `.env` file in the project root:

```env
# Flask Configuration
FLASK_APP=run.py
FLASK_ENV=production
SECRET_KEY=your_super_secret_key_here

# PostgreSQL Configuration
POSTGRES_USER=soc_user
POSTGRES_PASSWORD=soc_pass
POSTGRES_DB=soc_roster_db

DATABASE_URL=postgresql://soc_user:soc_pass@db:5432/soc_roster_db
```

---

## 🐳 Docker Deployment

### Prerequisites

* Docker Desktop
* Git

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_GITHUB_USERNAME/soc-roster-app.git
cd soc-roster-app
```

### 2. Build & Start Services

```bash
docker-compose up --build -d
```

### 3. Seed Initial Data

```bash
docker-compose exec web python seed.py
```

### 4. Access the Application

Open your browser:

```text
http://localhost:5000
```

---

## 💻 Local Development Setup

### Create Virtual Environment

```bash
python -m venv venv
```

### Activate Environment

**Windows**

```bash
venv\Scripts\activate
```

**Linux/macOS**

```bash
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Initialize Database

```bash
python seed.py
```

### Start Application

```bash
python run.py
```

---

## 📖 User Guide

### 🔐 Authentication

Access the platform through the login page using seeded credentials.

### 👥 User Management

Navigate to `/users` to:

* Create analysts
* Assign roles and tiers
* Manage SOC personnel

### 🏖️ Leave Management

Navigate to `/leave` to:

* Submit leave requests
* Approve or reject requests
* Automatically update roster availability

### 📅 Roster Generation

Navigate to `/roster` to:

* Select a target month
* Generate schedules automatically
* Enforce staffing and fatigue rules

### 📞 On-Call Management

Navigate to `/oncall` to:

* Maintain external escalation contacts
* Configure support windows
* Define incident response contacts

### 📊 Dashboard Monitoring

Navigate to `/dashboard` to:

* View active personnel
* Monitor current shift coverage
* Track operational metrics

---

## 🔒 Scheduling Rules

The roster engine enforces the following operational constraints:

* Continuous 24/7 coverage
* No duplicate analyst assignments
* Leave-aware scheduling
* Senior analyst supervision requirements
* Night-to-morning fatigue protection
* Fair analyst workload distribution
* Shift coverage validation

---

## 🎯 Use Cases

* Security Operations Centers (SOC)
* Managed Security Service Providers (MSSP)
* Network Operations Centers (NOC)
* Incident Response Teams
* Cybersecurity Monitoring Teams
* Enterprise Security Departments

---

## 📸 Application Modules

| Module            | Purpose                         |
| ----------------- | ------------------------------- |
| Dashboard         | Real-time SOC visibility        |
| Roster Management | Shift generation and scheduling |
| User Management   | Analyst administration          |
| Leave Management  | Leave request processing        |
| Shift Tracker     | Active shift monitoring         |
| On-Call Directory | Escalation contact management   |

---

## 🤝 Contributing

Contributions are welcome.

1. Fork the repository
2. Create a feature branch

```bash
git checkout -b feature/new-feature
```

3. Commit your changes

```bash
git commit -m "Add new feature"
```

4. Push your branch

```bash
git push origin feature/new-feature
```

5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License.

---

## 👨‍💻 Author

Built for modern Security Operations Centers requiring reliable, automated, and compliant 24/7 workforce scheduling.
