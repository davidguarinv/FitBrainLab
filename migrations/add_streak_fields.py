from flask import Flask
import sys
import os

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import db, create_app
import sqlite3
import os

def run_migration():
    """Add streak and daily challenge count fields to the User table"""
    # Get the path to the database file
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, '..', 'instance', 'fitbrainlab.db')
    
    # Check if the database file exists
    if not os.path.exists(db_path):
        print(f"Database file not found at {db_path}")
        return
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if the columns already exist
    cursor.execute("PRAGMA table_info(user)")
    columns = [column[1] for column in cursor.fetchall()]
    
    # Add the new columns if they don't exist
    if 'daily_streak' not in columns:
        print("Adding daily_streak column to user table...")
        cursor.execute("ALTER TABLE user ADD COLUMN daily_streak INTEGER DEFAULT 0")
    
    if 'last_challenge_date' not in columns:
        print("Adding last_challenge_date column to user table...")
        cursor.execute("ALTER TABLE user ADD COLUMN last_challenge_date DATE")
    
    if 'daily_e_count' not in columns:
        print("Adding daily_e_count column to user table...")
        cursor.execute("ALTER TABLE user ADD COLUMN daily_e_count INTEGER DEFAULT 0")
    
    if 'daily_m_count' not in columns:
        print("Adding daily_m_count column to user table...")
        cursor.execute("ALTER TABLE user ADD COLUMN daily_m_count INTEGER DEFAULT 0")
    
    if 'daily_h_count' not in columns:
        print("Adding daily_h_count column to user table...")
        cursor.execute("ALTER TABLE user ADD COLUMN daily_h_count INTEGER DEFAULT 0")
    
    # Commit the changes and close the connection
    conn.commit()
    conn.close()
    
    print("Migration completed successfully!")

if __name__ == '__main__':
    run_migration()
