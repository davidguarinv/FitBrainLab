import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the absolute path to the project directory
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Core configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Dynamic database configuration based on environment
    ENV = os.environ.get('FLASK_ENV', 'development')
    
    # Database connection handling
    if ENV == 'production':
        # Check for Supabase configuration first
        use_supabase = os.environ.get('USE_SUPABASE', 'false').lower() == 'true'
        
        if use_supabase:
            # Import here to avoid circular imports
            try:
                from utils.supabase_helper import get_supabase_connection_string
                database_url = get_supabase_connection_string()
            except (ImportError, ValueError):
                print("WARNING: Supabase helper not available or configuration incomplete")
                # Fallback to DATABASE_URL if Supabase config fails
                database_url = os.environ.get('DATABASE_URL')
        else:
            # Standard DATABASE_URL approach
            database_url = os.environ.get('DATABASE_URL')
        
        # Handle Heroku's postgres:// vs postgresql:// discrepancy
        if database_url and database_url.startswith('postgres:'):
            database_url = database_url.replace('postgres:', 'postgresql:', 1)
        
        # Support DISABLE_DB mode in production for static site features
        disable_db = os.environ.get('DISABLE_DB', 'false').lower() == 'true'
        if disable_db:
            print("WARNING: Running in DB-disabled mode. Database features will not be available.")
            SQLALCHEMY_DATABASE_URI = None
        else:
            SQLALCHEMY_DATABASE_URI = database_url
            
        # Remove SQLite-specific options in production
        SQLALCHEMY_ENGINE_OPTIONS = {}
    else:
        # Development environment - use SQLite
        DATABASE_PATH = os.path.join(basedir, 'instance', 'fitbrainlab.db')
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{DATABASE_PATH}'
        # SQLite-specific options
        SQLALCHEMY_ENGINE_OPTIONS = {
            'connect_args': {
                'check_same_thread': False
            }
        }
    
    # Data files configuration
    FUN_FACTS_FILE = os.path.join(basedir, 'fun_facts.json')
    
    # Email configuration
    RECIPIENT_EMAIL = os.environ.get('RECIPIENT_EMAIL')
    SMTP_SERVER = os.environ.get('SMTP_SERVER')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
    EMAIL_USER = os.environ.get('EMAIL_USER')
    EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')

