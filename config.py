import os

# Resolves to project root directory (/app)
basedir = os.path.abspath(os.path.dirname(__file__))
if os.path.basename(basedir) == 'app':
    basedir = os.path.dirname(basedir)

instance_path = os.path.join(basedir, 'instance')
os.makedirs(instance_path, exist_ok=True)

# Full path to database (/app/instance/soc_roster.db)
db_file = os.path.join(instance_path, 'soc_roster.db')

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'soc-roster-secret-key-2026'
    
    # Ensures 4 slashes format explicitly includes /app
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f"sqlite:////{db_file.lstrip('/')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False