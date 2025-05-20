from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from .models import User, Challenge, CompletedChallenge, InProgressChallenge, ChallengeRegeneration
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
    user_rank = None
    if current_user.is_authenticated:
        completed = CompletedChallenge.query\
            .filter_by(user_id=current_user.id)\
            .order_by(CompletedChallenge.completed_at.desc())\
            .limit(5).all()
            
        # Calculate user's rank based on points
        user_points = sum(c.challenge.points for c in completed)
        higher_ranked_users = db.session.query(db.func.count(User.id)).filter(
            User.id != current_user.id,
            User.is_public == True,
            # Subquery to get users with higher points
            User.id.in_(
                db.session.query(CompletedChallenge.user_id)
                .group_by(CompletedChallenge.user_id)
                .having(db.func.sum(Challenge.points) > user_points)
                .join(Challenge, Challenge.id == CompletedChallenge.challenge_id)
            )
        ).scalar() or 0
        
        user_rank = higher_ranked_users + 1  # User's rank (1-based)
            
        user_progress = {
            'completed_challenges': completed,
            'total_points': user_points,
            'daily_streak': current_user.daily_streak
        }
    
    # Get available challenges
    challenges = Challenge.query.all()
    
    # Get in-progress challenges for the current user if authenticated
    in_progress_challenges = []
    in_progress_count = 0
    if current_user.is_authenticated:
        in_progress = InProgressChallenge.query.filter_by(user_id=current_user.id).all()
        in_progress_count = len(in_progress)
        in_progress_challenge_ids = [c.challenge_id for c in in_progress]
        in_progress_challenges = Challenge.query.filter(Challenge.id.in_(in_progress_challenge_ids)).all() if in_progress_challenge_ids else []
    
    # Filter out in-progress challenges from available challenges
    available_challenges = [c for c in challenges if current_user.is_authenticated and c.id not in [ic.id for ic in in_progress_challenges] or not current_user.is_authenticated]
    
    # Get challenge regeneration timers
    now = datetime.utcnow()
    regeneration_timers = ChallengeRegeneration.query.all()
    regeneration_by_difficulty = {
        'E': sorted([r for r in regeneration_timers if r.difficulty == 'E'], key=lambda x: x.slot_number),
        'M': sorted([r for r in regeneration_timers if r.difficulty == 'M'], key=lambda x: x.slot_number),
        'H': sorted([r for r in regeneration_timers if r.difficulty == 'H'], key=lambda x: x.slot_number)
    }
    
    # Prepare challenges by difficulty with regeneration timers
    import random
    challenges_by_difficulty = {
        'E': [],
        'M': [],
        'H': []
    }
    
    # For each difficulty level, check regeneration timers and add available challenges
    for difficulty in ['E', 'M', 'H']:
        available_by_diff = [c for c in available_challenges if c.difficulty == difficulty]
        slots_count = 3 if difficulty == 'E' else (2 if difficulty == 'M' else 1)
        
        for i in range(slots_count):
            # Find the regeneration timer for this slot
            regen_timer = next((r for r in regeneration_by_difficulty[difficulty] if r.slot_number == i+1), None)
            
            # If timer exists and regeneration time has passed, or no timer exists
            if not regen_timer or regen_timer.regenerate_at <= now:
                # If we have available challenges, add one
                if available_by_diff:
                    challenge = random.choice(available_by_diff)
                    challenges_by_difficulty[difficulty].append({
                        'challenge': challenge,
                        'regenerating': False,
                        'time_remaining': None
                    })
                    available_by_diff.remove(challenge)  # Remove to avoid duplicates
                else:
                    # No available challenge, show empty slot
                    challenges_by_difficulty[difficulty].append({
                        'challenge': None,
                        'regenerating': False,
                        'time_remaining': None
                    })
            else:
                # Regeneration time hasn't passed, show timer
                time_remaining = (regen_timer.regenerate_at - now).total_seconds()
                hours = int(time_remaining // 3600)
                minutes = int((time_remaining % 3600) // 60)
                challenges_by_difficulty[difficulty].append({
                    'challenge': None,
                    'regenerating': True,
                    'time_remaining': f"{hours}h {minutes}m",
                    'slot_number': regen_timer.slot_number
                })
    
    # Add in-progress challenges to the context
    challenges_by_difficulty['in_progress'] = in_progress_challenges
    
    # Get recent completed challenges by any user
    recent_completed_challenges = db.session.query(
        CompletedChallenge, Challenge, User
    ).join(
        Challenge, Challenge.id == CompletedChallenge.challenge_id
    ).join(
        User, User.id == CompletedChallenge.user_id
    ).filter(
        User.is_public == True  # Only show public user completions
    ).order_by(
        CompletedChallenge.completed_at.desc()
    ).limit(5).all()
    
    # Create forms for auth section
    login_form = LoginForm() if section == 'auth' else None
    signup_form = RegistrationForm() if section == 'auth' else None

    return render_template('game.html',
                           section=section,
                           top_users=top_users,
                           user_progress=user_progress,
                           user_rank=user_rank,
                           challenges=challenges_by_difficulty,
                           recent_completed_challenges=recent_completed_challenges,
                           login_form=login_form,
                           signup_form=signup_form)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.game'))
    
    if request.method == 'POST':
        print(f"Login form data: {request.form}")
        username = request.form.get('username')
        password = request.form.get('password')
        remember_me = request.form.get('remember_me') == 'on'
        
        print(f"Username: {username}, Password provided: {'Yes' if password else 'No'}, Remember me: {remember_me}")
        
        # Basic validation
        if not username or not password:
            flash('Username and password are required', 'error')
            return redirect(url_for('main.game', section='auth'))
        
        # Authenticate user
        user = User.query.filter_by(username=username).first()
        if user is None or not user.check_password(password):
            flash('Invalid username or password', 'error')
            return redirect(url_for('main.game', section='auth'))
            
        # Log in the user
        login_user(user, remember=remember_me)
        flash('Logged in successfully!', 'success')
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
    
    if request.method == 'POST':
        print(f"Signup form data: {request.form}")
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        print(f"Username: {username}, Password provided: {'Yes' if password else 'No'}, Confirm provided: {'Yes' if confirm_password else 'No'}")
        
        # Basic validation
        if not username or not password:
            flash('Username and password are required', 'error')
            return redirect(url_for('main.game', section='auth'))
            
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('main.game', section='auth'))
        
        # Check if username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already taken', 'error')
            return redirect(url_for('main.game', section='auth'))
            
        # Create new user
        try:
            user = User(
                username=username,
                is_public=True
            )
            user.set_password(password)
            
            # Save to database
            db.session.add(user)
            db.session.commit()
            print(f"User created with id: {user.id}")
            
            # Log in the new user
            login_user(user)
            flash('Account created successfully!', 'success')
            return redirect(url_for('main.game'))
        except Exception as e:
            print(f"Error creating user: {str(e)}")
            db.session.rollback()
            flash('An error occurred during signup', 'error')
            return redirect(url_for('main.game', section='auth'))
    
    # GET request
    return redirect(url_for('main.game', section='auth'))
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
        return redirect(url_for('main.game', section='challenges', active=challenge_id))
    
    # Check if user already has 2 challenges in progress
    in_progress_count = InProgressChallenge.query.filter_by(
        user_id=current_user.id
    ).count()
    
    if in_progress_count >= 2:
        flash('You can only have 2 challenges in progress at once', 'error')
        return redirect(url_for('main.game', section='challenges'))
    
    # Create new in-progress challenge
    ip = InProgressChallenge(
        user_id=current_user.id,
        challenge_id=challenge_id,
        started_at=datetime.utcnow()
    )
    db.session.add(ip)
    db.session.commit()
    
    # Redirect to challenges page with active challenge
    return redirect(url_for('main.game', section='challenges', active=challenge_id))

@bp.route('/api/challenges/<int:challenge_id>/complete', methods=['POST'])
@login_required
def complete_challenge(challenge_id):
    # Check if in progress
    ip = InProgressChallenge.query.filter_by(
        user_id=current_user.id,
        challenge_id=challenge_id
    ).first()
    
    if not ip:
        flash('Challenge not started', 'error')
        return redirect(url_for('main.game', section='challenges'))
    
    # Get challenge details
    challenge = Challenge.query.get_or_404(challenge_id)
    
    # Mark as completed
    completed = CompletedChallenge(
        user_id=current_user.id,
        challenge_id=challenge_id,
        completed_at=datetime.utcnow(),
        points_earned=challenge.points
    )
    
    # Remove from in-progress and add completed challenge
    db.session.delete(ip)
    db.session.add(completed)
    db.session.commit()
    
    # Flash a success message and redirect to progress page
    flash('Challenge completed successfully!', 'success')
    return redirect(url_for('main.game', section='progress'))

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

@bp.route('/api/profile/delete-account', methods=['POST'])
@login_required
def delete_account():
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'You must be logged in to perform this action'})
        
    try:
        # Delete user's completed challenges
        CompletedChallenge.query.filter_by(user_id=current_user.id).delete()
        
        # Delete user's in-progress challenges
        InProgressChallenge.query.filter_by(user_id=current_user.id).delete()
        
        # Get user ID before logging out
        user_id = current_user.id
        
        # Log the user out
        logout_user()
        
        # Delete the user
        User.query.filter_by(id=user_id).delete()
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})
