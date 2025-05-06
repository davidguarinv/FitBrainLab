from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from .models import db, User, Challenge, CompletedChallenge, InProgressChallenge
from datetime import datetime, timedelta
from sqlalchemy import func

bp = Blueprint('game', __name__, url_prefix='/game')

# Main Routes
@bp.route('/')
def index():
    # Get sample challenges for each difficulty
    sample_challenges = {
        'easy': Challenge.query.filter_by(difficulty='E').first(),
        'medium': Challenge.query.filter_by(difficulty='M').first(),
        'hard': Challenge.query.filter_by(difficulty='H').first()
    }
    
    # Get top users for leaderboard
    top_users = User.query.filter_by(is_public=True).limit(10).all()
    
    # Calculate total points for each user
    for user in top_users:
        total_points = db.session.query(func.sum(Challenge.points)).join(
            CompletedChallenge,
            Challenge.id == CompletedChallenge.challenge_id
        ).filter(
            CompletedChallenge.user_id == user.id
        ).scalar() or 0
        user.total_points = total_points
    
    return render_template('game.html', 
                         sample_challenges=sample_challenges,
                         top_users=top_users,
                         user=current_user)

@bp.route('/login', methods=['POST'])
def login():
    data = request.form
    user = User.query.filter_by(email=data.get('email')).first()
    
    if user and user.check_password(data.get('password')):
        login_user(user)
        return redirect(url_for('game.index'))
    
    flash('Invalid email or password')
    return redirect(url_for('game.index'))

@bp.route('/signup', methods=['POST'])
def signup():
    data = request.form
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        flash('Email and password are required')
        return redirect(url_for('game.index'))
    
    if User.query.filter_by(email=email).first():
        flash('Email already registered')
        return redirect(url_for('game.index'))
    
    user = User(
        username=User.generate_username(),
        email=email,
        is_public=True
    )
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    login_user(user)
    return redirect(url_for('game.index'))

@bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('game.index'))

# API Routes
@bp.route('/api/challenges')
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
    challenge = Challenge.query.get_or_404(challenge_id)
    
    # Check if already in progress
    if InProgressChallenge.query.filter_by(
        user_id=current_user.id,
        challenge_id=challenge_id
    ).first():
        return jsonify(msg="Challenge already in progress"), 400
    
    in_progress = InProgressChallenge(
        user_id=current_user.id,
        challenge_id=challenge_id
    )
    db.session.add(in_progress)
    db.session.commit()
    
    return jsonify(success=True)

@bp.route('/api/challenges/<int:challenge_id>/complete', methods=['POST'])
@login_required
def complete_challenge(challenge_id):
    # Remove from in progress
    in_progress = InProgressChallenge.query.filter_by(
        user_id=current_user.id,
        challenge_id=challenge_id
    ).first_or_404()
    
    db.session.delete(in_progress)
    
    # Add to completed
    completed = CompletedChallenge(
        user_id=current_user.id,
        challenge_id=challenge_id
    )
    db.session.add(completed)
    db.session.commit()
    
    return jsonify(success=True)

@bp.route('/api/progress')
@login_required
def get_progress():
    today = datetime.utcnow().date()
    start_of_week = today - timedelta(days=today.weekday())
    
    # Get completed challenges for the week
    completed = db.session.query(
        func.date(CompletedChallenge.completed_at).label('date'),
        func.sum(Challenge.points).label('points')
    ).join(Challenge).filter(
        CompletedChallenge.user_id == current_user.id,
        CompletedChallenge.completed_at >= start_of_week
    ).group_by('date').all()
    
    # Format as {date: points}
    progress = {str(c.date): c.points for c in completed}
    
    return jsonify(progress)

@bp.route('/api/leaderboard')
def get_leaderboard():
    today = datetime.utcnow().date()
    start = today - timedelta(days=today.weekday())
    board = []
    
    for u in User.query.filter_by(is_public=True):
        pts = db.session.query(func.sum(Challenge.points)).join(
            CompletedChallenge,
            Challenge.id == CompletedChallenge.challenge_id
        ).filter(
            CompletedChallenge.user_id == u.id,
            CompletedChallenge.completed_at >= start
        ).scalar() or 0
        
        board.append({
            'username': u.username,
            'points': pts
        })
    
    return jsonify(sorted(board, key=lambda x: x['points'], reverse=True))

@bp.route('/api/profile')
@login_required
def get_profile():
    return jsonify({
        'username': current_user.username,
        'email': current_user.email,
        'is_public': current_user.is_public,
        'top_sport': current_user.top_sport
    })

@bp.route('/api/profile', methods=['PUT'])
@login_required
def update_profile():
    data = request.json
    
    if 'is_public' in data:
        current_user.is_public = data['is_public']
        
    if 'top_sport' in data:
        now = datetime.utcnow()
        if not current_user.last_sport_update or (now - current_user.last_sport_update).days >= 30:
            current_user.top_sport = data['top_sport']
            current_user.last_sport_update = now
            
    if 'password' in data:
        current_user.set_password(data['password'])
        
    db.session.commit()
    return jsonify(success=True)

@bp.route('/api/profile', methods=['DELETE'])
@login_required
def delete_profile():
    db.session.delete(current_user)
    db.session.commit()
    logout_user()
    return jsonify(success=True)
