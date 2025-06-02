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
    
    # Email configuration
    EMAIL_USER = os.environ.get('EMAIL_USER')
    EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
    RECIPIENT_EMAIL = os.environ.get('RECIPIENT_EMAIL')
    SMTP_SERVER = os.environ.get('SMTP_SERVER')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
    
    # Dynamic database configuration based on environment
    ENV = os.environ.get('FLASK_ENV', 'development')
    
    # Check for Supabase configuration first (regardless of environment)
    use_supabase = os.environ.get('USE_SUPABASE', 'false').lower() == 'true'
    disable_db = os.environ.get('DISABLE_DB', 'false').lower() == 'true'
    
    # Database connection handling
    if use_supabase:
        print("INFO: Using Supabase PostgreSQL database")
        # Build connection string from individual environment variables
        host = os.environ.get('SUPABASE_DB_HOST')
        port = os.environ.get('SUPABASE_DB_PORT')
        dbname = os.environ.get('SUPABASE_DB_NAME')
        user = os.environ.get('SUPABASE_DB_USER')
        password = os.environ.get('SUPABASE_DB_PASSWORD')
        
        if all([host, port, dbname, user, password]):
            database_url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
            print(f"INFO: Supabase connection established to {host}:{port}/{dbname}")
        else:
            print("WARNING: Incomplete Supabase configuration, missing required values")
            database_url = None
        
        # Using PostgreSQL-specific options
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_size': 10,
            'pool_recycle': 3600
        }
    elif ENV == 'production':
        # Standard DATABASE_URL approach for production when not using Supabase
        database_url = os.environ.get('DATABASE_URL')
        
        # Handle Heroku's postgres:// vs postgresql:// discrepancy
        if database_url and database_url.startswith('postgres:'):
            database_url = database_url.replace('postgres:', 'postgresql:', 1)
            
        # Remove SQLite-specific options in production
        SQLALCHEMY_ENGINE_OPTIONS = {}
    else:
        # Development environment with SQLite (when not using Supabase)
        print("INFO: Using SQLite database (development mode)")
        DATABASE_PATH = os.path.join(basedir, 'instance', 'fitbrainlab.db')
        database_url = f'sqlite:///{DATABASE_PATH}'
        # SQLite-specific options
        SQLALCHEMY_ENGINE_OPTIONS = {
            'connect_args': {
                'check_same_thread': False
            }
        }
    
    # Support DISABLE_DB mode for static site features
    if disable_db:
        print("WARNING: Running in DB-disabled mode. Database features will not be available.")
        SQLALCHEMY_DATABASE_URI = None
    else:
        SQLALCHEMY_DATABASE_URI = database_url
    
    # Data files configuration
    FUN_FACTS_FILE = os.path.join(basedir, 'fun_facts.json')
    
    # Email configuration
    RECIPIENT_EMAIL = os.environ.get('RECIPIENT_EMAIL')
    SMTP_SERVER = os.environ.get('SMTP_SERVER')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
    EMAIL_USER = os.environ.get('EMAIL_USER')
    EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')

