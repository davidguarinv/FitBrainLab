from app import create_app, db
from app.models import User, Challenge, CompletedChallenge
from datetime import datetime, timedelta
import random

app = create_app()

def seed_completed_challenges():
    with app.app_context():
        # Get all users and challenges
        users = User.query.all()
        challenges = Challenge.query.all()
        
        if not users or not challenges:
            print("No users or challenges found. Please run seed.py and seed_challenges.py first.")
            return
        
        # Create sample completed challenges
        completed_count = 0
        for i in range(15):  # Create 15 completed challenges
            user = random.choice(users)
            challenge = random.choice(challenges)
            
            # Random completion date within the last 30 days
            completed_at = datetime.now() - timedelta(days=random.randint(0, 30), 
                                                    hours=random.randint(0, 23), 
                                                    minutes=random.randint(0, 59))
            
            # Check if this challenge has already been completed by this user
            existing = CompletedChallenge.query.filter_by(
                user_id=user.id, 
                challenge_id=challenge.id
            ).first()
            
            if not existing:
                completed_challenge = CompletedChallenge(
                    user_id=user.id,
                    challenge_id=challenge.id,
                    completed_at=completed_at
                )
                db.session.add(completed_challenge)
                completed_count += 1
                
                # Points will be calculated from completed challenges
        
        db.session.commit()
        print(f"Added {completed_count} completed challenges")

if __name__ == "__main__":
    seed_completed_challenges()
