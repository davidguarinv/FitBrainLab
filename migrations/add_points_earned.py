import sys
import os

# Add the parent directory to the path so we can import the app module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import CompletedChallenge
from sqlalchemy import Column, Integer

app = create_app()

def add_points_earned_column():
    with app.app_context():
        # Connect to the database
        conn = db.engine.connect()
        
        # Check if the column already exists
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('completed_challenge')]
        
        if 'points_earned' not in columns:
            print("Adding points_earned column to completed_challenge table...")
            conn.execute(db.text("ALTER TABLE completed_challenge ADD COLUMN points_earned INTEGER"))
            print("Column added successfully!")
        else:
            print("points_earned column already exists.")
        
        conn.close()

if __name__ == '__main__':
    add_points_earned_column()
