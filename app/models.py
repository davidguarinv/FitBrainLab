from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import random
import json
import os
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
    top_sport_category = db.Column(db.String(50))  # Optional: sport category
    last_sport_update = db.Column(db.DateTime)  # Last update timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Creation timestamp
    last_challenge_date = db.Column(db.Date)  # Last challenge date
    daily_e_count = db.Column(db.Integer, default=0)  # Daily easy challenge count
    daily_m_count = db.Column(db.Integer, default=0)  # Daily medium challenge count
    daily_h_count = db.Column(db.Integer, default=0)  # Daily hard challenge count
    last_week_visited = db.Column(db.Integer)  # Last ISO week number visited
    last_year_visited = db.Column(db.Integer)  # Last year visited
    
    # New fields for password recovery and friend challenges
    backup_code = db.Column(db.String(16), unique=True)  # Backup code for password recovery
    personal_code = db.Column(db.String(10), unique=True)  # Personal code for friend challenges
    
    # Weekly challenge caps
    weekly_e_cap = db.Column(db.Integer, default=9)  # Weekly easy challenge cap
    weekly_m_cap = db.Column(db.Integer, default=6)  # Weekly medium challenge cap
    weekly_h_cap = db.Column(db.Integer, default=3)  # Weekly hard challenge cap
    weekly_e_completed = db.Column(db.Integer, default=0)  # Weekly easy challenges completed
    weekly_m_completed = db.Column(db.Integer, default=0)  # Weekly medium challenges completed
    weekly_h_completed = db.Column(db.Integer, default=0)  # Weekly hard challenges completed

    # Relationships
    completed_challenges = db.relationship('CompletedChallenge', backref='user', lazy='dynamic')

    def set_password(self, password):
        """Hash and store password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check hashed password."""
        return check_password_hash(self.password_hash, password)
        
    def generate_backup_code(self):
        """Generate a unique backup code for password recovery."""
        import secrets
        while True:
            code = secrets.token_hex(8)  # 16 character hex string
            if not User.query.filter_by(backup_code=code).first():
                self.backup_code = code
                return code
                
    def generate_personal_code(self):
        """Generate a unique personal code for friend challenges."""
        import string
        import secrets
        alphabet = string.ascii_uppercase + string.digits
        while True:
            code = ''.join(secrets.choice(alphabet) for _ in range(8))
            if not User.query.filter_by(personal_code=code).first():
                self.personal_code = code
                return code

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
        if difficulty == 'E' and self.daily_e_count >= 4:
            return False
        if difficulty == 'M' and self.daily_m_count >= 3:
            return False
        if difficulty == 'H' and self.daily_h_count >= 2:
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
    regen_hours = db.Column(db.Integer, default=6)  # Hours before challenge regenerates
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    completed_by = db.relationship('CompletedChallenge', backref='challenge', lazy='dynamic')


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
# Challenge Regeneration Model
# -------------------------
class ChallengeRegeneration(db.Model):
    __tablename__ = 'challenge_regeneration'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Add user_id as foreign key
    difficulty = db.Column(db.String(1), nullable=False)  # 'E', 'M', 'H'
    regenerate_at = db.Column(db.DateTime, nullable=False)
    slot_number = db.Column(db.Integer, nullable=False)  # Which slot (1-3 for easy, 1-2 for medium, 1 for hard)
    
    # Relationship with User model
    user = db.relationship('User', backref=db.backref('regeneration_timers', lazy='dynamic'))
    
    @staticmethod
    def get_regen_hours(difficulty):
        """Get the regeneration time in hours based on difficulty."""
        if difficulty == 'E':
            return 4  # Easy challenges regenerate in 4 hours
        elif difficulty == 'M':
            return 6  # Medium challenges regenerate in 6 hours
        elif difficulty == 'H':
            return 8  # Hard challenges regenerate in 8 hours
        return 4  # Default to 4 hours


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
    challenge = db.relationship('Challenge', backref='challenge_attempts')
    
    # Composite unique constraint to ensure a user can only have one active attempt per challenge per week
    __table_args__ = (db.UniqueConstraint('user_id', 'challenge_id', 'week_number', 'year', name='_user_challenge_week_uc'),)


