from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from .models import User, Challenge, CompletedChallenge, InProgressChallenge
from .forms import LoginForm, RegistrationForm
from datetime import datetime, timedelta
from sqlalchemy import func

# Create blueprint
bp = Blueprint('main', __name__)

# Main application routes
@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/about')
def about():
    return render_template('about.html')

@bp.route('/research')
def research():
    return render_template('research.html')

@bp.route('/publications')
def publications():
    return render_template('publications.html')

@bp.route('/communities')
def communities():
    return render_template('communities5.html')

@bp.route('/game')
@bp.route('/game/<section>')
def game(section='challenges'):
    if not current_user.is_authenticated and section not in ['leaderboard', None]:
        section = 'auth'
    
    # Get top users for the leaderboard with their points
    points_subq = db.session.query(
        CompletedChallenge.user_id,
        db.func.sum(Challenge.points).label('total_points')
    ).join(
        Challenge,
        Challenge.id == CompletedChallenge.challenge_id
    ).group_by(CompletedChallenge.user_id).subquery()

    top_users = db.session.query(User, db.func.coalesce(points_subq.c.total_points, 0))\
        .outerjoin(points_subq, User.id == points_subq.c.user_id)\
        .filter(User.is_public == True)\
        .order_by(db.desc('total_points'))\
        .limit(10).all()
    
    # Get user's progress if authenticated
    user_progress = None
    if current_user.is_authenticated:
        completed = CompletedChallenge.query\
            .filter_by(user_id=current_user.id)\
            .order_by(CompletedChallenge.completed_at.desc())\
            .limit(5).all()
        user_progress = {
            'completed_challenges': completed,
            'total_points': sum(c.challenge.points for c in completed),
            'daily_streak': current_user.daily_streak
        }
    
    # Get available challenges
    challenges = Challenge.query.all()
    challenges_by_difficulty = {
        'E': [c for c in challenges if c.difficulty == 'E'],
        'M': [c for c in challenges if c.difficulty == 'M'],
        'H': [c for c in challenges if c.difficulty == 'H']
    }
    
    # Create forms for auth section
    login_form = LoginForm() if section == 'auth' else None
    signup_form = RegistrationForm() if section == 'auth' else None

    return render_template('game.html',
                           section=section,
                           top_users=top_users,
                           user_progress=user_progress,
                           challenges=challenges_by_difficulty,
                           login_form=login_form,
                           signup_form=signup_form)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.game'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password', 'error')
            return redirect(url_for('main.game', section='auth'))
            
        login_user(user)
        flash('Successfully logged in!', 'success')
        return redirect(url_for('main.game'))
        
    return redirect(url_for('main.game', section='auth'))

@bp.route('/login-redirect')
def login_redirect():
    return redirect(url_for('main.login'))

@bp.route('/signup-redirect')
def signup_redirect():
    return redirect(url_for('main.signup'))

@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('main.game'))
        
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if user already exists
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Email already registered', 'error')
            return redirect(url_for('main.game', section='auth'))
            
        # Create new user
        user = User(
            username=form.username.data,
            email=form.email.data,
            is_public=True
        )
        user.set_password(form.password.data)
        
        # Save to database
        db.session.add(user)
        db.session.commit()
        
        # Log in the new user
        login_user(user)
        flash('Account created successfully!', 'success')
        return redirect(url_for('main.game'))
    return redirect(url_for('main.game', section='auth'))

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('main.game'))
    
    # Calculate total points for each user
    for user in top_users:
        total_points = db.session.query(func.sum(Challenge.points)).join(
            CompletedChallenge,
            Challenge.id == CompletedChallenge.challenge_id
        ).filter(
            CompletedChallenge.user_id == user.id
        ).scalar() or 0
        user.total_points = total_points

# API Routes
@bp.route('/api/challenges', methods=['GET'])
@login_required
def list_challenges():
    challenges = Challenge.query.all()
    return jsonify([{
        'id': c.id,
        'title': c.title,
        'description': c.description,
        'difficulty': c.difficulty,
        'points': c.points
    } for c in challenges])

@bp.route('/api/challenges/<int:challenge_id>/start', methods=['POST'])
@login_required
def start_challenge(challenge_id):
    # Check if already in progress
    existing = InProgressChallenge.query.filter_by(
        user_id=current_user.id,
        challenge_id=challenge_id
    ).first()
    
    if existing:
        return jsonify({'status': 'already_started'})
    
    # Create new in-progress challenge
    ip = InProgressChallenge(
        user_id=current_user.id,
        challenge_id=challenge_id,
        started_at=datetime.utcnow()
    )
    db.session.add(ip)
    db.session.commit()
    
    return jsonify({'status': 'started', 'id': ip.id})

