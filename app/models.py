from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import random
from . import db

# -------------------------
# User Model
# -------------------------
class User(UserMixin, db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)  # Primary key
    username = db.Column(db.String(64), unique=True, nullable=False)  # Unique username
    password_hash = db.Column(db.String(128))  # Hashed password
    is_public = db.Column(db.Boolean, default=True)  # Whether user profile is public
    top_sport = db.Column(db.String(50))  # Optional: most-played sport
    last_sport_update = db.Column(db.DateTime)  # Last update timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Creation timestamp
    daily_streak = db.Column(db.Integer, default=0)  # Daily streak counter
    last_challenge_date = db.Column(db.Date)  # Last challenge date
    daily_e_count = db.Column(db.Integer, default=0)  # Daily easy challenge count
    daily_m_count = db.Column(db.Integer, default=0)  # Daily medium challenge count
    daily_h_count = db.Column(db.Integer, default=0)  # Daily hard challenge count
    last_week_visited = db.Column(db.Integer)  # Last ISO week number visited
    last_year_visited = db.Column(db.Integer)  # Last year visited

    # Relationships
    completed_challenges = db.relationship('CompletedChallenge', backref='user', lazy='dynamic')
    in_progress_challenges = db.relationship('InProgressChallenge', backref='user', lazy='dynamic')

    def set_password(self, password):
        """Hash and store password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check hashed password."""
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def generate_username():
        """Generate a fun random username."""
        adjectives = ['Happy', 'Quick', 'Clever', 'Brave', 'Calm', 'Bright', 'Swift', 'Wild', 'Wise']
        nouns = ['Runner', 'Tiger', 'Eagle', 'Lion', 'Wolf', 'Bear', 'Hawk', 'Fox', 'Deer']
        return f"{random.choice(adjectives)}{random.choice(nouns)}{random.randint(1,999)}"

    def reset_daily_counts(self):
        """Reset daily challenge counts if it's a new day."""
        today = datetime.utcnow().date()
        if self.last_challenge_date != today:
            self.daily_e_count = 0
            self.daily_m_count = 0
            self.daily_h_count = 0
            self.last_challenge_date = today
            db.session.commit()

    def can_take_challenge(self, difficulty):
        """Check if user can take a challenge of given difficulty."""
        self.reset_daily_counts()
        if difficulty == 'E' and self.daily_e_count >= 3:
            return False
        if difficulty == 'M' and self.daily_m_count >= 2:
            return False
        if difficulty == 'H' and self.daily_h_count >= 1:
            return False
        return True

    @property
    def points(self):
        """Calculate total points from completed challenges."""
        from sqlalchemy import func
        from app import db
        # Use SQL sum to calculate total points - more efficient than Python sum
        total = db.session.query(func.sum(CompletedChallenge.points_earned)).filter(
            CompletedChallenge.user_id == self.id
        ).scalar()
        
        # Add bonus points from weekly habit challenges
        habit_points = db.session.query(func.sum(WeeklyHabitChallenge.bonus_points_earned)).filter(
            WeeklyHabitChallenge.user_id == self.id
        ).scalar()
        
        return (total or 0) + (habit_points or 0)
    
    def get_current_week_info(self):
        """Get the current ISO week number and year."""
        from datetime import datetime
        now = datetime.utcnow()
        iso_calendar = now.isocalendar()
        return {
            'week_number': iso_calendar[1],  # ISO week number (1-53)
            'year': iso_calendar[0]  # Year
        }
    
    def is_first_visit_of_week(self):
        """Check if this is the user's first visit in the current ISO week."""
        week_info = self.get_current_week_info()
        return (self.last_week_visited != week_info['week_number'] or 
                self.last_year_visited != week_info['year'])
    
    def update_last_visit_week(self):
        """Update the last visited week and year."""
        week_info = self.get_current_week_info()
        self.last_week_visited = week_info['week_number']
        self.last_year_visited = week_info['year']
        db.session.commit()
    
    def get_weekly_challenge_counts(self):
        """Get the count of completed challenges for the current week by difficulty."""
        from sqlalchemy import func
        from app import db
        week_info = self.get_current_week_info()
        
        # Query for completed challenges this week
        counts = {}
        for difficulty in ['E', 'M', 'H']:
            count = db.session.query(func.count(UserChallenge.id)).filter(
                UserChallenge.user_id == self.id,
                UserChallenge.week_number == week_info['week_number'],
                UserChallenge.year == week_info['year'],
                UserChallenge.status == 'completed',
                UserChallenge.challenge.has(Challenge.difficulty == difficulty)
            ).scalar() or 0
            counts[difficulty] = count
        
        return counts
    
    def can_take_weekly_challenge(self, difficulty):
        """
        Check if user can take a challenge of given difficulty based on weekly caps.
        This takes into account both completed challenges and in-progress challenges.
        """
        from utils.scheduler import get_current_week_info
        
        # Get current week info
        current_week = get_current_week_info()
        
        # Get counts of completed challenges for this week
        completed_counts = self.get_weekly_challenge_counts()
        
        # Count in-progress challenges by difficulty
        in_progress_counts = {'E': 0, 'M': 0, 'H': 0}
        
        # Get all in-progress challenges for this user in the current week
        in_progress = UserChallenge.query.filter_by(
            user_id=self.id,
            week_number=current_week['week_number'],
            year=current_week['year'],
            status='pending'
        ).all()
        
        # Count them by difficulty
        for challenge in in_progress:
            ch = Challenge.query.get(challenge.challenge_id)
            if ch:
                in_progress_counts[ch.difficulty] += 1
        
        # Calculate total count (completed + in-progress)
        total_counts = {
            'E': completed_counts['E'] + in_progress_counts['E'],
            'M': completed_counts['M'] + in_progress_counts['M'],
            'H': completed_counts['H'] + in_progress_counts['H']
        }
        
        # Weekly caps: 9 Easy, 6 Medium, 3 Hard
        if difficulty == 'E' and total_counts['E'] >= 9:
            return False
        if difficulty == 'M' and total_counts['M'] >= 6:
            return False
        if difficulty == 'H' and total_counts['H'] >= 3:
            return False
        return True
    
    def get_weekly_habit_challenge(self):
        """Get the user's weekly habit challenge for the current week."""
        week_info = self.get_current_week_info()
        return WeeklyHabitChallenge.query.filter_by(
            user_id=self.id,
            week_number=week_info['week_number'],
            year=week_info['year']
        ).first()
    
    def get_previous_week_completed_challenges(self):
        """Get the challenges completed in the previous week."""
        from datetime import datetime, timedelta
        from app import db
        
        # Calculate previous week
        current_week_info = self.get_current_week_info()
        current_date = datetime.utcnow()
        prev_date = current_date - timedelta(days=7)
        prev_iso = prev_date.isocalendar()
        prev_week = prev_iso[1]
        prev_year = prev_iso[0]
        
        # Query for completed challenges from previous week
        completed_challenges = db.session.query(UserChallenge, Challenge).join(
            Challenge, Challenge.id == UserChallenge.challenge_id
        ).filter(
            UserChallenge.user_id == self.id,
            UserChallenge.week_number == prev_week,
            UserChallenge.year == prev_year,
            UserChallenge.status == 'completed',
            Challenge.difficulty.in_(['E', 'M'])  # Only Easy and Medium challenges can be habit challenges
        ).all()
        
        return completed_challenges


