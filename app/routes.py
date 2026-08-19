import calendar
from datetime import datetime, date
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, User, RosterEntry, LeaveRequest, ExternalOnCall, Role

# Initialize Blueprint
main = Blueprint('main', __name__)

# Role-Based Access Control (RBAC) Decorator
def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role.name not in roles:
                flash('Unauthorized access privileges.', 'danger')
                return redirect(url_for('main.dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# --------------------------------------------------------------------------
# AUTHENTICATION ROUTES
# --------------------------------------------------------------------------

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash(f'Welcome back, {user.name}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.dashboard'))
        
        flash('Invalid email address or password.', 'danger')
    return render_template('login.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main.login'))

# --------------------------------------------------------------------------
# DASHBOARD
# --------------------------------------------------------------------------

@main.route('/')
@main.route('/dashboard')
@login_required
def dashboard():
    today = date.today()
    
    # Active shifts for today grouped by shift type
    today_entries = RosterEntry.query.filter_by(roster_date=today).all()
    active_shifts = {
        'Morning': [], 'Evening': [], 'Night': [], 
        'General': [], 'OFF': [], 'Leave': []
    }
    for entry in today_entries:
        if entry.shift_type in active_shifts:
            active_shifts[entry.shift_type].append(entry.user)

    # Active External On-Call resources
    oncall_contacts = ExternalOnCall.query.filter(
        ExternalOnCall.start_date <= today,
        ExternalOnCall.end_date >= today
    ).all()

    # Manager Escalation Contact
    manager_role = Role.query.filter_by(name='SOC_Manager').first()
    soc_manager = User.query.filter_by(role_id=manager_role.id).first() if manager_role else None

    return render_template(
        'dashboard.html',
        today=today,
        active_shifts=active_shifts,
        oncall_contacts=oncall_contacts,
        soc_manager=soc_manager
    )

# --------------------------------------------------------------------------
# ROSTER MANAGEMENT & SHIFT TRACKER
# --------------------------------------------------------------------------

@main.route('/roster')
@login_required
def view_roster():
    from app.scheduler import generate_monthly_roster  # Lazy import
    
    now = datetime.now()
    year = int(request.args.get('year', now.year))
    month = int(request.args.get('month', now.month))

    # Calculate full date list for the selected month
    _, num_days = calendar.monthrange(year, month)
    days_in_month = [date(year, month, d) for d in range(1, num_days + 1)]

    # Fetch users ordered by Tier and Name
    users = User.query.filter_by(is_active=True).order_by(User.tier, User.name).all()
    
    roster_data = RosterEntry.query.filter(
        db.extract('year', RosterEntry.roster_date) == year,
        db.extract('month', RosterEntry.roster_date) == month
    ).all()

    # Auto-generate if matrix for requested month is unpopulated
    if not roster_data:
        generate_monthly_roster(year, month)
        roster_data = RosterEntry.query.filter(
            db.extract('year', RosterEntry.roster_date) == year,
            db.extract('month', RosterEntry.roster_date) == month
        ).all()

    # Build dictionary lookup: (user_id, 'YYYY-MM-DD') -> RosterEntry
    roster_dict = {
        (r.user_id, r.roster_date.strftime('%Y-%m-%d')): r 
        for r in roster_data
    }

    return render_template(
        'roster.html',
        roster_dict=roster_dict,
        users=users,
        days_in_month=days_in_month,
        selected_year=year,
        selected_month=month,
        month_name=calendar.month_name[month]
    )

@main.route('/roster/generate', methods=['POST'])
@login_required
@role_required('Admin', 'SOC_Manager')
def generate_roster():
    from app.scheduler import generate_monthly_roster  # Lazy import
    
    year = int(request.form.get('year'))
    month = int(request.form.get('month'))
    generate_monthly_roster(year, month)
    flash(f'Roster generated successfully for {calendar.month_name[month]} {year}.', 'success')
    return redirect(url_for('main.view_roster', year=year, month=month))

@main.route('/shift-tracker')
@login_required
def shift_tracker():
    """Multi-month Shift Tracker overview across all 12 months."""
    year = int(request.args.get('year', datetime.now().year))
    
    months_summary = []
    for m in range(1, 13):
        _, num_days = calendar.monthrange(year, m)
        count = RosterEntry.query.filter(
            db.extract('year', RosterEntry.roster_date) == year,
            db.extract('month', RosterEntry.roster_date) == m
        ).count()
        
        months_summary.append({
            'month_num': m,
            'month_name': calendar.month_name[m],
            'total_entries': count,
            'is_generated': count > 0
        })

    return render_template('shift_tracker.html', months_summary=months_summary, year=year)

@main.route('/roster/override', methods=['POST'])
@login_required
@role_required('Admin', 'SOC_Manager')
def override_shift():
    user_id = int(request.form.get('user_id'))
    shift_date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
    new_shift = request.form.get('shift_type')

    entry = RosterEntry.query.filter_by(user_id=user_id, roster_date=shift_date).first()
    if entry:
        entry.shift_type = new_shift
        entry.is_override = True
    else:
        entry = RosterEntry(user_id=user_id, roster_date=shift_date, shift_type=new_shift, is_override=True)
        db.session.add(entry)

    db.session.commit()
    flash('Shift overridden successfully.', 'info')
    return redirect(url_for('main.view_roster', year=shift_date.year, month=shift_date.month))

