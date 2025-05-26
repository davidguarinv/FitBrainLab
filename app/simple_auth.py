from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, current_user, login_required
from datetime import datetime
from .simple_models import SimpleUser
from . import db

bp = Blueprint('simple_auth', __name__)

@bp.route('/simple/login', methods=['GET', 'POST'])
def login():
    """Simple login route that works with the existing application."""
    if current_user.is_authenticated:
        return redirect(url_for('main.game', section='challenges'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        try:
            user = SimpleUser.query.filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user)
                flash('Login successful!', 'success')
                return redirect(url_for('main.game', section='challenges'))
            else:
                flash('Invalid username or password.', 'error')
        except Exception as e:
            current_app.logger.error(f"Login error: {str(e)}")
            flash('An error occurred during login. Please try again.', 'error')
    
    # Generate a random username for the signup form
    random_username = SimpleUser.generate_username()
    return render_template('simple/login.html', random_username=random_username)

@bp.route('/simple/signup', methods=['GET', 'POST'])
def signup():
    """Simple signup route that works with the existing application."""
    if current_user.is_authenticated:
        return redirect(url_for('main.game', section='challenges'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')
        
        if password != confirm:
            flash('Passwords do not match.', 'error')
            random_username = SimpleUser.generate_username()
            return render_template('simple/signup.html', random_username=random_username)
        
        # Check if username already exists
        try:
            existing_user = SimpleUser.query.filter_by(username=username).first()
            if existing_user:
                flash('Username already taken.', 'error')
                random_username = SimpleUser.generate_username()
                return render_template('simple/signup.html', random_username=random_username)
        except Exception as e:
            current_app.logger.error(f"Error checking existing user: {str(e)}")
            flash('Database error. Please try again.', 'error')
            random_username = SimpleUser.generate_username()
            return render_template('simple/signup.html', random_username=random_username)
        
        # Create new user
        try:
            # Create a new user object
            new_user = SimpleUser(username=username)
            new_user.set_password(password)
            
            # Generate unique backup and personal codes
            new_user.generate_backup_code()
            new_user.generate_personal_code()
            
            # Add the user to the database
            db.session.add(new_user)
            db.session.commit()
            current_app.logger.info(f"User created successfully: {username}")
            
            # Login the new user
            login_user(new_user)
            flash('Account created successfully!', 'success')
            # Redirect to the challenges section of the game page
            return redirect(url_for('main.game', section='challenges'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error during signup: {str(e)}")
            
            # Provide more specific error messages based on the exception
            if 'database is locked' in str(e):
                flash('The system is currently busy. Please wait a moment and try again.', 'error')
            elif 'UNIQUE constraint failed' in str(e):
                flash('This username is already taken. Please try a different one.', 'error')
            else:
                flash('An error occurred during signup. Please try again.', 'error')
            
            random_username = SimpleUser.generate_username()
            return render_template('simple/signup.html', random_username=random_username)
    
    # Generate a random username for the signup form
    random_username = SimpleUser.generate_username()
    return render_template('simple/signup.html', random_username=random_username)

@bp.route('/simple/profile', methods=['GET'])
@login_required
def profile():
    """Simple profile route that displays the user's backup and personal codes."""
    return render_template('simple/profile.html')
