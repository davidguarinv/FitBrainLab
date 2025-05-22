from app import db
from app.models import ChallengeRegeneration
from datetime import datetime, timedelta

def ensure_visible_regeneration_timers():
    """Create visible regeneration timers with 1-minute regeneration for immediate testing"""
    now = datetime.utcnow()
    test_time = now + timedelta(minutes=1)
    
    # Clear existing timers
    ChallengeRegeneration.query.delete()
    db.session.commit()
    
    # Create test timers that will be visible immediately
    for diff, slots in {'E': 3, 'M': 2, 'H': 1}.items():
        for slot in range(1, slots + 1):
            timer = ChallengeRegeneration(
                difficulty=diff,
                slot_number=slot,
                regenerate_at=test_time
            )
            db.session.add(timer)
    
    db.session.commit()
    return "Regeneration timers created successfully!"
