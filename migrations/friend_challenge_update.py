import sys
import os

# Add the parent directory to the path so we can import app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import FriendChallengeLink
from config import Config
from sqlalchemy import Column, Boolean, DateTime
import sys

def run_migration():
    """Add new fields to FriendChallengeLink table for enhanced friend challenge functionality"""
    app = create_app(Config)
    with app.app_context():
        try:
            # Check if columns already exist to avoid errors
            inspector = db.inspect(db.engine)
            existing_columns = [c['name'] for c in inspector.get_columns('friend_challenge_link')]
            
            # Add new columns if they don't exist
            with db.engine.begin() as conn:
                if 'user1_completed' not in existing_columns:
                    conn.execute(db.text("ALTER TABLE friend_challenge_link ADD COLUMN user1_completed BOOLEAN DEFAULT FALSE"))
                    print("Added user1_completed column")
                
                if 'user2_completed' not in existing_columns:
                    conn.execute(db.text("ALTER TABLE friend_challenge_link ADD COLUMN user2_completed BOOLEAN DEFAULT FALSE"))
                    print("Added user2_completed column")
                
                if 'user1_completed_at' not in existing_columns:
                    conn.execute(db.text("ALTER TABLE friend_challenge_link ADD COLUMN user1_completed_at DATETIME"))
                    print("Added user1_completed_at column")
                
                if 'user2_completed_at' not in existing_columns:
                    conn.execute(db.text("ALTER TABLE friend_challenge_link ADD COLUMN user2_completed_at DATETIME"))
                    print("Added user2_completed_at column")
                
                if 'completion_expires_at' not in existing_columns:
                    conn.execute(db.text("ALTER TABLE friend_challenge_link ADD COLUMN completion_expires_at DATETIME"))
                    print("Added completion_expires_at column")
                
                if 'expired' not in existing_columns:
                    conn.execute(db.text("ALTER TABLE friend_challenge_link ADD COLUMN expired BOOLEAN DEFAULT FALSE"))
                    print("Added expired column")
            
            print("Migration completed successfully!")
            return True
        except Exception as e:
            print(f"Error during migration: {str(e)}")
            return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
