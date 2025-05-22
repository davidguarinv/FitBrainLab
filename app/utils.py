from datetime import datetime, timedelta
from .models import ChallengeRegeneration
from . import db

# This function is deprecated and has been moved to challenge_timers.py
# Use app.challenge_timers.create_regeneration_timer instead
def create_regeneration_timer(difficulty, slot_number=None):
    """
    DEPRECATED: This function has been moved to challenge_timers.py
    Use app.challenge_timers.create_regeneration_timer instead.
    """
    from app.challenge_timers import create_regeneration_timer as timer_function
    import warnings
    warnings.warn(
        "Using deprecated utils.create_regeneration_timer. "
        "Use app.challenge_timers.create_regeneration_timer instead.",
        DeprecationWarning, stacklevel=2
    )
    return timer_function(difficulty, slot_number)
