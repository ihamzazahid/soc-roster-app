import calendar
from datetime import date
from app import db
from app.models import User, RosterEntry, LeaveRequest, Shift

def generate_monthly_roster(year: int, month: int):
    # Get total days in target month
    _, num_days = calendar.monthrange(year, month)
    start_date = date(year, month, 1)
    end_date = date(year, month, num_days)

    # 1. Clear existing roster for this specific month
    RosterEntry.query.filter(
        RosterEntry.roster_date >= start_date,
        RosterEntry.roster_date <= end_date
    ).delete(synchronize_session='fetch')
    db.session.flush()

    # 2. Fetch active staff and available shifts
    active_users = User.query.filter_by(is_active=True).all()
    shifts = Shift.query.all() if hasattr(Shift, 'query') else []
    
    if not active_users:
        return False, "No active analysts configured."

    # Map shifts by name and ID
    shift_map = {s.name.strip().title(): s.id for s in shifts} if shifts else {}
    shift_id_to_name = {s.id: s.name for s in shifts} if shifts else {}
    
    general_shift_id = (
        shift_map.get('General') or 
        shift_map.get('Day') or 
        shift_map.get('Morning') or 
        (shifts[0].id if shifts else None)
    )

    op_shifts = [s for s in shifts if s.id != shift_map.get('General')] if shifts else []
    if not op_shifts and shifts:
        op_shifts = shifts

    op_shift_ids = [s.id for s in op_shifts]

    # Separate Fixed Management (L3 / Manager) from 24/7 Operational Staff (L1 / L2)
    fixed_staff = [u for u in active_users if getattr(u, 'tier', '') in ['L3', 'Manager', 'SOC Manager', 'SOC Lead']]
    op_staff = [u for u in active_users if getattr(u, 'tier', '') not in ['L3', 'Manager', 'SOC Manager', 'SOC Lead']]

    if not fixed_staff and not op_staff:
        op_staff = active_users

    # Initialize tracker for 24/7 operational staff
    tracker = {
        u.id: {
            'consecutive_work': 0,
            'consecutive_off': 0,
            'shift_idx': idx % (len(op_shift_ids) if op_shift_ids else 1)
        }
        for idx, u in enumerate(op_staff)
    }

    approved_leaves = LeaveRequest.query.filter(
        LeaveRequest.status == 'Approved',
        LeaveRequest.start_date <= end_date,
        LeaveRequest.end_date >= start_date
    ).all()

    def get_leave_status(user_id, current_day):
        for leave in approved_leaves:
            if leave.user_id == user_id and leave.start_date <= current_day <= leave.end_date:
                return leave
        return None

    new_entries = []

    # 3. Generate schedule day-by-day
    for day in range(1, num_days + 1):
        current_day = date(year, month, day)
        is_weekend = current_day.weekday() >= 5  # Sat/Sun

        # A. FIXED SCHEDULE STAFF (L3 & MANAGERS)
        for user in fixed_staff:
            uid = user.id
            leave = get_leave_status(uid, current_day)

            if leave:
                new_entries.append(RosterEntry(
                    user_id=uid,
                    roster_date=current_day,
                    shift_type=getattr(leave, 'leave_type', 'Leave'),
                    shift_id=None
                ))
            elif is_weekend:
                new_entries.append(RosterEntry(
                    user_id=uid,
                    roster_date=current_day,
                    shift_type='OFF',
                    shift_id=None
                ))
            else:
                new_entries.append(RosterEntry(
                    user_id=uid,
                    roster_date=current_day,
                    shift_type='General',
                    shift_id=general_shift_id
                ))

        # B. 24/7 OPERATIONAL STAFF (L1 & L2)
        for user in op_staff:
            uid = user.id
            state = tracker[uid]
            leave = get_leave_status(uid, current_day)

            if leave:
                new_entries.append(RosterEntry(
                    user_id=uid,
                    roster_date=current_day,
                    shift_type=getattr(leave, 'leave_type', 'Leave'),
                    shift_id=None
                ))
                state['consecutive_work'] = 0
                state['consecutive_off'] = 0
                continue

            if state['consecutive_work'] == 5:
                new_entries.append(RosterEntry(
                    user_id=uid,
                    roster_date=current_day,
                    shift_type='OFF',
                    shift_id=None
                ))
                state['consecutive_work'] = 0
                state['consecutive_off'] = 1
                continue

            if state['consecutive_off'] == 1:
                new_entries.append(RosterEntry(
                    user_id=uid,
                    roster_date=current_day,
                    shift_type='OFF',
                    shift_id=None
                ))
                state['consecutive_off'] = 0
                if op_shift_ids:
                    state['shift_idx'] = (state['shift_idx'] + 1) % len(op_shift_ids)
                continue

            assigned_shift_id = op_shift_ids[state['shift_idx']] if op_shift_ids else None
            shift_name = shift_id_to_name.get(assigned_shift_id, 'Morning')
            
            new_entries.append(RosterEntry(
                user_id=uid,
                roster_date=current_day,
                shift_type=shift_name,
                shift_id=assigned_shift_id
            ))
            state['consecutive_work'] += 1

    db.session.add_all(new_entries)
    db.session.commit()
    return True, f"Roster successfully generated for {calendar.month_name[month]} {year}!"