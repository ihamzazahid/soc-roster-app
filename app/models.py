from datetime import datetime, date
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class Role(db.Model):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    
    users = db.relationship('User', backref='role', lazy=True)


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    tier = db.Column(db.String(20), nullable=False, default='L1')  # L1, L2, L3, Manager
    joining_date = db.Column(db.Date, nullable=False, default=date.today)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)

    annual_leave_allocated = db.Column(db.Integer, default=20, nullable=False)
    annual_leave_used = db.Column(db.Integer, default=0, nullable=False)
    sick_leave_monthly_used = db.Column(db.Integer, default=0, nullable=False)
    sick_leave_total_used = db.Column(db.Integer, default=0, nullable=False)

    roster_entries = db.relationship('RosterEntry', backref='user', lazy=True, cascade="all, delete-orphan")
    leave_requests = db.relationship('LeaveRequest', backref='user', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)


class RosterEntry(db.Model):
    __tablename__ = 'roster_entries'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    roster_date = db.Column(db.Date, nullable=False)
    shift_type = db.Column(db.String(20), nullable=False)  # Morning, Evening, Night, General, OFF, Leave
    is_on_call = db.Column(db.Boolean, default=False, nullable=False)
    is_override = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'roster_date', name='_user_date_uc'),)


class LeaveRequest(db.Model):
    __tablename__ = 'leave_requests'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    leave_type = db.Column(db.String(20), nullable=False)  # Annual, Sick
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='Approved', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ExternalOnCall(db.Model):
    __tablename__ = 'external_oncall'

    id = db.Column(db.Integer, primary_key=True)
    team_name = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)