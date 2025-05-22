from datetime import datetime, timedelta
from app import create_app, db
from app.models import ChallengeRegeneration
from config import Config

def init_all_regeneration_timers():
    """Initialize all regeneration timers with proper times"""
    # Clear any existing timers
    ChallengeRegeneration.query.delete()
    db.session.commit()
    
    # Create one timer for each difficulty and slot
    now = datetime.utcnow()
    difficulties = {
        'E': {'slots': 3, 'hours': 6},
        'M': {'slots': 2, 'hours': 8},
        'H': {'slots': 1, 'hours': 10}
    }
    
    for diff, config in difficulties.items():
        for slot in range(1, config['slots'] + 1):
            # Set regeneration time to current time + 1 minute (for testing)
            # In production use: now + timedelta(hours=config['hours'])
            regen_time = now + timedelta(minutes=1)  # For testing
            
            # Create timer
            timer = ChallengeRegeneration(
                difficulty=diff,
                slot_number=slot,
                regenerate_at=regen_time
            )
            db.session.add(timer)
            print(f"Created timer for {diff} slot {slot}, regenerates in 1 minute")
    
    db.session.commit()
    print("All regeneration timers initialized successfully!")

# Run this function when imported
init_all_regeneration_timers()