# -------------------------
# Challenge Model
# -------------------------
class Challenge(db.Model):
    __tablename__ = 'challenge'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    difficulty = db.Column(db.String(1), nullable=False)  # 'E', 'M', 'H'
    points = db.Column(db.Integer, nullable=False)
    regen_hours = db.Column(db.Integer, default=6)  # Hours before challenge ates
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    completed_by = db.relationship('CompletedChallenge', backref='challenge', lazy='dynamic')
    in_progress_by = db.relationship('InProgressChallenge', backref='challenge', lazy='dynamic')


# -------------------------
# Completed Challenge Model
# -------------------------
class CompletedChallenge(db.Model):
    __tablename__ = 'completed_challenge'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    points_earned = db.Column(db.Integer, nullable=True)  # Store points earned when completing the challenge


# -------------------------
# In Progress Challenge Model
# -------------------------
class InProgressChallenge(db.Model):
    __tablename__ = 'in_progress_challenge'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)


# -------------------------
# Challenge Regeneration Model
# -------------------------
class ChallengeRegeneration(db.Model):
    __tablename__ = 'challenge_regeneration'

    id = db.Column(db.Integer, primary_key=True)
    difficulty = db.Column(db.String(1), nullable=False)  # 'E', 'M', 'H'
    regenerate_at = db.Column(db.DateTime, nullable=False)
    slot_number = db.Column(db.Integer, nullable=False)  # Which slot (1-3 for easy, 1-2 for medium, 1 for hard)
    
    @staticmethod
    def get_regen_hours(difficulty):
        """Get the regeneration time in hours based on difficulty."""
        if difficulty == 'E':
            return 6  # Easy challenges regenerate in 6 hours
        elif difficulty == 'M':
            return 8  # Medium challenges regenerate in 8 hours
        elif difficulty == 'H':
            return 10  # Hard challenges regenerate in 10 hours
        return 6  # Default to 6 hours


