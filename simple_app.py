from flask import Flask, render_template, redirect, url_for, flash, request, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
import secrets
import string
from datetime import datetime

# Create a simple Flask app
app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')

# Configure the app
app.config['SECRET_KEY'] = 'dev-key-for-session'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///simple_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Define a simple User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    backup_code = db.Column(db.String(16), unique=True)
    personal_code = db.Column(db.String(10), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
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
            if not User.query.filter_by(backup_code=code).first():
                self.backup_code = code
                return code
    
    def generate_personal_code(self):
        """Generate a unique personal code for friend challenges."""
        alphabet = string.ascii_uppercase + string.digits
        while True:
            code = ''.join(secrets.choice(alphabet) for _ in range(8))
            if not User.query.filter_by(personal_code=code).first():
                self.personal_code = code
                return code

# Create the database tables
with app.app_context():
    db.create_all()

# Login check decorator
def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Routes
@app.route('/')
def index():
    return redirect(url_for('profile'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            flash('Login successful!', 'success')
            return redirect(url_for('profile'))
        else:
            flash('Invalid username or password.', 'error')
    
    return render_template('simple_login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')
        
        if password != confirm:
            flash('Passwords do not match.', 'error')
            return render_template('simple_signup.html')
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already taken.', 'error')
            return render_template('simple_signup.html')
        
        try:
            new_user = User(username=username)
            new_user.set_password(password)
            
            # Generate unique backup and personal codes
            new_user.generate_backup_code()
            new_user.generate_personal_code()
            
            db.session.add(new_user)
            db.session.commit()
            
            session['user_id'] = new_user.id
            flash('Account created successfully!', 'success')
            return redirect(url_for('profile'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred during signup: {str(e)}', 'error')
    
    return render_template('simple_signup.html')

@app.route('/profile')
@login_required
def profile():
    user = User.query.get(session['user_id'])
    return render_template('simple_profile.html', user=user)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5007)
