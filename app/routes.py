from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from . import db
from .models import User, Challenge, CompletedChallenge, InProgressChallenge, ChallengeRegeneration
from .forms import LoginForm, RegistrationForm
from .email_handler import send_email
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

@bp.route('/submit-application', methods=['POST'])
def submit_application():
    """Handle form submission"""
    try:
        # Check email configuration
        if not current_app.config.get('EMAIL_USER'):
            return jsonify({
                'success': False,
                'message': 'Email configuration is not set up. Please contact the administrator.'
            }), 500
            
        # Get form data
        form_data = {
            'first_name': request.form.get('first_name'),
            'last_name': request.form.get('last_name'),
            'email': request.form.get('email'),
            'phone': request.form.get('phone'),
            'education': request.form.get('education'),
            'interest': request.form.get('interest'),
            'message': request.form.get('message')
        }
        
        # Validate required fields
        required_fields = ['first_name', 'last_name', 'email', 'education', 'interest', 'message']
        for field in required_fields:
            if not form_data.get(field):
                return jsonify({
                    'success': False, 
                    'message': f'{field.replace("_", " ").title()} is required'
                }), 400
        
        # Send email
        if send_email(form_data):
            return jsonify({
                'success': True, 
                'message': 'Application submitted successfully!'
            })
        else:
            return jsonify({
                'success': False, 
                'message': 'Failed to send application. Please try again.'
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Error processing application: {e}")
        return jsonify({
            'success': False, 
            'message': 'An error occurred. Please try again.'
        }), 500

@bp.route('/research')
def research():
    return render_template('research.html')

@bp.route('/publications')
def publications():
    return render_template('publications.html')

@bp.route('/research/stayfine')
def stayfine():
    return render_template('/research/stay_fine.html')

@bp.route('/research/stride4')
def stride4():
    return render_template('/research/stride-4.html')

@bp.route('/research/brain_adaptations')
def brain_adaptations():
    return render_template('/research/brain_adaptations.html')

@bp.route('/research/leopard_predict')
def leopard_predict():
    return render_template('/research/leopard_predict.html')

@bp.route('/game')
@bp.route('/game/<section>')
def game(section='challenges'):
    if not current_user.is_authenticated and section not in ['leaderboard', None]:
        section = 'auth'
    
    # Get top users for the all-time leaderboard
    all_time_users = db.session.query(
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
    
    # Get top users for the weekly leaderboard (challenges completed in the last 7 days)
    from datetime import datetime, timedelta
    one_week_ago = datetime.utcnow() - timedelta(days=7)
    
    weekly_users = db.session.query(
        User,
        db.func.coalesce(db.func.sum(CompletedChallenge.points_earned), 0).label('weekly_points')
    ).outerjoin(
        CompletedChallenge,
        (User.id == CompletedChallenge.user_id) & (CompletedChallenge.completed_at >= one_week_ago)
    ).filter(
        User.is_public == True
    ).group_by(
        User.id
    ).order_by(
        db.desc('weekly_points')
    ).limit(10).all()
    
    # Get active challenge ID from request args
    active_challenge_id = request.args.get('active')
    
    # Get user's progress if authenticated
    user_progress = None
    user_rank = None
    if current_user.is_authenticated:
        completed = CompletedChallenge.query\
            .filter_by(user_id=current_user.id)\
            .order_by(CompletedChallenge.completed_at.desc())\
            .limit(5).all()
            
        # Calculate user's rank based on points - use the same method as the leaderboard
        # Get the user's total points
        user_points = db.session.query(func.sum(CompletedChallenge.points_earned)).filter_by(user_id=current_user.id).scalar() or 0
        
        # Count how many users have more points than the current user
        higher_ranked_users = db.session.query(User).filter(
            User.id != current_user.id,
            User.is_public == True
        ).join(
            CompletedChallenge,
            User.id == CompletedChallenge.user_id
        ).group_by(
            User.id
        ).having(
            func.sum(CompletedChallenge.points_earned) > user_points
        ).count()
        
        user_rank = higher_ranked_users + 1  # User's rank (1-based)
            
        user_progress = {
            'completed_challenges': completed,
            'total_points': user_points,
            'rank': user_rank,
            'daily_streak': current_user.daily_streak
        }
    
    # Get challenges that are currently in progress
    if current_user.is_authenticated:
        in_progress = InProgressChallenge.query.filter_by(user_id=current_user.id).all()
        in_progress_challenge_ids = [c.challenge_id for c in in_progress]
        in_progress_challenges = Challenge.query.filter(Challenge.id.in_(in_progress_challenge_ids)).all() if in_progress_challenge_ids else []
    else:
        in_progress_challenges = []
    
    # Add in-progress challenges to the context
    challenges_by_difficulty = {
        'in_progress': in_progress_challenges
    }
    
    # Create forms for auth section
    login_form = LoginForm() if section == 'auth' else None
    signup_form = RegistrationForm() if section == 'auth' else None

    return render_template('game.html', 
                           section=section, 
                           user_progress=user_progress,
                           top_users=all_time_users,
                           weekly_users=weekly_users,
                           challenges=challenges_by_difficulty,
                           active_challenge_id=active_challenge_id,
                           in_progress_challenges=in_progress_challenges,
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

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('main.game'))

@bp.route('/api/leaderboard')
def get_leaderboard():
    """Get leaderboard data"""
    # Get the leaderboard type from request args (default to 'all-time')
    leaderboard_type = request.args.get('type', 'all-time')
    
    # All-time leaderboard
    if leaderboard_type == 'all-time':
        # Query for users with their total points
        users = db.session.query(
            User,
            func.sum(CompletedChallenge.points_earned).label('total_points')
        ).join(
            CompletedChallenge,
            User.id == CompletedChallenge.user_id
        ).filter(
            User.is_public == True  # Only include users who have opted to be on the leaderboard
        ).group_by(
            User.id
        ).order_by(
            func.sum(CompletedChallenge.points_earned).desc()
        ).limit(100).all()
        
        # Format the results
        leaderboard = [
            {
                'rank': i + 1,
                'username': user.username,
                'points': int(points) if points else 0,
                'is_current_user': user.id == current_user.id if current_user.is_authenticated else False
            }
            for i, (user, points) in enumerate(users)
        ]
    
    # Weekly leaderboard (challenges completed in the last 7 days)
    elif leaderboard_type == 'weekly':
        from datetime import datetime, timedelta
        one_week_ago = datetime.utcnow() - timedelta(days=7)
        
        # Query for users with their weekly points
        users = db.session.query(
            User,
            func.sum(CompletedChallenge.points_earned).label('weekly_points')
        ).join(
            CompletedChallenge,
            (User.id == CompletedChallenge.user_id) & (CompletedChallenge.completed_at >= one_week_ago)
        ).filter(
            User.is_public == True  # Only include users who have opted to be on the leaderboard
        ).group_by(
            User.id
        ).order_by(
            func.sum(CompletedChallenge.points_earned).desc()
        ).limit(100).all()
        
        # Format the results
        leaderboard = [
            {
                'rank': i + 1,
                'username': user.username,
                'points': int(points) if points else 0,
                'is_current_user': user.id == current_user.id if current_user.is_authenticated else False
            }
            for i, (user, points) in enumerate(users)
        ]
    
    return jsonify({
        'leaderboard': leaderboard,
        'type': leaderboard_type
    })

@login_required
def get_progress():
    """Get progress information for the current user"""
    # Get completed challenges
    completed_challenges = CompletedChallenge.query.filter_by(user_id=current_user.id).order_by(CompletedChallenge.completed_at.desc()).all()
    
    # Get daily streak information
    daily_streak = current_user.daily_streak
    
    # Get total points
    total_points = db.session.query(func.sum(CompletedChallenge.points_earned)).filter_by(user_id=current_user.id).scalar() or 0
    
    # Calculate user ranking
    higher_ranked_users = db.session.query(User).filter(
        User.id != current_user.id,
        User.is_public == True
    ).join(
        CompletedChallenge,
        User.id == CompletedChallenge.user_id
    ).group_by(
        User.id
    ).having(
        func.sum(CompletedChallenge.points_earned) > total_points
    ).count()
    
    rank = higher_ranked_users + 1  # User's rank (1-based)
    
    return jsonify({
        'completed_challenges': [
            {
                'id': cc.id,
                'challenge_id': cc.challenge_id,
                'challenge_title': cc.challenge.title,
                'points_earned': cc.points_earned,
                'completed_at': cc.completed_at.isoformat()
            } for cc in completed_challenges
        ],
        'daily_streak': daily_streak,
        'total_points': total_points,
        'rank': rank
    })

@bp.route('/api/profile')
@login_required
def get_profile():
    """Get profile information for the current user"""
    return jsonify({
        'username': current_user.username,
        'is_public': current_user.is_public,
        'top_sport_category': current_user.top_sport_category,
        'daily_streak': current_user.daily_streak,
        'created_at': current_user.created_at.isoformat() if current_user.created_at else None
    })

@bp.route('/api/profile', methods=['PUT'])
@login_required
def update_profile():
    """Update profile information for the current user"""
    data = request.get_json()
    
    if 'is_public' in data:
        current_user.is_public = data['is_public']
    
    if 'top_sport_category' in data:
        current_user.top_sport_category = data['top_sport_category']
        current_user.last_sport_update = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Profile updated successfully'
    })

@bp.route('/update_profile', methods=['POST'])
@login_required
def update_profile_form():
    # Handle form submission from profile page
    if 'top_sport_category' in request.form:
        current_user.top_sport_category = request.form.get('top_sport_category')
        current_user.last_sport_update = datetime.utcnow()
        db.session.commit()
        flash('Profile updated successfully!', 'success')
    
    return redirect(url_for('main.game', section='profile'))

@bp.route('/api/profile', methods=['DELETE'])
@login_required
def delete_profile():
    """Reset profile information for the current user"""
    current_user.is_public = False
    current_user.top_sport_category = None
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Profile reset successfully'
    })

