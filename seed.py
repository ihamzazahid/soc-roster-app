import sys
import os
from datetime import date, datetime, time, timedelta
import calendar

from app import create_app, db
from app.models import Role, User, Shift, ExternalOnCall, RosterEntry, LeaveRequest
from app.scheduler import generate_monthly_roster

app = create_app()

def seed_database():
    with app.app_context():
        print("Initializing SOC database setup...")
        db.create_all()

        DEFAULT_PASSWORD = "Password123!"

        # 1. Seed Roles
        roles_data = ['Admin', 'SOC_Manager', 'Analyst', 'Read_Only']
        roles_map = {}
        for role_name in roles_data:
            role = Role.query.filter_by(name=role_name).first()
            if not role:
                role = Role(name=role_name)
                db.session.add(role)
                db.session.flush()
                print(f"Added role: {role_name}")
            roles_map[role_name] = role.id

        # 2. Seed Shift Definitions
        shifts_data = [
            {"name": "General", "start_time": time(9, 0), "end_time": time(17, 0)},
            {"name": "Morning", "start_time": time(7, 0), "end_time": time(15, 0)},
            {"name": "Evening", "start_time": time(15, 0), "end_time": time(23, 0)},
            {"name": "Night", "start_time": time(23, 0), "end_time": time(7, 0)},
            {"name": "OFF", "start_time": None, "end_time": None},
            {"name": "Leave", "start_time": None, "end_time": None},
        ]
        shifts_map = {}
        for s in shifts_data:
            shift = Shift.query.filter_by(name=s["name"]).first()
            if not shift:
                shift = Shift(name=s["name"], start_time=s["start_time"], end_time=s["end_time"])
                db.session.add(shift)
                db.session.flush()
                print(f"Added shift: {s['name']}")
            shifts_map[s["name"]] = shift.id

        db.session.commit()

        # 3. Seed System Admin
        admin_email = "admin@company.com"
        admin = User.query.filter_by(email=admin_email).first()
        if not admin:
            admin = User(
                name="System Administrator",
                email=admin_email,
                phone="+1-555-0000",
                role_id=roles_map['Admin'],
                tier="Manager",
                joining_date=date(2020, 1, 1),
                annual_leave_allocated=25,
                annual_leave_used=0,
                sick_leave_monthly_used=0,
                sick_leave_total_used=0,
                is_active=True
            )
            admin.set_password(DEFAULT_PASSWORD)
            db.session.add(admin)
            print("Added System Admin: admin@company.com")

        # 4. Seed SOC Manager
        manager_email = "soc.manager@company.com"
        manager = User.query.filter_by(email=manager_email).first()
        if not manager:
            manager = User(
                name="Sarah Jenkins",
                email=manager_email,
                phone="+1-555-0199",
                role_id=roles_map['SOC_Manager'],
                tier="Manager",
                joining_date=date(2021, 3, 15),
                annual_leave_allocated=25,
                annual_leave_used=4,
                sick_leave_monthly_used=0,
                sick_leave_total_used=2,
                is_active=True
            )
            manager.set_password(DEFAULT_PASSWORD)
            db.session.add(manager)
            print("Added SOC Manager: Sarah Jenkins")

        # 5. Seed L3 Analysts
        l3_analysts = [
            ("Alex Mercer", "alex.mercer@company.com", "+1-555-0101", date(2022, 1, 10)),
            ("Elena Rostova", "elena.rostova@company.com", "+1-555-0102", date(2022, 6, 1)),
        ]
        for name, email, phone, joined in l3_analysts:
            if not User.query.filter_by(email=email).first():
                user = User(
                    name=name,
                    email=email,
                    phone=phone,
                    role_id=roles_map['Analyst'],
                    tier="L3",
                    joining_date=joined,
                    annual_leave_allocated=22,
                    annual_leave_used=5,
                    sick_leave_monthly_used=1,
                    sick_leave_total_used=3,
                    is_active=True
                )
                user.set_password(DEFAULT_PASSWORD)
                db.session.add(user)
                print(f"Added L3 Analyst: {name}")

        # 6. Seed L2 Analysts
        l2_analysts = [
            ("David Vance", "david.vance@company.com", "+1-555-0201", date(2023, 2, 15)),
            ("Priya Sharma", "priya.sharma@company.com", "+1-555-0202", date(2023, 4, 20)),
        ]
        for name, email, phone, joined in l2_analysts:
            if not User.query.filter_by(email=email).first():
                user = User(
                    name=name,
                    email=email,
                    phone=phone,
                    role_id=roles_map['Analyst'],
                    tier="L2",
                    joining_date=joined,
                    annual_leave_allocated=20,
                    annual_leave_used=2,
                    sick_leave_monthly_used=0,
                    sick_leave_total_used=1,
                    is_active=True
                )
                user.set_password(DEFAULT_PASSWORD)
                db.session.add(user)
                print(f"Added L2 Analyst: {name}")

        # 7. Seed L1 Analysts
        l1_analysts = [
            ("James Wilson", "james.wilson@company.com", "+1-555-0301", date(2024, 1, 15)),
            ("Maria Garcia", "maria.garcia@company.com", "+1-555-0302", date(2024, 2, 1)),
            ("Liam Chen", "liam.chen@company.com", "+1-555-0303", date(2024, 3, 10)),
            ("Zoe Taylor", "zoe.taylor@company.com", "+1-555-0304", date(2024, 5, 12)),
            ("Omar Hassan", "omar.hassan@company.com", "+1-555-0305", date(2024, 7, 1)),
        ]
        for name, email, phone, joined in l1_analysts:
            if not User.query.filter_by(email=email).first():
                user = User(
                    name=name,
                    email=email,
                    phone=phone,
                    role_id=roles_map['Analyst'],
                    tier="L1",
                    joining_date=joined,
                    annual_leave_allocated=20,
                    annual_leave_used=0,
                    sick_leave_monthly_used=0,
                    sick_leave_total_used=0,
                    is_active=True
                )
                user.set_password(DEFAULT_PASSWORD)
                db.session.add(user)
                print(f"Added L1 Analyst: {name}")

        # 8. Seed Sample Leave Request
        today = date.today()
        sample_user = User.query.filter_by(email="james.wilson@company.com").first()
        if sample_user and not LeaveRequest.query.filter_by(user_id=sample_user.id).first():
            leave = LeaveRequest(
                user_id=sample_user.id,
                leave_type="Annual",
                start_date=today + timedelta(days=5),
                end_date=today + timedelta(days=7),
                status="Approved"
            )
            db.session.add(leave)
            print(f"Added sample leave request for: {sample_user.name}")

        db.session.commit()

        # 9. Trigger Roster Generation for Current Month
        print(f"Generating roster schedule for {today.strftime('%B %Y')}...")
        generate_monthly_roster(today.year, today.month)

        # Backfill shift_id on generated roster entries if missing
        roster_entries = RosterEntry.query.filter(RosterEntry.shift_id == None).all()
        for entry in roster_entries:
            if entry.shift_type in shifts_map:
                entry.shift_id = shifts_map[entry.shift_type]
        db.session.commit()

        # 10. Seed Internal Escalation On-Call Flags
        l3_user = User.query.filter_by(tier="L3").first()
        if l3_user:
            oncall_entry = RosterEntry.query.filter_by(
                user_id=l3_user.id, 
                roster_date=today
            ).first()
            if oncall_entry:
                oncall_entry.is_on_call = True
                print(f"Assigned internal on-call duty to L3: {l3_user.name}")

        # 11. Seed External On-Call Contacts
        next_month = today + timedelta(days=30)
        external_teams = [
            ("Infra Team", "Robert Ford", "Principal Cloud Engineer", "robert.ford@company.com", "+1-555-0801"),
            ("DevSecOps Team", "Anita Patel", "DevSecOps Lead", "anita.patel@company.com", "+1-555-0802"),
            ("VTM Team", "Marcus Brody", "Vulnerability Manager", "marcus.brody@company.com", "+1-555-0803"),
            ("Onboarding Team", "Claire Bennet", "Integration Specialist", "claire.bennet@company.com", "+1-555-0804"),
        ]

        for team_name, name, title, email, phone in external_teams:
            if not ExternalOnCall.query.filter_by(email=email).first():
                oncall = ExternalOnCall(
                    team_name=team_name,
                    name=name,
                    title=title,
                    email=email,
                    phone=phone,
                    start_date=today,
                    end_date=next_month
                )
                db.session.add(oncall)
                print(f"Added External On-Call Contact: {name} ({team_name})")

        db.session.commit()
        print("\n✅ Database seeding and roster auto-generation completed successfully!")
        print(f"🔑 Default password for all user accounts: '{DEFAULT_PASSWORD}'")


if __name__ == '__main__':
    seed_database()