@bp.route('/api/challenges/<int:challenge_id>/complete', methods=['POST'])
@login_required
def complete_challenge(challenge_id):
    # Check if in progress
    ip = InProgressChallenge.query.filter_by(
        user_id=current_user.id,
        challenge_id=challenge_id
    ).first()
    
    if not ip:
        return jsonify({'error': 'Challenge not started'}), 400
    
    # Get challenge details
    challenge = Challenge.query.get_or_404(challenge_id)
    
    # Mark as completed
    completed = CompletedChallenge(
        user_id=current_user.id,
        challenge_id=challenge_id,
        completed_at=datetime.utcnow(),
        points_earned=challenge.points
    )
    
    # Update user points
    current_user.points = (current_user.points or 0) + challenge.points
    
    # Remove from in-progress
    db.session.delete(ip)
    db.session.add(completed)
    db.session.commit()
    
    return jsonify({
        'status': 'completed',
        'points_earned': challenge.points,
        'total_points': current_user.points
    })

@bp.route('/api/progress')
@login_required
def get_progress():
    # Get completed challenges
    completed = db.session.query(
        Challenge,
        CompletedChallenge.completed_at
    ).join(
        CompletedChallenge,
        Challenge.id == CompletedChallenge.challenge_id
    ).filter(
        CompletedChallenge.user_id == current_user.id
    ).all()
    
    # Get in-progress challenges
    in_progress = db.session.query(
        Challenge,
        InProgressChallenge.started_at
    ).join(
        InProgressChallenge,
        Challenge.id == InProgressChallenge.challenge_id
    ).filter(
        InProgressChallenge.user_id == current_user.id
    ).all()
    
    return jsonify({
        'completed': [{
            'id': c.id,
            'title': c.title,
            'points': c.points,
            'completed_at': completed_at.isoformat()
        } for c, completed_at in completed],
        'in_progress': [{
            'id': c.id,
            'title': c.title,
            'started_at': started_at.isoformat()
        } for c, started_at in in_progress],
        'total_points': current_user.points or 0
    })

@bp.route('/api/leaderboard')
def get_leaderboard():
    # Get top users by points
    top_users = db.session.query(
        User,
        db.func.coalesce(db.func.sum(CompletedChallenge.points_earned), 0).label('total_points')
    ).outerjoin(
        CompletedChallenge,
        User.id == CompletedChallenge.user_id
    ).filter(
        User.is_public == True
    ).group_by(
        User.id
    ).order_by(
        db.desc('total_points')
    ).limit(10).all()
    
    # Add current user if not in top 10
    current_user_data = None
    if current_user.is_authenticated:
        user_rank = db.session.query(
            db.func.count(User.id)
        ).filter(
            User.is_public == True,
            User.id != current_user.id,
            db.func.coalesce(
                db.func.sum(CompletedChallenge.points_earned).filter(
                    CompletedChallenge.user_id == User.id
                ), 0
            ) > db.func.coalesce(
                db.func.sum(CompletedChallenge.points_earned).filter(
                    CompletedChallenge.user_id == current_user.id
                ), 0
            )
        ).scalar() + 1
        
        current_user_data = {
            'rank': user_rank,
            'username': current_user.username,
            'points': current_user.points or 0
        }
    
    return jsonify({
        'top_users': [{
            'rank': i + 1,
            'username': user.username,
            'points': int(points)
        } for i, (user, points) in enumerate(top_users)],
        'current_user': current_user_data
    })

@bp.route('/api/profile')
@login_required
def get_profile():
    return jsonify({
        'username': current_user.username,
        'email': current_user.email,
        'is_public': current_user.is_public,
        'points': current_user.points or 0,
        'top_sport': current_user.top_sport,
        'member_since': current_user.created_at.isoformat()
    })

@bp.route('/api/profile', methods=['PUT'])
@login_required
def update_profile():
    data = request.get_json()
    
    if 'username' in data:
        current_user.username = data['username']
    if 'email' in data:
        current_user.email = data['email']
    if 'is_public' in data:
        current_user.is_public = data['is_public']
    if 'password' in data and data['password']:
        current_user.set_password(data['password'])
    
    db.session.commit()
    return jsonify({'status': 'success'})

@bp.route('/api/profile', methods=['DELETE'])
@login_required
def delete_profile():
    db.session.delete(current_user)
    db.session.commit()
    logout_user()
    return jsonify({'status': 'account_deleted'})