class WeeklyHabitChallenge(db.Model):
    __tablename__ = 'weekly_habit_challenge'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=False)
    week_number = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    days_completed = db.Column(db.Integer, default=0)
    bonus_points_earned = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='habit_challenges')
    challenge = db.relationship('Challenge', backref='habit_selections')
    __table_args__ = (db.UniqueConstraint('user_id', 'week_number', 'year', name='_user_habit_week_uc'),)


# -------------------------
# Achievement Model
# -------------------------
class Achievement(db.Model):
    __tablename__ = 'achievement'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    condition = db.Column(db.String(50), nullable=False)  # e.g. '5_easy', '3_weekly_streak'
    message = db.Column(db.String(200), nullable=False)
    points_reward = db.Column(db.Integer, nullable=False)
    icon_type = db.Column(db.String(50), nullable=True)  # e.g. 'first_challenge', 'weekly_streak'
    
    # Relationship with UserAchievement
    user_achievements = db.relationship('UserAchievement', backref='achievement', lazy='dynamic')
    
    ACHIEVEMENTS = [
        {
            'name': 'First Challenge!',
            'condition': '1_total',
            'message': 'Complete your first challenge.',
            'points_reward': 50,
            'icon_type': 'first_challenge'
        },
        {
            'name': 'Getting Started',
            'condition': '10_total',
            'message': 'Complete 10 challenges of any difficulty.',
            'points_reward': 100,
            'icon_type': 'getting_started'
        },
        {
            'name': 'Challenge Enthusiast',
            'condition': '50_total',
            'message': 'Complete 50 challenges of any difficulty.',
            'points_reward': 200,
            'icon_type': 'challenge_enthusiast'
        },
        {
            'name': 'Weekly Streak',
            'condition': '3_weekly_streak',
            'message': 'Complete challenges for 3 weeks in a row.',
            'points_reward': 150,
            'icon_type': 'weekly_streak'
        },
        {
            'name': 'Easy Beginner',
            'condition': '10_easy',
            'message': 'Complete 10 easy challenges.',
            'points_reward': 75,
            'icon_type': 'easy_beginner'
        },
        {
            'name': 'Medium Beginner',
            'condition': '10_medium',
            'message': 'Complete 10 medium challenges.',
            'points_reward': 100,
            'icon_type': 'medium_beginner'
        },
        {
            'name': 'Hard Beginner',
            'condition': '10_hard',
            'message': 'Complete 10 hard challenges.',
            'points_reward': 150,
            'icon_type': 'hard_beginner'
        }
    ]
    
    @staticmethod
    def seed_achievements():
        """Seed the default achievements into the database."""
        for achievement_data in Achievement.ACHIEVEMENTS:
            existing = Achievement.query.filter_by(name=achievement_data['name']).first()
            if not existing:
                achievement = Achievement(
                    name=achievement_data['name'],
                    condition=achievement_data['condition'],
                    message=achievement_data['message'],
                    points_reward=achievement_data['points_reward'],
                    icon_type=achievement_data['icon_type']
                )
                db.session.add(achievement)
        
        db.session.commit()
        return len(Achievement.ACHIEVEMENTS)


