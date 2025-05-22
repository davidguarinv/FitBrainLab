import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from config import Config

def add_missing_columns():
    """Add missing columns to the User table"""
    print("Adding missing columns to the User table...")
    
    # Extract the database path from the SQLAlchemy URI
    db_path = Config.DATABASE_PATH
    print(f"Using database at: {db_path}")
    
    # Ensure the directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if the columns already exist
    cursor.execute("PRAGMA table_info(user)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'last_week_visited' not in columns:
        print("Adding last_week_visited column...")
        cursor.execute("ALTER TABLE user ADD COLUMN last_week_visited INTEGER")
    
    if 'last_year_visited' not in columns:
        print("Adding last_year_visited column...")
        cursor.execute("ALTER TABLE user ADD COLUMN last_year_visited INTEGER")
    
    conn.commit()
    conn.close()
    
    print("Migration completed successfully!")

if __name__ == '__main__':
    add_missing_columns()
