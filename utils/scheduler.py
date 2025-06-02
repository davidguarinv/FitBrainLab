import random
import logging
from datetime import datetime, timedelta
from sqlalchemy import func
from app import db
from app.models import Challenge, WeeklyChallengeSet, UserWeeklyOrder, UserChallenge, WeeklyHabitChallenge

logger = logging.getLogger(__name__)

def get_current_week_info():
    """Get the current ISO week number and year."""
    now = datetime.utcnow()
    iso_calendar = now.isocalendar()
    return {
        'week_number': iso_calendar[1],  # ISO week number (1-53)
        'year': iso_calendar[0]  # Year
    }

def get_previous_week_info():
    """Get the previous ISO week number and year."""
    now = datetime.utcnow()
    prev_date = now - timedelta(days=7)
    iso_calendar = prev_date.isocalendar()
    return {
        'week_number': iso_calendar[1],  # ISO week number (1-53)
        'year': iso_calendar[0]  # Year
    }

def populate_weekly_challenge_set():
    """Populate the weekly challenge set for the current week.
    
    This function selects 15 Easy, 10 Medium, and 5 Hard challenges for the current week,
    ensuring they are different from the previous week.
    """
    # Get current week info
    current_week = get_current_week_info()
    week_number = current_week['week_number']
    year = current_week['year']
    
    # Check if we already have challenges for this week
    existing_count = WeeklyChallengeSet.query.filter_by(
        week_number=week_number,
        year=year
    ).count()
    
    if existing_count > 0:
        logger.info(f"Weekly challenge set already exists for week {week_number}, year {year}")
        return
    
    # Get previous week info
    prev_week = get_previous_week_info()
    
    # Get challenges from previous week to exclude
    prev_challenge_ids = db.session.query(WeeklyChallengeSet.challenge_id).filter_by(
        week_number=prev_week['week_number'],
        year=prev_week['year']
    ).all()
    prev_challenge_ids = [c[0] for c in prev_challenge_ids]
    
    # Select challenges for each difficulty
    challenge_counts = {'E': 15, 'M': 10, 'H': 5}
    
    for difficulty, count in challenge_counts.items():
        # Get all challenges of this difficulty that weren't in last week's set
        available_challenges = Challenge.query.filter(
            Challenge.difficulty == difficulty,
            ~Challenge.id.in_(prev_challenge_ids) if prev_challenge_ids else True
        ).all()
        
        # If we don't have enough challenges, include some from previous week
        if len(available_challenges) < count:
            additional_needed = count - len(available_challenges)
            prev_week_challenges = Challenge.query.filter(
                Challenge.difficulty == difficulty,
                Challenge.id.in_(prev_challenge_ids)
            ).all()
            
            # Shuffle and take what we need
            random.shuffle(prev_week_challenges)
            available_challenges.extend(prev_week_challenges[:additional_needed])
        
        # Shuffle and select the required number
        random.shuffle(available_challenges)
        selected_challenges = available_challenges[:count]
        
        # Add to weekly challenge set
        for challenge in selected_challenges:
            weekly_challenge = WeeklyChallengeSet(
                week_number=week_number,
                year=year,
                challenge_id=challenge.id,
                difficulty=difficulty
            )
            db.session.add(weekly_challenge)
    
    # Commit changes
    db.session.commit()
    logger.info(f"Populated weekly challenge set for week {week_number}, year {year}")

def create_user_weekly_order(user_id):
    """
    Create a shuffled order of weekly challenges for a specific user for the current week.
    This is idempotent and will not create duplicates if called multiple times for the same user/week.
    """
    from app.models import WeeklyChallengeSet, UserWeeklyOrder, Challenge
    from app import db
    import random
    logger = logging.getLogger(__name__)

    current_week = get_current_week_info()
    week_number = current_week['week_number']
    year = current_week['year']

    # Check if order already exists for this user/week
    existing = UserWeeklyOrder.query.filter_by(
        user_id=user_id,
        week_number=week_number,
        year=year
    ).first()
    if existing:
        logger.info(f"UserWeeklyOrder already exists for user {user_id}, week {week_number}, year {year}")
        return

    # Get the weekly challenge set for this week
    weekly_challenges = db.session.query(WeeklyChallengeSet, Challenge).join(
        Challenge, WeeklyChallengeSet.challenge_id == Challenge.id
    ).filter(
        WeeklyChallengeSet.week_number == week_number,
        WeeklyChallengeSet.year == year
    ).all()

    # Group challenges by difficulty
    challenges_by_difficulty = {'E': [], 'M': [], 'H': []}
    for wc, challenge in weekly_challenges:
        challenges_by_difficulty[wc.difficulty].append(challenge)

    # Shuffle and create order entries for each difficulty
    for difficulty, challenges in challenges_by_difficulty.items():
        random.shuffle(challenges)
        for i, challenge in enumerate(challenges):
            user_order = UserWeeklyOrder(
                user_id=user_id,
                week_number=week_number,
                year=year,
                challenge_id=challenge.id,
                difficulty=difficulty,
                order_position=i
            )
            db.session.add(user_order)
    db.session.commit()
    logger.info(f"Created weekly challenge order for user {user_id}, week {week_number}, year {year}")

# Initialize scheduler functions
def init_app(app):
    """Initialize scheduler functions with the Flask app."""
    from flask_apscheduler import APScheduler
    
    # First populate the weekly challenge set on startup if needed
    with app.app_context():
        populate_weekly_challenge_set()
    
    # Set up the scheduler for automated weekly population
    scheduler = APScheduler()
    scheduler.init_app(app)
    
    # TODO: Re-enable this feature once implemented
    # Schedule weekly challenge set population - TEMPORARILY DISABLED
    # @scheduler.task('cron', id='populate_weekly_challenges', week='*', day_of_week='mon', hour=0, minute=0)
    # def scheduled_weekly_challenge_population():
    #     with app.app_context():
    #         populate_weekly_challenge_set()
    
    # Create a dummy function to avoid errors
    def scheduled_weekly_challenge_population():
        pass
    
    # Start the scheduler
    scheduler.start()
