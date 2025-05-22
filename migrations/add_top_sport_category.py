import sys
import os

# Add the parent directory to the path to allow importing app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask
from sqlalchemy import Column, String, text
from app import create_app, db
from app.models import User
from datetime import datetime, timezone
from config import Config

def update():
    # Create and configure the app
    app = create_app(Config)
    
    # Use app context
    with app.app_context():
        # Add the new column if it doesn't exist
        try:
            db.session.execute(text('ALTER TABLE user ADD COLUMN top_sport_category VARCHAR(50)'))
        except Exception as e:
            print(f"Column top_sport_category might already exist: {e}")
            
        # Migrate data from top_sport to top_sport_category if the column exists
        try:
            # Check if top_sport column exists
            db.session.execute(text('SELECT top_sport FROM user LIMIT 1'))
            # If it exists, copy data to the new column
            db.session.execute(text('UPDATE user SET top_sport_category = top_sport'))
            # Drop the old column
            db.session.execute(text('ALTER TABLE user DROP COLUMN top_sport'))
            print("Migrated data from top_sport to top_sport_category")
        except Exception as e:
            print(f"No top_sport column found or error during migration: {e}")
        
        # Add last_sport_update column if it doesn't exist
        try:
            db.session.execute(text('ALTER TABLE user ADD COLUMN last_sport_update TIMESTAMP'))
        except Exception as e:
            print(f"Column last_sport_update might already exist: {e}")
            
        # Set default value for existing users
        current_time = datetime.now(timezone.utc)
        db.session.execute(text(f"UPDATE user SET last_sport_update = '{current_time}' WHERE last_sport_update IS NULL"))
        
        # Commit changes
        db.session.commit()
        
        print("Migration completed successfully")

if __name__ == "__main__":
    update()
