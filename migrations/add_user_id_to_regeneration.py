import sys
import os

# Add the parent directory to the path to allow importing app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask
from sqlalchemy import Column, Integer, ForeignKey, text
from app import create_app, db
from app.models import ChallengeRegeneration, User
from datetime import datetime, timezone
from config import Config

def update():
    # Create and configure the app
    app = create_app(Config)
    
    # Use app context
    with app.app_context():
        print("Starting migration to add user_id to challenge_regeneration table...")
        
        # 1. First check if we already have the user_id column
        column_exists = False
        try:
            db.session.execute(text('SELECT user_id FROM challenge_regeneration LIMIT 1'))
            column_exists = True
            print("Column user_id already exists.")
        except Exception as e:
            print(f"Column user_id does not exist yet: {e}")
        
        # 2. If column doesn't exist, create it
        if not column_exists:
            try:
                # Add the column allowing nulls initially
                db.session.execute(text('ALTER TABLE challenge_regeneration ADD COLUMN user_id INTEGER'))
                print("Added user_id column to challenge_regeneration table.")
                
                # Get default user - just use the first user since there's no admin flag
                default_user = User.query.first()
                
                if default_user:
                    # Update all existing records to use this user
                    db.session.execute(text(f"UPDATE challenge_regeneration SET user_id = {default_user.id}"))
                    print(f"Updated all existing records to use user_id {default_user.id}.")
                    
                    # SQLite has limited support for adding constraints after table creation
                    # For SQLite, foreign keys are enforced when tables are created or recreated
                    # We'll rely on the model definition for enforcement
                    print("Note: Foreign key will be enforced through the SQLAlchemy model")

                    
                    # SQLite doesn't support ALTER COLUMN directly, so we'll handle the NOT NULL constraint differently
                    # For SQLite, we would normally recreate the table, but for simplicity we'll keep it as is
                    # since we're already setting all values
                    print("Note: SQLite doesn't support altering column nullability directly. Constraint will be enforced on new records.")
                else:
                    print("Warning: No users found in the database. Can't update existing records.")
            except Exception as e:
                print(f"Error updating challenge_regeneration table: {e}")
                db.session.rollback()
                return
        
        # 3. Commit the changes
        db.session.commit()
        print("Migration completed successfully.")

if __name__ == "__main__":
    update()
