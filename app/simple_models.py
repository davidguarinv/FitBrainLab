from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import string
from datetime import datetime
from . import db

class SimpleUser(UserMixin, db.Model):
    """A simplified user model that works with the existing database structure."""
    __tablename__ = 'simple_user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_public = db.Column(db.Boolean, default=True)
    backup_code = db.Column(db.String(16), unique=True)
    personal_code = db.Column(db.String(10), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Weekly challenge caps (copied from original User model)
    weekly_e_cap = db.Column(db.Integer, default=9)
    weekly_m_cap = db.Column(db.Integer, default=6)
    weekly_h_cap = db.Column(db.Integer, default=3)
    weekly_e_completed = db.Column(db.Integer, default=0)
    weekly_m_completed = db.Column(db.Integer, default=0)
    weekly_h_completed = db.Column(db.Integer, default=0)
    
    # Daily challenge counts
    daily_e_count = db.Column(db.Integer, default=0)
    daily_m_count = db.Column(db.Integer, default=0)
    daily_h_count = db.Column(db.Integer, default=0)
    
    def set_password(self, password):
        """Hash and store password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check hashed password."""
        return check_password_hash(self.password_hash, password)
    
    def generate_backup_code(self):
        """Generate a unique backup code for password recovery."""
        while True:
            code = secrets.token_hex(8)  # 16 character hex string
            if not SimpleUser.query.filter_by(backup_code=code).first():
                self.backup_code = code
                return code
    
    def generate_personal_code(self):
        """Generate a unique personal code for friend challenges."""
        alphabet = string.ascii_uppercase + string.digits
        while True:
            code = ''.join(secrets.choice(alphabet) for _ in range(8))
            if not SimpleUser.query.filter_by(personal_code=code).first():
                self.personal_code = code
                return code
    
    @staticmethod
    def generate_username():
        """Generate a fun random username."""
        adjectives = ['Happy', 'Clever', 'Swift', 'Bright', 'Agile', 'Quick', 'Smart', 'Active', 'Dynamic', 'Sharp',
                      'Brilliant', 'Creative', 'Focused', 'Energetic', 'Powerful']
        nouns = ['Brain', 'Mind', 'Thinker', 'Runner', 'Player', 'Athlete', 'Champion', 'Winner', 'Master', 'Star',
                 'Genius', 'Ninja', 'Expert', 'Guru', 'Hero']
        import random
        number = random.randint(1, 999)
        adjective = random.choice(adjectives)
        noun = random.choice(nouns)
        return f"{adjective}{noun}{number}"