@main.route('/roster/export')
@login_required
def export_excel():
    from app.utils import export_roster_to_excel  # Lazy import
    
    now = datetime.now()
    year = int(request.args.get('year', now.year))
    month = int(request.args.get('month', now.month))

    roster_entries = RosterEntry.query.filter(
        db.extract('year', RosterEntry.roster_date) == year,
        db.extract('month', RosterEntry.roster_date) == month
    ).all()

    data = [{
        'Date': e.roster_date.strftime('%Y-%m-%d'),
        'Analyst': e.user.name,
        'Role': e.user.tier,
        'Shift': e.shift_type
    } for e in roster_entries]

    excel_file = export_roster_to_excel(data, year, month)
    return send_file(
        excel_file,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'SOC_Roster_{year}_{month:02d}.xlsx'
    )

# --------------------------------------------------------------------------
# LEAVE MANAGEMENT
# --------------------------------------------------------------------------

@main.route('/leaves')
@login_required
def view_leaves():
    users = User.query.filter_by(is_active=True).order_by(User.name).all()
    leave_requests = LeaveRequest.query.order_by(LeaveRequest.created_at.desc()).all()
    return render_template('leave.html', users=users, requests=leave_requests)

@main.route('/leaves/submit', methods=['POST'])
@login_required
def submit_leave():
    from app.scheduler import generate_monthly_roster  # Lazy import
    
    user_id = int(request.form.get('user_id'))
    leave_type = request.form.get('leave_type')
    start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
    end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()

    if start_date > end_date:
        flash('Start date must be before or equal to end date.', 'danger')
        return redirect(url_for('main.view_leaves'))

    leave = LeaveRequest(
        user_id=user_id,
        leave_type=leave_type,
        start_date=start_date,
        end_date=end_date,
        status='Approved'
    )
    db.session.add(leave)

    num_days = (end_date - start_date).days + 1
    user = User.query.get_or_404(user_id)
    if leave_type == 'Annual':
        user.annual_leave_used += num_days
    elif leave_type == 'Sick':
        user.sick_leave_monthly_used += num_days
        user.sick_leave_total_used += num_days

    db.session.commit()

    # Re-trigger roster engine to reflect approved leave across months
    curr = start_date
    while curr <= end_date:
        generate_monthly_roster(curr.year, curr.month)
        if curr.month == 12:
            curr = date(curr.year + 1, 1, 1)
        else:
            curr = date(curr.year, curr.month + 1, 1)

    flash('Leave request submitted and roster recalculated.', 'success')
    return redirect(url_for('main.view_leaves'))

# --------------------------------------------------------------------------
# EXTERNAL ON-CALL CONTACTS
# --------------------------------------------------------------------------

@main.route('/oncall', methods=['GET', 'POST'])
@login_required
def view_oncall():
    if request.method == 'POST':
        if current_user.role.name not in ['Admin', 'SOC_Manager']:
            flash('Unauthorized to add on-call contacts.', 'danger')
            return redirect(url_for('main.view_oncall'))

        new_oncall = ExternalOnCall(
            team_name=request.form.get('team_name'),
            name=request.form.get('name'),
            title=request.form.get('title'),
            email=request.form.get('email'),
            phone=request.form.get('phone'),
            start_date=datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date(),
            end_date=datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
        )
        db.session.add(new_oncall)
        db.session.commit()
        flash('External contact added successfully.', 'success')
        return redirect(url_for('main.view_oncall'))

    oncall_list = ExternalOnCall.query.order_by(ExternalOnCall.start_date.desc()).all()
    return render_template('oncall.html', oncall_list=oncall_list)

@main.route('/oncall/update/<int:contact_id>', methods=['POST'])
@login_required
@role_required('Admin', 'SOC_Manager')
def update_oncall(contact_id):
    contact = ExternalOnCall.query.get_or_404(contact_id)
    
    contact.team_name = request.form.get('team_name', contact.team_name)
    contact.name = request.form.get('name', contact.name)
    contact.title = request.form.get('title', contact.title)
    contact.email = request.form.get('email', contact.email)
    contact.phone = request.form.get('phone', contact.phone)
    
    if request.form.get('start_date'):
        contact.start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
    if request.form.get('end_date'):
        contact.end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()

    db.session.commit()
    flash('External contact updated successfully.', 'success')
    return redirect(url_for('main.view_oncall'))

@main.route('/oncall/delete/<int:contact_id>', methods=['POST'])
@login_required
@role_required('Admin', 'SOC_Manager')
def delete_oncall(contact_id):
    contact = ExternalOnCall.query.get_or_404(contact_id)
    db.session.delete(contact)
    db.session.commit()
    flash('External contact removed successfully.', 'info')
    return redirect(url_for('main.view_oncall'))