class WeeklyChallengeSet(db.Model):
    __tablename__ = 'weekly_challenge_set'

    id = db.Column(db.Integer, primary_key=True)
    week_number = db.Column(db.Integer, nullable=False)  # ISO week number (1-53)
    year = db.Column(db.Integer, nullable=False)  # Year for the week
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=False)
    difficulty = db.Column(db.String(1), nullable=False)  # 'E', 'M', 'H'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to Challenge
    challenge = db.relationship('Challenge', backref='weekly_sets')
    
    # Composite unique constraint to ensure a challenge is only in the set once per week
    __table_args__ = (db.UniqueConstraint('week_number', 'year', 'challenge_id', name='_week_challenge_uc'),)


class UserWeeklyOrder(db.Model):
    __tablename__ = 'user_weekly_order'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    week_number = db.Column(db.Integer, nullable=False)  # ISO week number (1-53)
    year = db.Column(db.Integer, nullable=False)  # Year for the week
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=False)
    difficulty = db.Column(db.String(1), nullable=False)  # 'E', 'M', 'H'
    order_position = db.Column(db.Integer, nullable=False)  # Position in the user's ordered list
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='weekly_orders')
    challenge = db.relationship('Challenge', backref='user_orders')
    
    # Composite unique constraint
    __table_args__ = (
        db.UniqueConstraint('user_id', 'week_number', 'year', 'challenge_id', name='_user_week_challenge_uc'),
        db.UniqueConstraint('user_id', 'week_number', 'year', 'difficulty', 'order_position', name='_user_week_diff_pos_uc'),
    )


class UserChallenge(db.Model):
    __tablename__ = 'user_challenge'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=False)
    week_number = db.Column(db.Integer, nullable=False)  # ISO week number (1-53)
    year = db.Column(db.Integer, nullable=False)  # Year for the week
    status = db.Column(db.String(10), nullable=False)  # 'pending', 'completed', 'abandoned'
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    points_earned = db.Column(db.Integer, nullable=True)
    
    # Relationships
    user = db.relationship('User', backref='user_challenges')
    challenge = db.relationship('Challenge', backref='user_attempts')
    
    # Composite unique constraint to ensure a user can only have one active attempt per challenge per week
    __table_args__ = (db.UniqueConstraint('user_id', 'challenge_id', 'week_number', 'year', name='_user_challenge_week_uc'),)


class WeeklyHabitChallenge(db.Model):
    __tablename__ = 'weekly_habit_challenge'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=False)
    week_number = db.Column(db.Integer, nullable=False)  # ISO week number (1-53)
    year = db.Column(db.Integer, nullable=False)  # Year for the week
    days_completed = db.Column(db.Integer, default=0)  # Number of days completed this week (0-7)
    bonus_points_earned = db.Column(db.Integer, default=0)  # Bonus points earned for habit completion
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='habit_challenges')
    challenge = db.relationship('Challenge', backref='habit_selections')
    
    # Composite unique constraint to ensure a user can only have one habit challenge per week
    __table_args__ = (db.UniqueConstraint('user_id', 'week_number', 'year', name='_user_habit_week_uc'),)
