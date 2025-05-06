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
    email = db.Column(db.String(120), unique=True, nullable=False)  # Email
    password_hash = db.Column(db.String(128))  # Hashed password
    is_public = db.Column(db.Boolean, default=True)  # Whether user profile is public
    top_sport = db.Column(db.String(50))  # Optional: most-played sport
    last_sport_update = db.Column(db.DateTime)  # Last update timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Creation timestamp

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


# -------------------------
# In Progress Challenge Model
# -------------------------
class InProgressChallenge(db.Model):
    __tablename__ = 'in_progress_challenge'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
