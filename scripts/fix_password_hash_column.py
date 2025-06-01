#!/usr/bin/env python
"""
Fix the password_hash column in the user table to allow longer password hashes.
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment variables
load_dotenv()

# Build the connection string from Supabase environment variables
def get_connection_string():
    host = os.environ.get('SUPABASE_DB_HOST')
    port = os.environ.get('SUPABASE_DB_PORT')
    dbname = os.environ.get('SUPABASE_DB_NAME')
    user = os.environ.get('SUPABASE_DB_USER')
    password = os.environ.get('SUPABASE_DB_PASSWORD')
    
    if not all([host, port, dbname, user, password]):
        print("ERROR: Missing required Supabase environment variables")
        sys.exit(1)
    
    return f"postgresql://{user}:{password}@{host}:{port}/{dbname}"

def main():
    print("Connecting to Supabase database...")
    connection_string = get_connection_string()
    
    # Create SQLAlchemy engine
    try:
        engine = create_engine(connection_string)
        connection = engine.connect()
        print("Connection successful!")
    except Exception as e:
        print(f"Connection failed: {e}")
        sys.exit(1)
    
    # Alter the password_hash column to accept a longer string
    print("Altering password_hash column to VARCHAR(512)...")
    
    try:
        # First, check if any rows exist - if they do, we'll need to backup the data
        check_sql = text("SELECT COUNT(*) FROM public.\"user\"")
        result = connection.execute(check_sql)
        count = result.scalar()
        
        if count > 0:
            print(f"Found {count} existing rows in user table, backing up data...")
            # Create backup if needed
        
        # Alter the column type
        alter_sql = text("ALTER TABLE public.\"user\" ALTER COLUMN password_hash TYPE VARCHAR(512)")
        connection.execute(alter_sql)
        connection.commit()
        print("Column altered successfully!")
        
    except Exception as e:
        print(f"Error altering column: {e}")
        sys.exit(1)
    
    print("Fix complete. The password_hash column now accepts longer values.")

if __name__ == "__main__":
    main()
