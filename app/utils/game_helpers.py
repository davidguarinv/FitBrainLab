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
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Query for in-progress challenges for this user in the specified week
        user_challenges = UserChallenge.query.filter_by(
            user_id=user_id,
            week_number=week_number,
            year=year,
            status='pending'
        ).all()
        
        # Get the actual challenge objects
        challenge_ids = [uc.challenge_id for uc in user_challenges]
        challenges = Challenge.query.filter(Challenge.id.in_(challenge_ids)).all()
        
        logger.info(f"Found {len(challenges)} in-progress challenges for user {user_id}")
        return challenges, len(challenges)
    except Exception as e:
        logger.error(f"Error getting in-progress challenges: {str(e)}")
        db.session.rollback()
        return [], 0
    

