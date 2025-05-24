from datetime import datetime, timedelta
import json
import math
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from . import db
from .models import User, Challenge, CompletedChallenge, InProgressChallenge, ChallengeRegeneration, UserChallenge, WeeklyChallengeSet, UserWeeklyOrder, WeeklyHabitChallenge
from .forms import LoginForm, RegistrationForm
from .email_handler import send_email
import logging
import os
import json
from sqlalchemy import func
import uuid
import re
import math

print(">>> THIS routes.py LOADED <<<")

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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
    """Handle form submission from about page"""
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
        
        # Send email (using 'application' type for about page form)
        if send_email(form_data, 'application'):
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

@bp.route('/submit_community', methods=['POST'])
def submit_community():
    """Handle community form submission"""
    try:
        # Log detailed request information
        logger.info("Community form submission received")
        logger.info(f"Request URL: {request.url}")
        logger.info(f"Request method: {request.method}")
        logger.info(f"Request content type: {request.content_type}")
        logger.info(f"Request headers: {dict(request.headers)}")
        logger.info(f"Form data: {dict(request.form)}")
        logger.info(f"Request args: {dict(request.args)}")
        logger.info(f"Request path: {request.path}")
        logger.info(f"Request full path: {request.full_path}")
        logger.info(f"Base URL: {request.base_url}")
        logger.info(f"Host URL: {request.host_url}")
        
        # Get all form data
        form_data = request.form.to_dict()
        
        # Update field names for consistency
        if 'Location' in form_data:
            form_data['Address'] = form_data.pop('Location')
        
        logger.info(f"Processed form data: {form_data}")
        
        return jsonify({
            'success': True,
            'message': 'Form received successfully'
        })
    except Exception as e:
        logger.error(f"Error processing community submission: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")
        return jsonify({
            'success': False, 
            'message': f'Error processing form: {str(e)}'
        }), 500

    try:
        # Get all form data
        form_data = request.form.to_dict()
        logger.debug(f"Processed form data: {form_data}")
        
        # Validate required fields
        required_fields = ['Name', 'email', 'Location', 'Sport', 'website', 'message']
        for field in required_fields:
            if not form_data.get(field):
                error_message = f'{field.replace("_", " ").title()} is required'
                logger.warning(f"Missing required field: {field}")
                if request.is_json or request.content_type == 'application/json':
                    return jsonify({
                        'success': False, 
                        'message': error_message
                    }), 400
                else:
                    flash(error_message, 'error')
                    return redirect(url_for('main.communities'))
        
        # Generate unique submission ID
        submission_id = str(uuid.uuid4())
        logger.debug(f"Generated submission ID: {submission_id}")
        
        # Store submission temporarily
        temp_submissions_file = os.path.join(current_app.static_folder, 'temp_submissions.json')
        
        # Load existing submissions
        temp_submissions = {}
        if os.path.exists(temp_submissions_file):
            try:
                with open(temp_submissions_file, 'r') as f:
                    temp_submissions = json.load(f)
            except json.JSONDecodeError:
                current_app.logger.warning(f"Could not parse JSON from {temp_submissions_file}")
                temp_submissions = {}

        # Add new submission
        temp_submissions[submission_id] = {
            'data': form_data,
            'timestamp': datetime.now().isoformat(),
            'status': 'pending'
        }

        # Save updated submissions
        try:
            with open(temp_submissions_file, 'w') as f:
                json.dump(temp_submissions, f, indent=2)
        except Exception as e:
            current_app.logger.error(f"Error saving submissions: {e}")
            return jsonify({
                'success': False,
                'message': 'Failed to save submission. Please try again.'
            }), 500

        # Send confirmation email
        try:
            confirm_url = url_for('main.confirm_community', submission_id=submission_id, action='confirm', _external=True)
            reject_url = url_for('main.confirm_community', submission_id=submission_id, action='reject', _external=True)
            
            send_email(
                subject='Community Submission Confirmation',
                recipients=[form_data['email']],
                template='email/confirm_community.html',
                confirm_url=confirm_url,
                reject_url=reject_url,
                community_name=form_data['Name']
            )
            
            return jsonify({
                'success': True,
                'message': 'Thank you! Please check your email for confirmation.'
            })
            
        except Exception as e:
            current_app.logger.error(f"Error sending confirmation email: {e}")
            return jsonify({
                'success': False,
                'message': 'Failed to send confirmation email. Please try again.'
            }), 500

    except Exception as e:
        current_app.logger.error(f"Error processing community submission: {e}")
        return jsonify({
            'success': False,
            'message': 'An error occurred. Please try again.'
        }), 500

