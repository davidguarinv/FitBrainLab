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
    # Get all in-progress challenges for the user in the specified week/year
    in_progress = UserChallenge.query.filter_by(
        user_id=user_id,
        status='pending',
        week_number=week_number,
        year=year
    ).all()
    
    # Get the actual Challenge objects
    in_progress_challenges = []
    if in_progress:
        challenge_ids = [c.challenge_id for c in in_progress]
        in_progress_challenges = Challenge.query.filter(Challenge.id.in_(challenge_ids)).all()
    
    return in_progress_challenges, len(in_progress_challenges)
