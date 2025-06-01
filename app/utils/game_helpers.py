from app import db
from app.models import UserChallenge, Challenge

def get_in_progress_challenges(user_id, week_number, year):
    """
    Get all in-progress challenges for a user in the specified week and year.
    
    Args:
        user_id (int): The ID of the user
        week_number (int): The ISO week number
        year (int): The year
        
    Returns:
        tuple: (list of Challenge objects, count of active challenges)
    """
    # TODO: Re-enable this feature once the database schema is updated
    # For now, return empty results to avoid database errors
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"In-progress challenges are temporarily disabled for user {user_id}")
    
    # Return empty list and count
    return [], 0
