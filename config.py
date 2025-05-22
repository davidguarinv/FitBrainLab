import os

# Get the absolute path to the project directory
basedir = os.path.abspath(os.path.dirname(__file__))

# Set environment variables if not already set
if not os.environ.get('RECIPIENT_EMAIL'):
    os.environ['RECIPIENT_EMAIL'] = 'davidguarinv@gmail.com'  # Your Gmail where you want to receive the emails
if not os.environ.get('SMTP_SERVER'):
    os.environ['SMTP_SERVER'] = 'smtp.gmail.com'  # Using Gmail's SMTP server
if not os.environ.get('SMTP_PORT'):
    os.environ['SMTP_PORT'] = '587'
if not os.environ.get('EMAIL_USER'):
    os.environ['EMAIL_USER'] = 'fitbrainlab@gmail.com'  # Create a new Gmail account for the lab
if not os.environ.get('EMAIL_PASSWORD'):
    os.environ['EMAIL_PASSWORD'] = 'your_app_specific_password'  # You'll need to set this with an app-specific password

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'
    # Use absolute path for SQLite database
    DATABASE_PATH = os.path.join(basedir, 'instance', 'fitbrainlab.db')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{DATABASE_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Email configuration
    # The email address where form submissions will be sent
    RECIPIENT_EMAIL = os.environ.get('RECIPIENT_EMAIL') or 'davidguarinv@gmail.com'  # Your Gmail where you want to receive the emails
    
    # SMTP server configuration
    SMTP_SERVER = 'smtp.gmail.com'  # Using Gmail's SMTP server
    SMTP_PORT = 587
    # Gmail account for the lab
    EMAIL_USER = os.environ.get('EMAIL_USER') or 'fitbrainlab@gmail.com'  # Create a new Gmail account for the lab
    # App-specific password for Gmail
    EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')  # You'll need to set this with an app-specific password
