import os
import sqlite3
from datetime import datetime

# Get the database paths
db_paths = ['instance/app.db', 'instance/fitbrainlab.db']

for db_path in db_paths:
    print(f"\nAttempting to fix database at {db_path}")
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} does not exist. Skipping.")
        continue
        
    try:
        # Connect to the database with a longer timeout
        conn = sqlite3.connect(db_path, timeout=30)
        
        # Set pragmas to optimize for concurrency
        conn.execute("PRAGMA journal_mode=DELETE")  # Use DELETE instead of WAL for better compatibility
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA busy_timeout=10000")  # 10 seconds
        
        # Vacuum the database to clean up any fragmentation
        conn.execute("VACUUM")
        
        # Get all tables in the database
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        
        print(f"Tables found: {', '.join(table_names)}")
        
        # Check if the user table exists
        if 'user' in table_names:
            # Check if the user table has backup_code and personal_code columns
            cursor.execute("PRAGMA table_info(user)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            print(f"User table columns: {', '.join(column_names)}")
            
            # Add backup_code and personal_code columns if they don't exist
            if 'backup_code' not in column_names:
                print("Adding backup_code column to user table")
                conn.execute("ALTER TABLE user ADD COLUMN backup_code TEXT UNIQUE")
            
            if 'personal_code' not in column_names:
                print("Adding personal_code column to user table")
                conn.execute("ALTER TABLE user ADD COLUMN personal_code TEXT UNIQUE")
                
            print("User table updated successfully!")
        else:
            print("User table not found in this database.")
        
        # Commit changes and close connection
        conn.commit()
        conn.close()
        
        print(f"Database {db_path} fixed successfully!")
        
    except Exception as e:
        print(f"Error fixing database {db_path}: {str(e)}")

print("\nDatabase fix script completed.")
