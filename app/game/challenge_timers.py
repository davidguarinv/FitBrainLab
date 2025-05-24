from datetime import datetime, timedelta
from .models import ChallengeRegeneration
from . import db

from datetime import datetime, timedelta
from flask import current_app
from . import db
from .models import ChallengeRegeneration

def create_regeneration_timer(difficulty, slot_number=None):
    """
    Create or update a regeneration timer for a challenge of the given difficulty.
    This is the DEFINITIVE version of this function - use this one, not any duplicates.
    
    Args:
        difficulty (str): The difficulty level ('E', 'M', or 'H')
        slot_number (int, optional): The slot number to regenerate. If None, will find an available slot.
    """
    # Log what we're doing
    current_app.logger.info(f'Creating regeneration timer for {difficulty} difficulty')
    
    # If no slot provided, determine the appropriate slot number
    if slot_number is None:
        # Max slots by difficulty: E=3, M=2, H=1
        max_slots = 3 if difficulty == 'E' else (2 if difficulty == 'M' else 1)
        
        # Get existing timers for this difficulty
        existing_timers = ChallengeRegeneration.query.filter_by(difficulty=difficulty).all()
        used_slots = [t.slot_number for t in existing_timers]
        
        # Find the first available slot
        slot_number = None
        for i in range(1, max_slots + 1):
            if i not in used_slots:
                slot_number = i
                break
        
        # If all slots are used, use slot 1
        if slot_number is None:
            slot_number = 1
            
        current_app.logger.info(f'Selected slot {slot_number} for {difficulty} difficulty')
    
    # Get regeneration time
    regen_hours = ChallengeRegeneration.get_regen_hours(difficulty)
    regen_time = datetime.utcnow() + timedelta(hours=regen_hours)
    
    # Check if timer already exists for this slot
    existing_timer = ChallengeRegeneration.query.filter_by(
        difficulty=difficulty, 
        slot_number=slot_number
    ).first()
    
    if existing_timer:
        # Update existing timer
        existing_timer.regenerate_at = regen_time
        current_app.logger.info(f'Updated regeneration timer for {difficulty} slot {slot_number} to {regen_time}')
    else:
        # Create new timer
        new_timer = ChallengeRegeneration(
            difficulty=difficulty,
            slot_number=slot_number,
            regenerate_at=regen_time
        )
        db.session.add(new_timer)
        current_app.logger.info(f'Created new regeneration timer for {difficulty} slot {slot_number} to {regen_time}')
    
    # Commit changes
    db.session.commit()
    return regen_time
    
# Alias for backward compatibility
set_regeneration_timer = create_regeneration_timer
