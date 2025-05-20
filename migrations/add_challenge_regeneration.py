import sys
import os
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import the app module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import ChallengeRegeneration

app = create_app()

def create_challenge_regeneration_table():
    with app.app_context():
        # Check if the table already exists
        inspector = db.inspect(db.engine)
        if 'challenge_regeneration' not in inspector.get_table_names():
            print("Creating challenge_regeneration table...")
            # Create the table
            db.create_all()
            print("Table created successfully!")
            
            # Initialize with default regeneration times
            now = datetime.utcnow()
            
            # Add slots for easy challenges (3 slots)
            for i in range(1, 4):
                regen = ChallengeRegeneration(difficulty='E', slot_number=i, regenerate_at=now)
                db.session.add(regen)
            
            # Add slots for medium challenges (2 slots)
            for i in range(1, 3):
                regen = ChallengeRegeneration(difficulty='M', slot_number=i, regenerate_at=now)
                db.session.add(regen)
            
            # Add slot for hard challenge (1 slot)
            regen = ChallengeRegeneration(difficulty='H', slot_number=1, regenerate_at=now)
            db.session.add(regen)
            
            db.session.commit()
            print("Initialized regeneration slots!")
        else:
            print("challenge_regeneration table already exists.")

if __name__ == '__main__':
    create_challenge_regeneration_table()
