import calendar
from datetime import date, timedelta
from app import db
from app.models import User, Roster, LeaveRequest, Shift

def generate_monthly_roster(year: int, month: int):
    # Get total days in target month
    _, num_days = calendar.monthrange(year, month)
    start_date = date(year, month, 1)
    end_date = date(year, month, num_days)

    # 1. Clear existing roster for this specific month (prevents duplication)
    Roster.query.filter(
        Roster.roster_date >= start_date,
        Roster.roster_date <= end_date
    ).delete(synchronize_session=False)

    # 2. Get active analysts and available shift types
    analysts = User.query.filter_by(is_active=True).all()
    shifts = Shift.query.all()  # e.g., Day (08:00-16:00), Evening (16:00-00:00), Night (00:00-08:00)
    
    if not analysts or not shifts:
        return False, "No active analysts or shift types configured."

    # Map available shifts
    shift_pool = [s.id for s in shifts]

    # Track consecutive workdays and current shift index for each analyst
    # Format: analyst_id -> {'consecutive_work': int, 'consecutive_off': int, 'shift_idx': int}
    tracker = {
        a.id: {'consecutive_work': 0, 'consecutive_off': 0, 'shift_idx': idx % len(shift_pool)}
        for idx, a in enumerate(analysts)
    }

    # Fetch all approved leaves for the month
    approved_leaves = LeaveRequest.query.filter(
        LeaveRequest.status == 'Approved',
        LeaveRequest.start_date <= end_date,
        LeaveRequest.end_date >= start_date
    ).all()

    # Helper function to check if analyst is on approved leave on a given date
    def is_on_leave(user_id, current_day):
        for leave in approved_leaves:
            if leave.user_id == user_id and leave.start_date <= current_day <= leave.end_date:
                return True
        return False

    # 3. Generate schedule day-by-day for the month
    for day in range(1, num_days + 1):
        current_day = date(year, month, day)

        for user in analysts:
            uid = user.id
            state = tracker[uid]

            # Check Leave Status
            if is_on_leave(uid, current_day):
                new_roster = Roster(
                    user_id=uid,
                    roster_date=current_day,
                    status='Leave',
                    shift_id=None
                )
                db.session.add(new_roster)
                # Leave resets work streak
                state['consecutive_work'] = 0
                state['consecutive_off'] = 0
                continue

            # Check 5 Work Days -> 2 Off Days Rotation
            if state['consecutive_work'] == 5:
                # Assign OFF Day 1
                new_roster = Roster(
                    user_id=uid,
                    roster_date=current_day,
                    status='OFF',
                    shift_id=None
                )
                db.session.add(new_roster)
                state['consecutive_work'] = 0
                state['consecutive_off'] = 1
                continue

            if state['consecutive_off'] == 1:
                # Assign OFF Day 2
                new_roster = Roster(
                    user_id=uid,
                    roster_date=current_day,
                    status='OFF',
                    shift_id=None
                )
                db.session.add(new_roster)
                state['consecutive_off'] = 0
                
                # ROTATE SHIFT: After completing 2 days off, switch to the next shift timing
                state['shift_idx'] = (state['shift_idx'] + 1) % len(shift_pool)
                continue

            # Assign Work Shift
            assigned_shift_id = shift_pool[state['shift_idx']]
            new_roster = Roster(
                user_id=uid,
                roster_date=current_day,
                status='Working',
                shift_id=assigned_shift_id
            )
            db.session.add(new_roster)
            state['consecutive_work'] += 1

    db.session.commit()
    return True, f"Roster successfully generated for {calendar.month_name[month]} {year}!"