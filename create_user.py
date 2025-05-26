import os
import sys
import sqlite3
import hashlib
import secrets
import string
from datetime import datetime

def generate_password_hash(password):
    """Generate a secure password hash."""
    salt = secrets.token_hex(8)
    hash_obj = hashlib.scrypt(
        password.encode('utf-8'),
        salt=salt.encode('utf-8'),
        n=32768,
        r=8,
        p=1,
        dklen=64
    )
    return f"scrypt:32768:8:1${salt}${hash_obj.hex()}"

def generate_backup_code():
    """Generate a unique backup code."""
    return secrets.token_hex(8)  # 16 character hex string

def generate_personal_code():
    """Generate a unique personal code."""
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(8))

def create_user(username, password):
    """Create a new user directly in the database."""
    # Get the database paths
    db_paths = ['instance/app.db', 'instance/fitbrainlab.db']
    
    for db_path in db_paths:
        print(f"\nAttempting to create user in database at {db_path}")
        
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
            
            # Get all tables in the database
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            table_names = [table[0] for table in tables]
            
            print(f"Tables found: {', '.join(table_names)}")
            
            # Check if the user table exists
            if 'user' in table_names:
                # Check if the username already exists
                cursor.execute("SELECT id FROM user WHERE username = ?", (username,))
                existing_user = cursor.fetchone()
                if existing_user:
                    print(f"User {username} already exists in database {db_path}.")
                    conn.close()
                    continue
                
                # Check if the user table has backup_code and personal_code columns
                cursor.execute("PRAGMA table_info(user)")
                columns = cursor.fetchall()
                column_names = [col[1] for col in columns]
                
                # Generate user data
                password_hash = generate_password_hash(password)
                backup_code = generate_backup_code()
                personal_code = generate_personal_code()
                created_at = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')
                
                # Prepare the SQL statement based on available columns
                columns_list = ['username', 'password_hash', 'is_public', 'created_at']
                values_list = [username, password_hash, 1, created_at]
                
                # Add backup_code and personal_code if the columns exist
                if 'backup_code' in column_names:
                    columns_list.append('backup_code')
                    values_list.append(backup_code)
                
                if 'personal_code' in column_names:
                    columns_list.append('personal_code')
                    values_list.append(personal_code)
                
                # Add default values for other columns
                if 'daily_e_count' in column_names:
                    columns_list.append('daily_e_count')
                    values_list.append(0)
                
                if 'daily_m_count' in column_names:
                    columns_list.append('daily_m_count')
                    values_list.append(0)
                
                if 'daily_h_count' in column_names:
                    columns_list.append('daily_h_count')
                    values_list.append(0)
                
                if 'weekly_e_cap' in column_names:
                    columns_list.append('weekly_e_cap')
                    values_list.append(9)
                
                if 'weekly_m_cap' in column_names:
                    columns_list.append('weekly_m_cap')
                    values_list.append(6)
                
                if 'weekly_h_cap' in column_names:
                    columns_list.append('weekly_h_cap')
                    values_list.append(3)
                
                if 'weekly_e_completed' in column_names:
                    columns_list.append('weekly_e_completed')
                    values_list.append(0)
                
                if 'weekly_m_completed' in column_names:
                    columns_list.append('weekly_m_completed')
                    values_list.append(0)
                
                if 'weekly_h_completed' in column_names:
                    columns_list.append('weekly_h_completed')
                    values_list.append(0)
                
                # Build the SQL statement
                columns_str = ', '.join(columns_list)
                placeholders = ', '.join(['?' for _ in values_list])
                sql = f"INSERT INTO user ({columns_str}) VALUES ({placeholders})"
                
                # Execute the SQL statement
                cursor.execute(sql, values_list)
                conn.commit()
                
                print(f"User {username} created successfully in database {db_path}!")
                print(f"Backup code: {backup_code}")
                print(f"Personal code: {personal_code}")
                
                conn.close()
                return True
            else:
                print(f"User table not found in database {db_path}.")
                conn.close()
        
        except Exception as e:
            print(f"Error creating user in database {db_path}: {str(e)}")
            try:
                conn.close()
            except:
                pass
    
    print("\nFailed to create user in any database.")
    return False

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python create_user.py <username> <password>")
        sys.exit(1)
    
    username = sys.argv[1]
    password = sys.argv[2]
    
    success = create_user(username, password)
    
    if success:
        print("\nUser created successfully!")
    else:
        print("\nFailed to create user.")
        sys.exit(1)
