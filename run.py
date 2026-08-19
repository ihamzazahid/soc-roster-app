import os
from app import create_app, db
from app.models import User, Role, ExternalOnCall, RosterEntry, LeaveRequest

app = create_app()


@app.shell_context_processor
def make_shell_context():
    """Exposes DB and models automatically when running `flask shell`."""
    return {
        'db': db,
        'User': User,
        'Role': Role,
        'ExternalOnCall': ExternalOnCall,
        'RosterEntry': RosterEntry,
        'LeaveRequest': LeaveRequest
    }


# Ensure database tables exist when Gunicorn or Flask imports app
with app.app_context():
    db.create_all()


if __name__ == '__main__':
    # Used only when executing `python run.py` directly in local development
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() in ['true', '1', 't']

    app.run(host=host, port=port, debug=debug)