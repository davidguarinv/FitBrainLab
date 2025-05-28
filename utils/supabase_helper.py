import os
from supabase import create_client
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

def get_supabase_client():
    """Create and return a Supabase client"""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
    
    return create_client(url, key)

def get_supabase_connection_string():
    """Get a PostgreSQL connection string for Supabase"""
    # Format is: postgresql://postgres.[ref]:[PASSWORD]@[HOST]:[PORT]/postgres
    db_host = os.environ.get("SUPABASE_DB_HOST")
    db_port = os.environ.get("SUPABASE_DB_PORT", "6543")  # Transaction pooler uses port 6543
    db_name = os.environ.get("SUPABASE_DB_NAME", "postgres")
    db_user = os.environ.get("SUPABASE_DB_USER")
    db_pass = os.environ.get("SUPABASE_DB_PASSWORD")
    
    if not all([db_host, db_user, db_pass]):
        raise ValueError("Supabase database connection information is incomplete")
    
    # Construct the connection string
    # Note: The format for transaction pooler is slightly different from standard PostgreSQL
    return f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

def get_sqlalchemy_engine():
    """Create a SQLAlchemy engine for Supabase PostgreSQL"""
    connection_string = get_supabase_connection_string()
    return create_engine(connection_string)

def get_session():
    """Create a SQLAlchemy session for Supabase"""
    engine = get_sqlalchemy_engine()
    Session = sessionmaker(bind=engine)
    return Session()
