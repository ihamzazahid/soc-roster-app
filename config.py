import os

# Base directory (/app)
basedir = os.path.abspath(os.path.dirname(__file__))

# If config.py lives inside /app/app/, step up one level to /app
if os.path.basename(basedir) == 'app':
    basedir = os.path.abspath(os.path.join(basedir, '..'))

instance_path = os.path.join(basedir, 'instance')
os.makedirs(instance_path, exist_ok=True)

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'soc-roster-secret-key-2026'
    
    # Points explicitly to /app/instance/soc_roster.db
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(instance_path, 'soc_roster.db')
        
    SQLALCHEMY_TRACK_MODIFICATIONS = False