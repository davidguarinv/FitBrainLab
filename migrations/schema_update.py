"""
Schema update script for adding new columns to existing tables.
This is needed before running the game_expansion.py migration.
"""

import os
import sys
import sqlite3
from datetime import datetime

# Add the project directory to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from config import Config

def update_schema():
    """Update the database schema to add new columns to existing tables."""
    print("Starting schema update...")
    
    # Connect to the database
    db_path = Config.DATABASE_PATH
    print(f"Connecting to database at: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get existing columns in user table
        cursor.execute("PRAGMA table_info(user)")
        existing_columns = [col[1] for col in cursor.fetchall()]
        print(f"Existing columns in user table: {existing_columns}")
        
        # Add new columns to user table if they don't exist
        new_columns = [
            ("backup_code", "VARCHAR(16)"),
            ("personal_code", "VARCHAR(10)"),
            ("weekly_e_cap", "INTEGER DEFAULT 9"),
            ("weekly_m_cap", "INTEGER DEFAULT 6"),
            ("weekly_h_cap", "INTEGER DEFAULT 3"),
            ("weekly_e_completed", "INTEGER DEFAULT 0"),
            ("weekly_m_completed", "INTEGER DEFAULT 0"),
            ("weekly_h_completed", "INTEGER DEFAULT 0")
        ]
        
        for col_name, col_type in new_columns:
            if col_name not in existing_columns:
                print(f"Adding column {col_name} to user table")
                cursor.execute(f"ALTER TABLE user ADD COLUMN {col_name} {col_type}")
        
        # Create achievement table if it doesn't exist
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS achievement (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            condition VARCHAR(100) NOT NULL,
            message TEXT NOT NULL,
            points_reward INTEGER DEFAULT 150,
            created_at DATETIME
        )
        """)
        
        # Create user_achievement table if it doesn't exist
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_achievement (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            achievement_id INTEGER NOT NULL,
            achieved_at DATETIME,
            FOREIGN KEY(user_id) REFERENCES user(id),
            FOREIGN KEY(achievement_id) REFERENCES achievement(id),
            UNIQUE(user_id, achievement_id)
        )
        """)
        
        # Create friend_challenge_link table if it doesn't exist
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS friend_challenge_link (
            id INTEGER PRIMARY KEY,
            challenge_id INTEGER NOT NULL,
            user1_id INTEGER NOT NULL,
            user2_id INTEGER NOT NULL,
            user1_confirmed BOOLEAN DEFAULT 0,
            user2_confirmed BOOLEAN DEFAULT 0,
            created_at DATETIME,
            expires_at DATETIME,
            FOREIGN KEY(challenge_id) REFERENCES challenge(id),
            FOREIGN KEY(user1_id) REFERENCES user(id)
        )
        """)
        
        # Create challenge_of_the_week table if it doesn't exist
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS challenge_of_the_week (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            challenge_id INTEGER NOT NULL,
            week_number INTEGER NOT NULL,
            year INTEGER NOT NULL,
            created_at DATETIME,
            last_completed DATE,
            times_completed INTEGER DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES user(id),
            FOREIGN KEY(challenge_id) REFERENCES challenge(id),
            UNIQUE(user_id, week_number, year)
        )
        """)
        
        # Create weekly_leaderboard_reward table if it doesn't exist
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS weekly_leaderboard_reward (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            week_number INTEGER NOT NULL,
            year INTEGER NOT NULL,
            rank INTEGER NOT NULL,
            points_awarded INTEGER NOT NULL,
            awarded_at DATETIME,
            FOREIGN KEY(user_id) REFERENCES user(id),
            UNIQUE(user_id, week_number, year)
        )
        """)
        
        # Commit the changes
        conn.commit()
        print("Schema update completed successfully!")
        
    except Exception as e:
        print(f"Error updating schema: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()
    
    return True

if __name__ == "__main__":
    update_schema()
