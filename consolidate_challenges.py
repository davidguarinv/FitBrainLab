import os
import sys
from datetime import datetime, timedelta

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the Flask app and models
from app import create_app
from app.models import db, User, Challenge, CompletedChallenge, InProgressChallenge, UserChallenge
from config import Config

# Create the Flask app with the Config
app = create_app(Config)

# Function to migrate old challenge data to the new system
def consolidate_challenge_data():
    with app.app_context():
        print("\n==== Starting Challenge System Consolidation ====")
        
        # First, get all in-progress challenges from the old system
        old_in_progress = InProgressChallenge.query.all()
        print(f"Found {len(old_in_progress)} challenges in progress from the old system")
        
        # For each in-progress challenge, create a corresponding UserChallenge entry
        for old_challenge in old_in_progress:
            # Get the current week info
            from utils.scheduler import get_current_week_info
            current_week = get_current_week_info()
            
            # Check if this challenge already exists in the new system
            existing = UserChallenge.query.filter_by(
                user_id=old_challenge.user_id,
                challenge_id=old_challenge.challenge_id,
                week_number=current_week['week_number'],
                year=current_week['year']
            ).first()
            
            if not existing:
                # Create a new UserChallenge entry
                new_challenge = UserChallenge(
                    user_id=old_challenge.user_id,
                    challenge_id=old_challenge.challenge_id,
                    week_number=current_week['week_number'],
                    year=current_week['year'],
                    status='pending',
                    started_at=old_challenge.started_at
                )
                db.session.add(new_challenge)
                print(f"  - Migrated in-progress challenge {old_challenge.challenge_id} for user {old_challenge.user_id}")
        
        # Next, get all completed challenges from the old system
        old_completed = CompletedChallenge.query.all()
        print(f"Found {len(old_completed)} completed challenges from the old system")
        
        # For each completed challenge, create a corresponding UserChallenge entry if it doesn't exist
        for old_challenge in old_completed:
            # Get the current week info (we'll assume completed challenges are from the current week)
            from utils.scheduler import get_current_week_info
            current_week = get_current_week_info()
            
            # Check if this challenge already exists in the new system
            existing = UserChallenge.query.filter_by(
                user_id=old_challenge.user_id,
                challenge_id=old_challenge.challenge_id,
                week_number=current_week['week_number'],
                year=current_week['year']
            ).first()
            
            if not existing:
                # Create a new UserChallenge entry marked as completed
                new_challenge = UserChallenge(
                    user_id=old_challenge.user_id,
                    challenge_id=old_challenge.challenge_id,
                    week_number=current_week['week_number'],
                    year=current_week['year'],
                    status='completed',
                    started_at=old_challenge.completed_at - timedelta(hours=1),  # Approximate start time
                    completed_at=old_challenge.completed_at,
                    points_earned=old_challenge.points_earned
                )
                db.session.add(new_challenge)
                print(f"  - Migrated completed challenge {old_challenge.challenge_id} for user {old_challenge.user_id}")
            elif existing.status == 'pending':
                # Update the existing challenge to completed status
                existing.status = 'completed'
                existing.completed_at = old_challenge.completed_at
                existing.points_earned = old_challenge.points_earned
                print(f"  - Updated existing challenge {old_challenge.challenge_id} for user {old_challenge.user_id} to completed status")
        
        # Commit all changes
        db.session.commit()
        print("Challenge data consolidation complete!")

# Execute the migration function
if __name__ == '__main__':
    consolidate_challenge_data()
