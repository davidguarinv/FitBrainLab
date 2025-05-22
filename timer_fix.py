#!/usr/bin/env python3

"""
This script fixes regeneration timers by creating test timers that will be visible immediately.
Run this script directly before starting the app to ensure timers are visible.
"""

import sys
import os

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import Flask app components
from app import create_app, db
from app.models import ChallengeRegeneration
from datetime import datetime, timedelta
from config import Config

# Create app context
app = create_app(Config)

def fix_regeneration_timers():
    """Create visible regeneration timers with short regeneration times for testing"""
    with app.app_context():
        print("\n===== FIXING REGENERATION TIMERS =====\n")
        
        # Clear all existing timers
        ChallengeRegeneration.query.delete()
        db.session.commit()
        print("Cleared all existing regeneration timers.")
        
        # Create new test timers with short regeneration times
        now = datetime.utcnow()
        test_regen_time = now + timedelta(minutes=5)  # 5-minute regeneration for testing
        
        # Create timers for each difficulty and slot
        created_count = 0
        for diff, slots in {'E': 3, 'M': 2, 'H': 1}.items():
            for slot in range(1, slots + 1):
                timer = ChallengeRegeneration(
                    difficulty=diff,
                    slot_number=slot,
                    regenerate_at=test_regen_time
                )
                db.session.add(timer)
                created_count += 1
                print(f"Created timer for {diff} slot {slot}, regenerates at {test_regen_time}")
        
        db.session.commit()
        print(f"\nCreated {created_count} new regeneration timers.")
        print("These timers will be visible on the challenges page.")
        print("They will regenerate in 5 minutes for testing purposes.")
        print("\n======================================\n")
        return created_count

if __name__ == "__main__":
    timer_count = fix_regeneration_timers()
    print(f"Successfully created {timer_count} regeneration timers!")
    print("Now start the application with 'python run.py'")