# -------------------------
# User Achievement Model
# -------------------------
class UserAchievement(db.Model):
    __tablename__ = 'user_achievement'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievement.id'), nullable=False)
    achieved_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with User
    user = db.relationship('User', backref='achievements')
    
    # Ensure a user can only earn an achievement once
    __table_args__ = (db.UniqueConstraint('user_id', 'achievement_id', name='_user_achievement_uc'),)

    @staticmethod
    def check_achievements(user_id):
        """Check if the user has earned any new achievements."""
        from sqlalchemy import func
        
        # Get the user
        user = User.query.get(user_id)
        if not user:
            return []
        
        # Get achievements the user has already earned
        earned_achievement_ids = [ua.achievement_id for ua in UserAchievement.query.filter_by(user_id=user_id).all()]
        
        # Get all possible achievements
        all_achievements = Achievement.query.all()
        
        newly_earned = []
        
        for achievement in all_achievements:
            # Skip if already earned
            if achievement.id in earned_achievement_ids:
                continue
                
            # Check conditions
            condition = achievement.condition
            earned = False
            
            # Total challenges
            if condition.endswith('_total'):
                count = int(condition.split('_')[0])
                total_completed = CompletedChallenge.query.filter_by(user_id=user_id).count()
                earned = total_completed >= count
                
            # Easy challenges
            elif condition.endswith('_easy'):
                count = int(condition.split('_')[0])
                easy_completed = CompletedChallenge.query.join(Challenge).filter(
                    CompletedChallenge.user_id == user_id,
                    Challenge.difficulty == 'E'
                ).count()
                earned = easy_completed >= count
                
            # Medium challenges
            elif condition.endswith('_medium'):
                count = int(condition.split('_')[0])
                medium_completed = CompletedChallenge.query.join(Challenge).filter(
                    CompletedChallenge.user_id == user_id,
                    Challenge.difficulty == 'M'
                ).count()
                earned = medium_completed >= count
                
            # Hard challenges
            elif condition.endswith('_hard'):
                count = int(condition.split('_')[0])
                hard_completed = CompletedChallenge.query.join(Challenge).filter(
                    CompletedChallenge.user_id == user_id,
                    Challenge.difficulty == 'H'
                ).count()
                earned = hard_completed >= count
                
            # Weekly all
            elif condition == 'weekly_all':
                earned = (user.weekly_e_completed >= user.weekly_e_cap and
                         user.weekly_m_completed >= user.weekly_m_cap and
                         user.weekly_h_completed >= user.weekly_h_cap)
                
            # Friend challenges
            elif condition.startswith('friend_'):
                count = int(condition.split('_')[1])
                friend_completed = db.session.query(func.count(FriendChallengeLink.id)).filter(
                    ((FriendChallengeLink.user1_id == user_id) & FriendChallengeLink.user1_confirmed) |
                    ((FriendChallengeLink.user2_id == user_id) & FriendChallengeLink.user2_confirmed)
                ).scalar()
                earned = friend_completed >= count
                
            # Habit challenges
            elif condition.startswith('habit_'):
                count = int(condition.split('_')[1])
                habit_completed = WeeklyHabitChallenge.query.filter(
                    WeeklyHabitChallenge.user_id == user_id,
                    WeeklyHabitChallenge.days_completed == 7
                ).count()
                earned = habit_completed >= count
                
            # If earned, create a new UserAchievement
            if earned:
                new_achievement = UserAchievement(user_id=user_id, achievement_id=achievement.id)
                db.session.add(new_achievement)
                newly_earned.append({
                    'name': achievement.name,
                    'message': achievement.message,
                    'points_reward': achievement.points_reward
                })
                
        if newly_earned:
            db.session.commit()
            
        return newly_earned


