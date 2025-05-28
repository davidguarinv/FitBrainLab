#!/usr/bin/env python
"""
Deploy schema and seed data to Supabase

This script connects to your Supabase PostgreSQL database
and executes the SQL schema and seed scripts.
"""

import os
import sys
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
import argparse

# Load environment variables
load_dotenv()

def get_connection_string():
    """Get PostgreSQL connection string from environment variables"""
    # Get Supabase connection parameters from environment variables
    db_host = os.environ.get("SUPABASE_DB_HOST")
    db_port = os.environ.get("SUPABASE_DB_PORT", "6543")
    db_name = os.environ.get("SUPABASE_DB_NAME", "postgres")
    db_user = os.environ.get("SUPABASE_DB_USER")
    db_pass = os.environ.get("SUPABASE_DB_PASSWORD")
    
    # Validate required variables are present
    if not all([db_host, db_user, db_pass]):
        print("Error: Missing required Supabase database connection information")
        print("Please ensure SUPABASE_DB_HOST, SUPABASE_DB_USER, and SUPABASE_DB_PASSWORD are set in .env")
        sys.exit(1)
    
    # Format connection string
    return f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

def execute_sql_file(conn, file_path):
    """Execute SQL statements from a file"""
    try:
        print(f"Executing SQL from: {file_path}")
        
        # Read the SQL file
        with open(file_path, 'r') as sql_file:
            sql_content = sql_file.read()
            
        # Create a cursor and execute the SQL
        cursor = conn.cursor()
        cursor.execute(sql_content)
        conn.commit()
        cursor.close()
        
        print(f"Successfully executed: {file_path}")
        return True
    except Exception as e:
        print(f"Error executing SQL from {file_path}: {e}")
        conn.rollback()
        return False

def main():
    parser = argparse.ArgumentParser(description='Deploy schema and seed data to Supabase')
    parser.add_argument('--schema-only', action='store_true', help='Deploy schema only, skip seed data')
    parser.add_argument('--seed-only', action='store_true', help='Deploy seed data only, skip schema')
    args = parser.parse_args()
    
    conn_string = get_connection_string()
    
    try:
        # Connect to the database
        print("Connecting to Supabase PostgreSQL database...")
        conn = psycopg2.connect(conn_string)
        
        # Get the full path to the script directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Deploy schema (unless --seed-only is specified)
        if not args.seed_only:
            schema_path = os.path.join(script_dir, "supabase_schema.sql")
            if not execute_sql_file(conn, schema_path):
                print("Schema deployment failed. Exiting.")
                sys.exit(1)
        
        # Deploy seed data (unless --schema-only is specified)
        if not args.schema_only:
            seed_path = os.path.join(script_dir, "seed_supabase_challenges.sql")
            if not execute_sql_file(conn, seed_path):
                print("Seed data deployment failed.")
                sys.exit(1)
        
        print("Deployment completed successfully!")
        
    except Exception as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    main()
