import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the absolute path to the project directory
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'
    DATABASE_PATH = os.path.join(basedir, 'instance', 'fitbrainlab.db')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{DATABASE_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Email configuration
    RECIPIENT_EMAIL = os.environ.get('RECIPIENT_EMAIL')
    SMTP_SERVER = os.environ.get('SMTP_SERVER')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
    EMAIL_USER = os.environ.get('EMAIL_USER')
    EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