@bp.route('/confirm-community/<submission_id>/<action>', methods=['GET'])
def confirm_community(submission_id, action):
    """Handle community confirmation from email buttons"""
    try:
        # Load temporary submissions
        temp_submissions_file = os.path.join(current_app.static_folder, 'temp_submissions.json')
        
        if not os.path.exists(temp_submissions_file):
            return "Submission not found", 404
            
        with open(temp_submissions_file, 'r') as f:
            temp_submissions = json.load(f)
        
        # Get submission_id from URL parameters
        submission_id = request.args.get('submission_id')
        if not submission_id:
            return "Missing submission_id parameter", 400
            
        if submission_id not in temp_submissions:
            return "Submission not found", 404
            
        community_data = temp_submissions[submission_id]
        
        if action == 'accept':
            # Read existing communities
            json_file = os.path.join(current_app.static_folder, 'data', 'communities_with_logos.json')
            
            communities = []
            if os.path.exists(json_file):
                with open(json_file, 'r', encoding='utf-8') as f:
                    communities = json.load(f)
            
            # Create new community entry
            new_community = {
                "Name": community_data.get('Name', ''),
                "Sport": community_data.get('Sport', ''),
                "email": community_data.get('email', ''),
                "website": community_data.get('website', ''),
                "Location": community_data.get('Location', ''),
                "Cost": community_data.get('Cost', ''),
                "Int/Dutch": community_data.get('Int/Dutch', 'Both'),
                "Student-based": community_data.get('Student-based', 'No'),
                "image_url": community_data.get('image_url', '')
            }
            
            # Add new community to the list
            communities.append(new_community)
            
            # Save updated communities
            os.makedirs(os.path.dirname(json_file), exist_ok=True)
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(communities, f, indent=2, ensure_ascii=False)
            
            # Remove from temporary submissions
            del temp_submissions[submission_id]
            with open(temp_submissions_file, 'w') as f:
                json.dump(temp_submissions, f, indent=2)
            
            current_app.logger.info(f"Community '{new_community['Name']}' added successfully")
            return f"<h1>Community Added Successfully!</h1><p>The community '{new_community['Name']}' has been added to the platform.</p>"
            
        elif action == 'reject':
            # Remove from temporary submissions
            del temp_submissions[submission_id]
            with open(temp_submissions_file, 'w') as f:
                json.dump(temp_submissions, f, indent=2)
            
            current_app.logger.info(f"Community submission '{community_data.get('Name', 'Unknown')}' rejected")
            return f"<h1>Community Rejected</h1><p>The community submission has been rejected and removed.</p>"
            
        return "Invalid action", 400
        
    except Exception as e:
        current_app.logger.error(f"Error in community confirmation: {e}")
        return f"An error occurred: {str(e)}", 500

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
        user_points = current_user.points
        
        # Count how many users have more points than the current user
        higher_ranked_users = db.session.query(db.func.count(User.id)).filter(
            User.id != current_user.id,
            User.is_public == True
        ).join(
            CompletedChallenge,
            User.id == CompletedChallenge.user_id
        ).group_by(
            User.id
        ).having(
            db.func.sum(CompletedChallenge.points_earned) > user_points
        ).count()
        
        user_rank = higher_ranked_users + 1  # User's rank (1-based)
            
        user_progress = {
            'completed_challenges': completed,
            'total_points': user_points,
            'rank': user_rank,
            'daily_streak': current_user.daily_streak
        }
    
    # Import weekly challenge utilities
    from utils.scheduler import get_current_week_info, create_user_weekly_order, populate_weekly_challenge_set
    
    # Get current week info
    current_week = get_current_week_info()
    
    # Check if we need to populate the weekly challenge set
    populate_weekly_challenge_set()
    
    # Check if this is the user's first visit this week and handle weekly setup
    show_habit_modal = False
    if current_user.is_authenticated and current_user.is_first_visit_of_week():
        # Create user's weekly challenge order if it doesn't exist
        create_user_weekly_order(current_user.id)
        
        # Check if user completed challenges last week for habit selection
        prev_week_challenges = current_user.get_previous_week_completed_challenges()
        if prev_week_challenges:
            show_habit_modal = True
        
        # Update the user's last visit week
        current_user.update_last_visit_week()
    
    # Get in-progress challenges for the current user if authenticated
    in_progress_challenges = []
    in_progress_count = 0
    if current_user.is_authenticated:
        # Get challenges that are currently in progress (from UserChallenge with status 'pending')
        in_progress = UserChallenge.query.filter_by(
            user_id=current_user.id,
            status='pending',
            week_number=current_week['week_number'],
            year=current_week['year']
        ).all()
        
        in_progress_count = len(in_progress)
        in_progress_challenge_ids = [c.challenge_id for c in in_progress]
        in_progress_challenges = Challenge.query.filter(Challenge.id.in_(in_progress_challenge_ids)).all() if in_progress_challenge_ids else []
    
    # Get challenge regeneration timers - now user specific
    now = datetime.utcnow()
    
    # Get user-specific regeneration timers if authenticated, or empty list if not
    regeneration_timers = []
    if current_user.is_authenticated:
        regeneration_timers = ChallengeRegeneration.query.filter_by(user_id=current_user.id).all()
    
    # Debug: Print all regeneration timers in detail
    print("\n==== REGENERATION TIMER DEBUGGING ====")
    print(f'Found {len(regeneration_timers)} regeneration timers at {now}:')
    for timer in regeneration_timers:
        time_remaining = (timer.regenerate_at - now).total_seconds()
        status = 'ACTIVE' if time_remaining > 0 else 'EXPIRED'
        print(f'  - {timer.difficulty} slot {timer.slot_number}: {status} - regenerates in {time_remaining:.0f} seconds - at {timer.regenerate_at}')
    
    # Organize regeneration timers by difficulty and slot number
    regeneration_by_slot = {}
    for timer in regeneration_timers:
        key = (timer.difficulty, timer.slot_number)
        regeneration_by_slot[key] = timer
    
    # Never force test timers in production
    force_test_timers = False
    
    # Debug information about in-progress challenges
    if current_user.is_authenticated:
        print("\n==== DEBUG: IN-PROGRESS CHALLENGES ====")
        for challenge in in_progress_challenges:
            print(f"  - Challenge {challenge.id}: {challenge.title} ({challenge.difficulty})")
        print(f"Total in-progress: {len(in_progress_challenges)}")
    
    if force_test_timers:
        print("\n==== FORCING TEST TIMERS ====")
        # Create test timers if none exist or force them to be active
        test_regeneration_time = now + timedelta(minutes=2)
        for diff, slots in {'E': 3, 'M': 2, 'H': 1}.items():
            for slot in range(1, slots + 1):
                key = (diff, slot)
                timer = regeneration_by_slot.get(key)
                if timer:
                    # Update existing timer to be active
                    timer.regenerate_at = test_regeneration_time
                    print(f'  - Updated timer for {diff} slot {slot} to regenerate in 2 minutes')
                else:
                    # Create new timer with user_id
                    new_timer = ChallengeRegeneration(
                        user_id=current_user.id,
                        difficulty=diff,
                        slot_number=slot,
                        regenerate_at=test_regeneration_time
                    )
                    db.session.add(new_timer)
                    regeneration_by_slot[key] = new_timer
                    print(f'  - Created timer for {diff} slot {slot} to regenerate in 2 minutes')
        db.session.commit()
        
    # Print active timer details
    print("\n==== ACTIVE TIMERS FOR TEMPLATE RENDERING ====")
    active_timer_count = 0
    for key, timer in regeneration_by_slot.items():
        difficulty, slot = key
        time_remaining = (timer.regenerate_at - now).total_seconds()
        if time_remaining > 0:
            active_timer_count += 1
            print(f'  - Active timer: {difficulty} slot {slot}: regenerates in {time_remaining:.0f} seconds')
    print(f'Total active timers: {active_timer_count}')
    print("====================================")
    
    # Prepare challenges by difficulty with weekly ordering
    challenges_by_difficulty = {
        'E': [],
        'M': [],
        'H': []
    }
    
    # Define display counts for each difficulty
    display_counts = {'E': 3, 'M': 2, 'H': 1}
    
    # Define weekly caps for each difficulty
    weekly_caps = {'E': 9, 'M': 6, 'H': 3}
    
    if current_user.is_authenticated:
        # Get the user's weekly challenge counts
        weekly_counts = current_user.get_weekly_challenge_counts()
        
        # For each difficulty level, prepare the slots
        for difficulty in ['E', 'M', 'H']:
            # Check if user has reached the weekly cap for this difficulty
            if weekly_counts.get(difficulty, 0) >= weekly_caps[difficulty]:
                # User has reached the cap, show 'All done for this week!'
                for slot_number in range(1, display_counts[difficulty] + 1):
                    challenges_by_difficulty[difficulty].append({
                        'challenge': None,
                        'regenerating': False,
                        'time_remaining': None,
                        'slot_number': slot_number,
                        'all_done': True  # Flag to show 'All done for this week!' message
                    })
                continue
            
            # Get the user's weekly order for this difficulty
            user_order = UserWeeklyOrder.query.filter_by(
                user_id=current_user.id,
                week_number=current_week['week_number'],
                year=current_week['year'],
                difficulty=difficulty
            ).order_by(UserWeeklyOrder.order_position).all()
            
            # Get challenges that the user has already attempted this week
            attempted_challenges = UserChallenge.query.filter_by(
                user_id=current_user.id,
                week_number=current_week['week_number'],
                year=current_week['year']
            ).all()
            attempted_ids = [c.challenge_id for c in attempted_challenges if c.status != 'abandoned']
            
            # Filter out challenges that are already in progress
            in_progress_ids = [c.id for c in in_progress_challenges]
            
            # Find the next challenges to display (that aren't attempted or in progress)
            available_challenges = []
            for order in user_order:
                if order.challenge_id not in attempted_ids and order.challenge_id not in in_progress_ids:
                    challenge = Challenge.query.get(order.challenge_id)
                    if challenge:
                        available_challenges.append(challenge)
                        if len(available_challenges) >= display_counts[difficulty]:
                            break
            
            # Fill slots with available challenges
            for slot_number in range(1, display_counts[difficulty] + 1):
                # First, check if there's a regeneration timer active for this slot
                timer_key = (difficulty, slot_number)
                regen_timer = regeneration_by_slot.get(timer_key)
                
                # Show the timer if it's active and not expired
                if regen_timer and regen_timer.regenerate_at > now:
                    # Calculate remaining time
                    time_remaining = (regen_timer.regenerate_at - now).total_seconds()
                    hours = int(time_remaining // 3600)
                    minutes = int((time_remaining % 3600) // 60)
                    
                    # Format time remaining - only show hours and minutes
                    if hours > 0:
                        time_str = f"{hours}h {minutes}m"
                    else:
                        time_str = f"{minutes}m"
                        
                    # Show regeneration timer in this specific slot
                    print(f'Displaying regeneration timer for {difficulty} slot {slot_number}, expires at {regen_timer.regenerate_at}')
                    challenges_by_difficulty[difficulty].append({
                        'challenge': None,
                        'regenerating': True,
                        'time_remaining': time_str,
                        'regenerate_at': regen_timer.regenerate_at.isoformat(),
                        'slot_number': slot_number
                    })
                # If no timer or timer expired, try to show a challenge if available
                elif slot_number <= len(available_challenges):
                    challenge = available_challenges[slot_number - 1]
                    challenges_by_difficulty[difficulty].append({
                        'challenge': challenge,
                        'regenerating': False,
                        'time_remaining': None,
                        'slot_number': slot_number
                    })
                else:
                    # Empty slot with no timer and no challenge available
                    challenges_by_difficulty[difficulty].append({
                        'challenge': None,
                        'regenerating': False,
                        'time_remaining': None,
                        'slot_number': slot_number
                    })
    else:
        # For non-authenticated users, just show empty slots
        for difficulty in ['E', 'M', 'H']:
            for slot_number in range(1, display_counts[difficulty] + 1):
                challenges_by_difficulty[difficulty].append({
                    'challenge': None,
                    'regenerating': False,
                    'time_remaining': None,
                    'slot_number': slot_number
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

# Challenge API routes are now in api.py

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

@bp.route('/submit_community_suggestion', methods=['POST'])
def submit_community_suggestion():
    community_name = request.form.get('community_name')
    email = request.form.get('email')
    message = request.form.get('message')

    # Here you can handle saving or emailing the suggestion
    print(f"Suggestion received: {community_name} - {email} - {message}")

    # Redirect back to the communities page with success flag
    return redirect(url_for('main.communities', suggestion_sent='True'))