@bp.route('/api/profile/delete-account', methods=['POST'])
@login_required
def delete_account():
    """Delete user account and all associated data"""
    # Verify the password
    data = request.get_json()
    password = data.get('password')
    
    if not password or not current_user.check_password(password):
        return jsonify({
            'success': False,
            'message': 'Invalid password'
        }), 401
    
    # Delete all associated data
    CompletedChallenge.query.filter_by(user_id=current_user.id).delete()
    InProgressChallenge.query.filter_by(user_id=current_user.id).delete()
    ChallengeRegeneration.query.filter_by(user_id=current_user.id).delete()
    
    # Delete the user
    user_id = current_user.id
    logout_user()
    User.query.filter_by(id=user_id).delete()
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Account deleted successfully'
    })

@bp.route('/communities')
def communities():
    import os
    import pandas as pd
    from flask import request, render_template

    # Use the communities_with_logos.json file for better image support
    import json
    path = os.path.join("static", "data", "communities_with_logos.json")
    
    with open(path, 'r') as file:
        communities_data = json.load(file)
    
    # Convert to DataFrame for consistent handling
    df = pd.DataFrame(communities_data)

    # Normalize cost column to numeric
    df['Cost'] = pd.to_numeric(df['Cost'], errors='coerce')

    # Define cost ranges
    cost_ranges = {
        "0-50": (0, 50),
        "51-100": (51, 100),
        "101-200": (101, 200),
        "201+": (201, float('inf'))
    }

    # Get filter parameters
    selected_sport = request.args.get("sport", "")
    selected_cost_range = request.args.get("cost", "")

    # Apply filters
    if selected_sport:
        df = df[df["Sport"] == selected_sport]
    if selected_cost_range in cost_ranges:
        low, high = cost_ranges[selected_cost_range]
        df = df[df["Cost"].between(low, high)]

    # Extract all sports for the filter dropdown
    all_sports = sorted(df['Sport'].dropna().unique())

    # Pagination setup
    try:
        page = int(request.args.get("page", 1))
    except ValueError:
        page = 1

    per_page = 6
    total = len(df)
    total_pages = max((total + per_page - 1) // per_page, 1)
    page = max(1, min(page, total_pages))

    start = (page - 1) * per_page
    end = start + per_page
    paginated = df.iloc[start:end]

    return render_template(
        "communities.html",
        communities=paginated.to_dict(orient="records"),
        page=page,
        total_pages=total_pages,
        sports=all_sports,
        selected_sport=selected_sport,
        cost_ranges=cost_ranges,
        selected_cost_range=selected_cost_range
    )

