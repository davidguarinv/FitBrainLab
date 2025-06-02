"""
Migration script to add week_number and year columns to the user_challenge table.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import db
from run import app
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Add week_number and year columns to user_challenge table if they don't exist."""
    with app.app_context():
        logger.info("Starting migration to add week columns to user_challenge table")
        
        # Check if columns already exist
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('user_challenge')]
        
        if 'week_number' not in columns:
            logger.info("Adding week_number column to user_challenge table")
            db.session.execute(text('ALTER TABLE user_challenge ADD COLUMN week_number INTEGER DEFAULT 1'))
            db.session.commit()
        else:
            logger.info("week_number column already exists")
            
        if 'year' not in columns:
            logger.info("Adding year column to user_challenge table")
            db.session.execute(text('ALTER TABLE user_challenge ADD COLUMN year INTEGER DEFAULT 2025'))
            db.session.commit()
        else:
            logger.info("year column already exists")
            
        if 'status' not in columns:
            logger.info("Adding status column to user_challenge table")
            db.session.execute(text("ALTER TABLE user_challenge ADD COLUMN status VARCHAR(10) DEFAULT 'pending'"))
            db.session.commit()
        else:
            logger.info("status column already exists")
            
        logger.info("Migration completed successfully")

if __name__ == "__main__":
    run_migration()
