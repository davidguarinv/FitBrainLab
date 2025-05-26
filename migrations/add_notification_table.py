import sys
import os

# Add the parent directory to the path so we can import app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import Notification
from config import Config
import sys

def run_migration():
    """Add Notification table for friend challenge bonus point notifications"""
    app = create_app(Config)
    with app.app_context():
        try:
            # Check if the table already exists
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            if 'notification' not in existing_tables:
                # Create the notification table
                db.create_all(tables=[Notification.__table__])
                print("Created notification table")
            else:
                print("Notification table already exists")
            
            print("Migration completed successfully!")
            return True
        except Exception as e:
            print(f"Error during migration: {str(e)}")
            return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