# -------------------------
# Friend Challenge Link Model
# -------------------------
class FriendChallengeLink(db.Model):
    __tablename__ = 'friend_challenge_link'
    
    id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=False)
    user1_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user2_id = db.Column(db.Integer, nullable=False)
    user1_confirmed = db.Column(db.Boolean, default=False)
    user2_confirmed = db.Column(db.Boolean, default=False)
    user1_completed = db.Column(db.Boolean, default=False)
    user2_completed = db.Column(db.Boolean, default=False)
    user1_completed_at = db.Column(db.DateTime, nullable=True)
    user2_completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    completion_expires_at = db.Column(db.DateTime, nullable=True)
    expired = db.Column(db.Boolean, default=False)
    
    # Relationships
    challenge = db.relationship('Challenge', backref='friend_links')
    user1 = db.relationship('User', backref='friend_challenges_initiated', foreign_keys=[user1_id])
    
    def is_complete(self):
        """Check if both users have confirmed the challenge."""
        return self.user1_confirmed and self.user2_confirmed
        
    def is_expired(self):
        """Check if the link has expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at


class FriendTokenUsage(db.Model):
    __tablename__ = 'friend_token_usage'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    used_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship('User', backref='friend_token_usages')


# -------------------------
# Challenge of the Week Model
# -------------------------
class ChallengeOfTheWeek(db.Model):
    __tablename__ = 'challenge_of_the_week'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=False)
    week_number = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_completed = db.Column(db.Date, nullable=True)
    times_completed = db.Column(db.Integer, default=0)
    
    # Relationships
    user = db.relationship('User', backref='challenge_of_the_week')
    challenge = db.relationship('Challenge', backref='cotw_selections')
    
    # Ensure a user can only have one Challenge of the Week per week
    __table_args__ = (db.UniqueConstraint('user_id', 'week_number', 'year', name='_user_cotw_week_uc'),)
    
    def can_complete_today(self):
        """Check if the challenge can be completed today."""
        today = datetime.utcnow().date()
        return self.last_completed is None or self.last_completed != today
    
    def complete_daily(self):
        """Mark the challenge as completed for today and increment count."""
        today = datetime.utcnow().date()
        self.last_completed = today
        self.times_completed += 1
        db.session.commit()
        
        # Return the points earned (50% of original challenge points)
        return int(self.challenge.points * 0.5)


# -------------------------
# Weekly Leaderboard Rewards Model
# -------------------------
class WeeklyLeaderboardReward(db.Model):
    __tablename__ = 'weekly_leaderboard_reward'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    week_number = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    rank = db.Column(db.Integer, nullable=False)  # 1, 2, or 3 for top three positions
    points_awarded = db.Column(db.Integer, nullable=False)
    awarded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with User
    user = db.relationship('User', backref='leaderboard_rewards')
    
    # Ensure a user can only receive one reward per week
    __table_args__ = (db.UniqueConstraint('user_id', 'week_number', 'year', name='_user_weekly_reward_uc'),)



# -------------------------
# Notification Model
# -------------------------
class Notification(db.Model):
    __tablename__ = 'notification'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with User
    user = db.relationship('User', backref='notifications')


# -------------------------
# Fun Fact Model
# -------------------------
class FunFact(db.Model):
    __tablename__ = 'fun_fact'
    id = db.Column(db.Integer, primary_key=True)
    fact = db.Column(db.String(500), nullable=False)
    source = db.Column(db.String(500), nullable=True)
    times_shown = db.Column(db.Integer, default=0)
    last_shown = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @staticmethod
    def import_from_json(app):
        """Import fun facts from JSON file."""
        json_file = os.path.join(app.static_folder, 'data', 'fun_facts.json')
        if not os.path.exists(json_file):
            app.logger.error(f"Fun facts JSON file not found at {json_file}")
            return False
            
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Check if we have exercise facts
            if 'exercise_facts' not in data:
                app.logger.error("No exercise_facts found in JSON file")
                return False
                
            # Get existing fact IDs to avoid duplicates
            existing_facts = {fact.id: fact for fact in FunFact.query.all()}
            
            # Import facts
            count = 0
            for fact_data in data['exercise_facts']:
                # Skip if already exists
                if fact_data['id'] in existing_facts:
                    continue
                    
                new_fact = FunFact(
                    id=fact_data['id'],
                    fact=fact_data['fact'],
                    source=fact_data.get('source', '')
                )
                db.session.add(new_fact)
                count += 1
                
            if count > 0:
                db.session.commit()
                app.logger.info(f"Imported {count} new fun facts")
            return True
            
        except Exception as e:
            app.logger.error(f"Error importing fun facts: {str(e)}")
            db.session.rollback()
            return False
            
    @staticmethod
    def get_random_fact():
        """Get a random fun fact, prioritizing ones that haven't been shown recently."""
        # First try to get facts that have never been shown
        never_shown = FunFact.query.filter(FunFact.times_shown == 0).all()
        if never_shown:
            return random.choice(never_shown)
            
        # Then try to get facts that have been shown less often
        return FunFact.query.order_by(FunFact.times_shown, FunFact.last_shown).first()
