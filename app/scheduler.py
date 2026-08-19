import calendar
from datetime import date, timedelta
from app.models import db, User, RosterEntry, LeaveRequest

SHIFTS = ['Morning', 'Evening', 'Night']

def is_user_on_leave(user_id, target_date):
    """Check if the given analyst has approved leave on target_date."""
    leave = LeaveRequest.query.filter(
        LeaveRequest.user_id == user_id,
        LeaveRequest.status == 'Approved',
        LeaveRequest.start_date <= target_date,
        LeaveRequest.end_date >= target_date
    ).first()
    return leave is not None

def generate_monthly_roster(year, month):
    """
    Generates deterministic 24/7 roster with L2 mandatory coverage in peak shifts.
    """
    _, num_days = calendar.monthrange(year, month)
    
    # 1. Fetch Active Analysts categorized by Tier
    all_users = User.query.filter_by(is_active=True).all()
    
    l2_users = [u for u in all_users if u.tier in ['L2', 'L3', 'SOC Lead', 'Tier-2', 'Tier-3']]
    l1_users = [u for u in all_users if u.tier not in ['L2', 'L3', 'SOC Lead', 'Tier-2', 'Tier-3']]
    
    # Fallback: Treat all as general pool if tier classification is missing
    if not l2_users:
        l2_users = all_users
    if not l1_users:
        l1_users = all_users

    # Delete existing manual overrides non-protected entries for clean recalculation
    RosterEntry.query.filter(
        db.extract('year', RosterEntry.roster_date) == year,
        db.extract('month', RosterEntry.roster_date) == month,
        RosterEntry.is_override == False
    ).delete(synchronize_session=False)

    l2_idx = 0
    l1_idx = 0

    for day in range(1, num_days + 1):
        current_date = date(year, month, day)
        
        # Track who is assigned today to prevent double shifts
        assigned_today = set()

        # Previous day's night shift analysts (to enforce rest rules)
        yesterday = current_date - timedelta(days=1)
        yesterday_night_entries = RosterEntry.query.filter_by(
            roster_date=yesterday, 
            shift_type='Night'
        ).all()
        night_rest_user_ids = {e.user_id for e in yesterday_night_entries}

        # ------------------------------------------------------------------
        # 1. MORNING SHIFT (Mandatory L2 + L1)
        # ------------------------------------------------------------------
        # Pick L2 Lead
        morning_l2 = None
        for _ in range(len(l2_users)):
            candidate = l2_users[l2_idx % len(l2_users)]
            l2_idx += 1
            if candidate.id not in night_rest_user_ids and not is_user_on_leave(candidate.id, current_date):
                morning_l2 = candidate
                break

        # Pick L1 Analyst
        morning_l1 = None
        for _ in range(len(l1_users)):
            candidate = l1_users[l1_idx % len(l1_users)]
            l1_idx += 1
            if candidate.id != getattr(morning_l2, 'id', None) and candidate.id not in night_rest_user_ids and not is_user_on_leave(candidate.id, current_date):
                morning_l1 = candidate
                break

        for u in [morning_l2, morning_l1]:
            if u and u.id not in assigned_today:
                db.session.add(RosterEntry(user_id=u.id, roster_date=current_date, shift_type='Morning'))
                assigned_today.add(u.id)

        # ------------------------------------------------------------------
        # 2. EVENING SHIFT (Mandatory L2/L3 + L1)
        # ------------------------------------------------------------------
        evening_l2 = None
        for _ in range(len(l2_users)):
            candidate = l2_users[l2_idx % len(l2_users)]
            l2_idx += 1
            if candidate.id not in assigned_today and candidate.id not in night_rest_user_ids and not is_user_on_leave(candidate.id, current_date):
                evening_l2 = candidate
                break

        evening_l1 = None
        for _ in range(len(l1_users)):
            candidate = l1_users[l1_idx % len(l1_users)]
            l1_idx += 1
            if candidate.id not in assigned_today and candidate.id not in night_rest_user_ids and not is_user_on_leave(candidate.id, current_date):
                evening_l1 = candidate
                break

        for u in [evening_l2, evening_l1]:
            if u and u.id not in assigned_today:
                db.session.add(RosterEntry(user_id=u.id, roster_date=current_date, shift_type='Evening'))
                assigned_today.add(u.id)

        # ------------------------------------------------------------------
        # 3. NIGHT SHIFT (Overnight Operational Coverage)
        # ------------------------------------------------------------------
        night_analyst = None
        for _ in range(len(all_users)):
            candidate = all_users[(l1_idx + l2_idx) % len(all_users)]
            l1_idx += 1
            if candidate.id not in assigned_today and not is_user_on_leave(candidate.id, current_date):
                night_analyst = candidate
                break

        if night_analyst and night_analyst.id not in assigned_today:
            db.session.add(RosterEntry(user_id=night_analyst.id, roster_date=current_date, shift_type='Night'))
            assigned_today.add(night_analyst.id)

        # ------------------------------------------------------------------
        # 4. MARK REMAINING ANALYSTS AS OFF OR LEAVE
        # ------------------------------------------------------------------
        for user in all_users:
            if user.id not in assigned_today:
                if is_user_on_leave(user.id, current_date):
                    db.session.add(RosterEntry(user_id=user.id, roster_date=current_date, shift_type='Leave'))
                else:
                    db.session.add(RosterEntry(user_id=user.id, roster_date=current_date, shift_type='OFF'))

    db.session.commit()