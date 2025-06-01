#!/usr/bin/env python
"""
Script to diagnose and repair database issues.
This script checks challenge data and weekly challenge sets,
fixing any inconsistencies found.
"""

import os
import sys
from datetime import datetime

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from utils.scheduler import get_current_week_info
from app.models import Challenge, WeeklyChallengeSet

# Create the Flask app with the development configuration
app = create_app()

def diagnose_db():
    """Diagnose database health."""
    print("===== DATABASE DIAGNOSIS =====")
    
    # Check Challenge table
    challenge_count = Challenge.query.count()
    print(f"Challenge table: {challenge_count} records")
    
    # Check if we have challenges of each difficulty
    difficulties = db.session.query(Challenge.difficulty, db.func.count(Challenge.id)).group_by(Challenge.difficulty).all()
    difficulty_map = {diff: count for diff, count in difficulties}
    print(f"Challenge difficulties: {difficulty_map}")
    
    # Check WeeklyChallengeSet table
    current_week = get_current_week_info()
    week_number = current_week['week_number']
    year = current_week['year']
    
    weekly_set_count = WeeklyChallengeSet.query.count()
    current_week_count = WeeklyChallengeSet.query.filter_by(
        week_number=week_number, 
        year=year
    ).count()
    
    print(f"WeeklyChallengeSet total: {weekly_set_count} records")
    print(f"Current week ({week_number}/{year}) challenges: {current_week_count} records")
    
    # Check if weekly challenge IDs exist in challenges table
    print("\nChecking weekly challenge references...")
    weekly_challenges = WeeklyChallengeSet.query.all()
    
    valid_count = 0
    invalid_count = 0
    
    for wc in weekly_challenges:
        challenge = Challenge.query.get(wc.challenge_id)
        if challenge:
            valid_count += 1
        else:
            invalid_count += 1
            print(f"Invalid reference: WeeklyChallengeSet id={wc.id}, challenge_id={wc.challenge_id}")
    
    print(f"Valid references: {valid_count}")
    print(f"Invalid references: {invalid_count}")
    
    return {
        'challenge_count': challenge_count,
        'weekly_set_count': weekly_set_count,
        'current_week_count': current_week_count,
        'valid_refs': valid_count,
        'invalid_refs': invalid_count,
        'needs_repair': challenge_count == 0 or invalid_count > 0 or current_week_count == 0,
    }

def delete_and_reseed_challenges():
    """Delete and reseed challenges."""
    print("\n===== REPAIRING DATABASE =====")
    
    # First, delete any invalid weekly challenge references
    invalid_weekly = []
    
    weekly_challenges = WeeklyChallengeSet.query.all()
    for wc in weekly_challenges:
        if not Challenge.query.get(wc.challenge_id):
            invalid_weekly.append(wc.id)
    
    if invalid_weekly:
        print(f"Deleting {len(invalid_weekly)} invalid weekly challenge references...")
        for wc_id in invalid_weekly:
            wc = WeeklyChallengeSet.query.get(wc_id)
            db.session.delete(wc)
        db.session.commit()
    
    # Check if we have challenges
    challenge_count = Challenge.query.count()
    
    if challenge_count == 0:
        print("No challenges found, running seed script...")
        
        try:
            # Read and execute the seed script directly
            with open('scripts/seed_supabase_challenges.sql', 'r') as file:
                sql = file.read()
                
                # Split the script into individual statements
                statements = sql.split(';')
                
                for statement in statements:
                    if statement.strip():
                        try:
                            db.session.execute(statement)
                            db.session.commit()
                        except Exception as e:
                            db.session.rollback()
                            print(f"Error executing statement: {e}")
            
            print("Seed script executed successfully")
        except Exception as e:
            print(f"Error running seed script: {e}")
            return False
    
    # Now populate weekly challenges for current week
    current_week = get_current_week_info()
    week_number = current_week['week_number']
    year = current_week['year']
    
    # Check if current week has challenges
    current_week_count = WeeklyChallengeSet.query.filter_by(
        week_number=week_number,
        year=year
    ).count()
    
    if current_week_count < 15:  # We should have at least 15 challenges
        print(f"Only {current_week_count} challenges found for current week, adding more...")
        
        # Delete existing weekly challenges for current week
        WeeklyChallengeSet.query.filter_by(
            week_number=week_number,
            year=year
        ).delete()
        db.session.commit()
        
        # Add weekly challenges manually
        difficulties = {'E': 15, 'M': 10, 'H': 5}
        added = 0
        
        for diff, count in difficulties.items():
            # Get challenges of this difficulty
            challenges = Challenge.query.filter_by(difficulty=diff).all()
            
            if len(challenges) < count:
                print(f"Not enough challenges of difficulty {diff}. Have {len(challenges)}, need {count}")
                count = len(challenges)  # Use what we have
            
            # Randomly select challenges
            import random
            selected = random.sample(challenges, count)
            
            for challenge in selected:
                weekly_challenge = WeeklyChallengeSet(
                    week_number=week_number,
                    year=year,
                    challenge_id=challenge.id,
                    difficulty=diff
                )
                db.session.add(weekly_challenge)
                added += 1
        
        db.session.commit()
        print(f"Added {added} weekly challenges for current week")
    
    return True

def main():
    """Main repair function."""
    with app.app_context():
        # Diagnose database health
        diagnosis = diagnose_db()
        
        if diagnosis['needs_repair']:
            print("\nDatabase needs repair. Proceeding with repairs...")
            if delete_and_reseed_challenges():
                print("\n===== REPAIR COMPLETE =====")
                # Run diagnosis again to confirm fix
                after_diagnosis = diagnose_db()
                
                if after_diagnosis['needs_repair']:
                    print("ERROR: Database still needs repair after attempted fix.")
                    return False
                else:
                    print("Database successfully repaired!")
                    return True
            else:
                print("ERROR: Failed to repair database.")
                return False
        else:
            print("\nDatabase appears healthy, no repairs needed.")
            return True

if __name__ == "__main__":
    main()
