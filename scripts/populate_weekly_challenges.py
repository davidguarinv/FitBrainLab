#!/usr/bin/env python
"""
Script to populate weekly challenge sets for the current week.
This script manually runs the populate_weekly_challenge_set function
to ensure challenges are available for the current week.
"""

import os
import sys

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from utils.scheduler import populate_weekly_challenge_set, get_current_week_info
from app.models import Challenge, WeeklyChallengeSet

# Create the Flask app with the development configuration
app = create_app()

def main():
    """Main function to populate weekly challenges."""
    with app.app_context():
        # First, let's check if there are any challenges in the database
        challenge_count = Challenge.query.count()
        print(f"Found {challenge_count} challenges in the database")
        
        if challenge_count == 0:
            print("ERROR: No challenges in database. Run seed_supabase_challenges.sql first.")
            return False
            
        # Get current week info
        current_week = get_current_week_info()
        week_number = current_week['week_number']
        year = current_week['year']
        print(f"Current week: {week_number}, year: {year}")
        
        # Check if we already have weekly challenges
        existing_count = WeeklyChallengeSet.query.filter_by(
            week_number=week_number,
            year=year
        ).count()
        
        print(f"Found {existing_count} existing weekly challenges for current week")
        
        if existing_count > 0:
            # If we have existing challenges, let's check if they're valid
            print("Checking if existing weekly challenges are valid...")
            
            weekly_challenges = WeeklyChallengeSet.query.filter_by(
                week_number=week_number,
                year=year
            ).all()
            
            # Check if challenge IDs exist in the Challenge table
            valid_count = 0
            invalid_ids = []
            
            for wc in weekly_challenges:
                challenge = Challenge.query.get(wc.challenge_id)
                if challenge:
                    valid_count += 1
                    print(f"✅ Challenge {wc.challenge_id} ({wc.difficulty}) exists: {challenge.title[:30]}")
                else:
                    invalid_ids.append(wc.challenge_id)
                    print(f"❌ Challenge {wc.challenge_id} ({wc.difficulty}) does NOT exist")
            
            print(f"Valid challenges: {valid_count}/{len(weekly_challenges)}")
            
            if invalid_ids:
                print(f"Invalid challenge IDs: {invalid_ids}")
                print("Deleting invalid weekly challenge entries...")
                
                for invalid_id in invalid_ids:
                    WeeklyChallengeSet.query.filter_by(challenge_id=invalid_id).delete()
                
                db.session.commit()
                print("Invalid entries deleted")
            
            if valid_count < 5:  # If we have too few valid challenges
                print("Too few valid challenges, repopulating...")
                # Delete existing and repopulate
                WeeklyChallengeSet.query.filter_by(
                    week_number=week_number,
                    year=year
                ).delete()
                db.session.commit()
                populate_weekly_challenge_set()
                print("Weekly challenges repopulated")
            else:
                print("Enough valid challenges exist, no need to repopulate")
        else:
            # If no weekly challenges exist, populate them
            print("No weekly challenges found for current week, populating...")
            populate_weekly_challenge_set()
            print("Weekly challenges populated")
        
        # Verify the result
        final_count = WeeklyChallengeSet.query.filter_by(
            week_number=week_number,
            year=year
        ).count()
        
        print(f"Final count: {final_count} weekly challenges for current week")
        return True

if __name__ == "__main__":
    main()
