"""
Database migration script for the game expansion features.
This script creates new tables and adds columns to existing tables.
"""

import os
import sys
from datetime import datetime
import secrets
import string

# Add the project directory to the path so we can import the app
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from app import create_app, db
from app.models import User, Achievement

def migrate_database():
    """Apply database migrations for game expansion features."""
    app = create_app()
    
    with app.app_context():
        print("Starting game expansion migrations...")
        
        # Create all tables
        db.create_all()
        
        # Seed achievements
        num_achievements = Achievement.seed_achievements()
        print(f"Added {num_achievements} achievements")
        
        # Generate backup codes and personal codes for existing users
        users = User.query.all()
        updated_count = 0
        
        for user in users:
            # Generate backup code if not present
            if not user.backup_code:
                user.backup_code = secrets.token_hex(8)
                updated_count += 1
                
            # Generate personal code if not present
            if not user.personal_code:
                alphabet = string.ascii_uppercase + string.digits
                user.personal_code = ''.join(secrets.choice(alphabet) for _ in range(8))
                
        db.session.commit()
        print(f"Updated {updated_count} users with backup and personal codes")
        
        print("Migration completed successfully!")

if __name__ == "__main__":
    migrate_database()
