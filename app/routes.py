
from datetime import datetime, timedelta
import json
import math
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from . import db
from .models import (
    User,
    Challenge,
    CompletedChallenge,
    ChallengeRegeneration,
    UserChallenge,
    WeeklyChallengeSet,
    UserWeeklyOrder,
    WeeklyHabitChallenge,
    FunFact,
    FriendChallengeLink,
    ChallengeOfTheWeek
)
from .forms import LoginForm, RegistrationForm
from .email_handler import send_email
import logging
import os
import json as _json
from sqlalchemy import func
import uuid
import re
from app.utils.game_helpers import get_in_progress_challenges
from utils.scheduler import get_current_week_info, create_user_weekly_order, populate_weekly_challenge_set

bp = Blueprint('main', __name__)

def save_to_main_json(submission_id, submission_data):
    """Save a community submission to the main JSON file"""
    try:
        # Log the start of the save process
        community_name = submission_data['data'].get('Name', 'Unknown')
        current_app.logger.info(f"Attempting to save community: {community_name}")
        
        # Read existing communities
        json_file = os.path.join(current_app.static_folder, 'data', 'communities_with_logos.json')
        
        # Verify directory exists and is writable
        data_dir = os.path.dirname(json_file)
        if not os.path.exists(data_dir):
            try:
                os.makedirs(data_dir, exist_ok=True)
                current_app.logger.info(f"Created directory: {data_dir}")
            except Exception as e:
                current_app.logger.error(f"Failed to create directory: {e}")
                return False
        
        # Verify file permissions and read existing data
        if os.path.exists(json_file):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    communities = json.load(f)
                current_app.logger.info(f"Loaded {len(communities)} existing communities")
            except Exception as e:
                current_app.logger.error(f"Failed to read existing file: {e}")
                return False
        else:
            communities = []
            current_app.logger.info("Creating new communities file")
        
        # Create new community entry from the submission data
        new_community = {
            "Name": submission_data['data'].get('Name', ''),
            "Sport": submission_data['data'].get('Sport', ''),
            "email": submission_data['data'].get('email', ''),
            "website": submission_data['data'].get('website', ''),
            "Address": submission_data['data'].get('Address', ''),
            "Cost": submission_data['data'].get('Cost', ''),
            "Int/Dutch": submission_data['data'].get('Int/Dutch', 'Both'),
            "Student-based": submission_data['data'].get('Student-based', 'No'),
            "image_url": submission_data['data'].get('image_url', '')
        }
        
        # Add new community to the list
        communities.append(new_community)
        current_app.logger.info(f"Added community: {new_community['Name']}")
        
        # Save updated communities
        try:
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(communities, f, indent=2, ensure_ascii=False)
            current_app.logger.info(f"Successfully saved community '{new_community['Name']}' to {json_file}")
            return True
        except Exception as e:
            current_app.logger.error(f"Failed to write to file {json_file}: {e}")
            return False
        
    except Exception as e:
        current_app.logger.error(f"Error saving to main JSON: {e}")
        return False

print(">>> THIS routes.py LOADED <<<")

# Helper function to format time remaining for regeneration timers
def format_time_remaining(seconds):
    """Format seconds into a human-readable string (e.g., '2h 30m' or '45m')"""
    if seconds is None:
        return None
        
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"

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
        # Get all form data
        form_data = request.form.to_dict()
        logger.debug(f"Processed form data: {form_data}")
        
# All fields are optional, use get() with default empty string
        form_data = request.form.to_dict()
        logger.debug(f"Processed form data: {form_data}")
        
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
        else:
            # Create empty file if it doesn't exist
            try:
                os.makedirs(os.path.dirname(temp_submissions_file), exist_ok=True)
                with open(temp_submissions_file, 'w') as f:
                    json.dump({}, f)
                current_app.logger.info(f"Created empty temp_submissions.json file")
            except Exception as e:
                current_app.logger.error(f"Failed to create temp_submissions.json: {e}")
                return jsonify({
                    'success': False,
                    'message': 'Failed to create temporary submissions file. Please try again.'
                }), 500
        
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

        # Add submission_id to form_data before saving
        form_data['submission_id'] = submission_id

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

        # Send confirmation email if email configuration is available
        try:
            if current_app.config.get('SMTP_SERVER') and current_app.config.get('EMAIL_USER'):
                # Get base URL from config or use current request host
                base_url = current_app.config.get('BASE_URL', request.host_url.rstrip('/'))
                
                # Generate confirmation URLs manually
                confirm_url = f"{base_url}/confirm-community/{submission_id}/accept"
                reject_url = f"{base_url}/confirm-community/{submission_id}/reject"
                
                # Add confirmation URLs to form data
                form_data['confirm_url'] = confirm_url
                form_data['reject_url'] = reject_url
                
                # Send email with confirmation links
                if not send_email(form_data, email_type='community_submission'):
                    current_app.logger.error("Failed to send confirmation email")
                    flash('An error occurred sending the confirmation email. Please try again.', 'error')
                    return redirect(url_for('main.communities'))
                flash('Thank you! Please check your email for confirmation.', 'success')
            else:
                flash('Thank you! Your submission has been received.', 'success')
        except Exception as e:
            current_app.logger.error(f"Error sending confirmation email: {e}")
            flash('Thank you! Your submission has been received.', 'success')

        return redirect(url_for('main.communities'))
            
    except Exception as e:
        current_app.logger.error(f"Error processing community submission: {e}")
        return jsonify({
            'success': False,
            'message': 'An error occurred. Please try again.'
        }), 500

@bp.route('/confirm-community/<submission_id>/<action>', methods=['GET'])
def confirm_community(submission_id, action):
    """Handle community submission confirmation"""
    try:
        # Log the incoming request
        current_app.logger.info(f"Received confirmation request: ID={submission_id}, action={action}")
        
        # Load temporary submissions
        temp_submissions_file = os.path.join(current_app.static_folder, 'temp_submissions.json')
        
        if not os.path.exists(temp_submissions_file):
            current_app.logger.error(f"Temporary submissions file not found: {temp_submissions_file}")
            return jsonify({
                "error": "Temporary submissions file not found",
                "status": "error"
            }), 404

        try:
            with open(temp_submissions_file, 'r') as f:
                temp_submissions = json.load(f)
        except json.JSONDecodeError as e:
            current_app.logger.error(f"Error reading submissions file: {e}")
            return jsonify({
                "error": "Error reading submissions file",
                "status": "error"
            }), 500

        if submission_id not in temp_submissions:
            current_app.logger.error(f"Submission ID not found: {submission_id}")
            return jsonify({
                "error": "Submission not found",
                "status": "error"
            }), 404

        community_data = temp_submissions[submission_id]
        community_name = community_data['data'].get('Name', 'Unknown')
        
        if action == 'accept':
            current_app.logger.info(f"Attempting to accept community: {community_name}")
            # Save to main communities file
            if save_to_main_json(submission_id, community_data):
                # Remove from temp submissions
                try:
                    del temp_submissions[submission_id]
                    with open(temp_submissions_file, 'w') as f:
                        json.dump(temp_submissions, f, indent=2)
                    current_app.logger.info(f"Successfully accepted community: {community_name}")
                    # Redirect to communities page after successful acceptance
                    return redirect(url_for('main.communities', suggestion_sent=True))
                except Exception as e:
                    current_app.logger.error(f"Error removing accepted submission: {e}")
                    return jsonify({
                        "error": "Failed to remove accepted submission",
                        "status": "error"
                    }), 500
            else:
                current_app.logger.error(f"Failed to save community to main file: {community_name}")
                return jsonify({
                    "error": "Failed to save community",
                    "status": "error"
                }), 500

        elif action == 'reject':
            current_app.logger.info(f"Attempting to reject community: {community_name}")
            # Remove from temporary submissions
            try:
                del temp_submissions[submission_id]
                with open(temp_submissions_file, 'w') as f:
                    json.dump(temp_submissions, f, indent=2)
                current_app.logger.info(f"Successfully rejected community: {community_name}")
                # Redirect to communities page after successful rejection
                return redirect(url_for('main.communities'))
            except Exception as e:
                current_app.logger.error(f"Error removing rejected submission: {e}")
                return jsonify({
                    "error": "Failed to remove submission",
                    "status": "error"
                }), 500

        return jsonify({
            "error": "Invalid action",
            "status": "error"
        }), 400

    except Exception as e:
        current_app.logger.error(f"Error in community confirmation: {e}")
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "message": str(e)
        }), 500

@bp.route('/communities')
def communities():
    """Display communities page with filtering and pagination"""
    try:
        # Load communities data
        json_file = os.path.join(current_app.static_folder, 'data', 'communities_with_logos.json')
        
        if not os.path.exists(json_file):
            # Create empty file if it doesn't exist
            os.makedirs(os.path.dirname(json_file), exist_ok=True)
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
            data = []
        else:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

        selected_sport = request.args.get("sport", "")
        selected_cost_range = request.args.get("cost", "")
        page = int(request.args.get("page", 1))
        per_page = 9

        # Check if suggestion was sent to show confirmation message
        suggestion_sent = request.args.get('suggestion_sent') == 'True'

        # Filter data
        filtered_data = []
        for item in data:
            if selected_sport and item.get("Sport") != selected_sport:
                continue
            if selected_cost_range and selected_cost_range != "":
                try:
                    cost_str = item.get("Cost", "0")
                    # Extract numeric value from cost string
                    cost_match = re.search(r'\d+', str(cost_str))
                    if cost_match:
                        cost = float(cost_match.group())
                        if '-' in selected_cost_range:
                            min_cost, max_cost = map(int, selected_cost_range.split('-'))
                        else:
                            # Handle "200+" case
                            min_cost = int(selected_cost_range.replace('+', ''))
                            max_cost = 9999
                        
                        if not (min_cost <= cost <= max_cost):
                            continue
                except:
                    # If we can't parse the cost, include it anyway
                    pass
            filtered_data.append(item)

        # Pagination
        total_items = len(filtered_data)
        total_pages = math.ceil(total_items / per_page) if total_items > 0 else 1
        start = (page - 1) * per_page
        end = start + per_page
        paginated_data = filtered_data[start:end]

        # Get unique sports for filter dropdown
        sports = sorted(set(item.get("Sport", "") for item in data if item.get("Sport")))
        
        # Cost ranges for filter
        cost_ranges = {
            "0-50": "0-50",
            "50-100": "50-100", 
            "100-200": "100-200",
            "200+": "200+"
        }

        return render_template("communities.html",
                               communities=paginated_data,
                               sports=sports,
                               selected_sport=selected_sport,
                               cost_ranges=cost_ranges,
                               selected_cost_range=selected_cost_range,
                               page=page,
                               total_pages=total_pages,
                               suggestion_sent=suggestion_sent)
    
    except Exception as e:
        current_app.logger.error(f"Error loading communities page: {e}")
        flash('Error loading communities. Please try again.', 'error')
        return render_template("communities.html",
                               communities=[],
                               sports=[],
                               selected_sport="",
                               cost_ranges={},
                               selected_cost_range="",
                               page=1,
                               total_pages=1,
                               suggestion_sent=False)

# Static Pages
@bp.route('/research')
def research(): return render_template('research.html')

@bp.route('/publications')
def publications(): return render_template('publications.html')

@bp.route('/research/stayfine')
def stayfine(): return render_template('research/stay_fine.html')

@bp.route('/research/stride4')
def stride4(): return render_template('research/stride-4.html')

@bp.route('/research/brain_adaptations')
def brain_adaptations(): return render_template('research/brain_adaptations.html')

@bp.route('/research/leopard_predict')
def leopard_predict(): return render_template('research/leopard_predict.html')

# API Endpoints for Game Actions
@bp.route('/api/challenges/<int:challenge_id>/complete', methods=['POST'])
@login_required
def complete_challenge(challenge_id):
    """Complete a challenge, record it, and optionally return a fun fact."""
    try:
        challenge = Challenge.query.get_or_404(challenge_id)
        if CompletedChallenge.query.filter_by(user_id=current_user.id, challenge_id=challenge_id).first():
            flash('Already completed this challenge.', 'info')
            return redirect(url_for('main.game', section='challenges'))
        uc = UserChallenge.query.filter_by(user_id=current_user.id, challenge_id=challenge_id, status='pending').first()
        if uc:
            uc.status = 'completed'
            uc.completed_at = datetime.utcnow()
        else:
            uc = UserChallenge(
                user_id=current_user.id,
                challenge_id=challenge_id,
                status='completed',
                week_number=datetime.utcnow().isocalendar()[1],
                year=datetime.utcnow().year,
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            )
            db.session.add(uc)
        comp = CompletedChallenge(
            user_id=current_user.id,
            challenge_id=challenge_id,
            points_earned=challenge.points,
            completed_at=datetime.utcnow()
        )
        db.session.add(comp)
        fun_fact = FunFact.get_random_fact()
        if fun_fact:
            fun_fact.times_shown += 1
            fun_fact.last_shown = datetime.utcnow()
        db.session.commit()
        flash('Challenge completed successfully!', 'success')
        if fun_fact:
            return render_template('game.html', section='challenges', fun_fact=fun_fact)
        return redirect(url_for('main.game', section='challenges'))
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error completing challenge: {e}")
        flash('Error completing challenge.', 'error')
        return redirect(url_for('main.game', section='challenges'))

@bp.route('/api/challenges/<int:challenge_id>/abandon', methods=['POST'])
@login_required
def abandon_challenge(challenge_id):
    """Set cooldown on abandon and lock slot."""
    uc = UserChallenge.query.filter_by(user_id=current_user.id, challenge_id=challenge_id, status='pending').first_or_404()
    uc.status = 'abandoned'
    uc.cooldown_until = datetime.utcnow() + timedelta(hours=2)
    db.session.commit()
    flash('Challenge abandoned. Slot locked for 2 hours.', 'warning')
    return redirect(url_for('main.game', section='challenges'))

# API endpoint to start (add to in-progress) a challenge
@bp.route('/api/challenges/<int:challenge_id>/start', methods=['POST'])
@login_required
def start_challenge(challenge_id):
    """Mark a challenge as in-progress (pending), enforcing the 2-slot limit."""
    try:
        week = get_current_week_info()
        in_prog, count = get_in_progress_challenges(
            current_user.id,
            week['week_number'],
            week['year']
        )
        if count >= 2:
            flash('You already have 2 challenges in progress!', 'warning')
            return redirect(url_for('main.game', section='challenges'))

        uc = UserChallenge.query.filter_by(
            user_id=current_user.id,
            challenge_id=challenge_id,
            status='pending'
        ).first()

        if not uc:
            uc = UserChallenge(
                user_id=current_user.id,
                challenge_id=challenge_id,
                status='pending',
                week_number=week['week_number'],
                year=week['year'],
                started_at=datetime.utcnow()
            )
            db.session.add(uc)

        db.session.commit()
        flash('Challenge started!', 'success')

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error starting challenge: {e}")
        
        # Provide more specific error messages based on the exception
        if 'UNIQUE constraint failed' in str(e):
            flash('You have already started this challenge this week.', 'error')
        elif 'FOREIGN KEY constraint failed' in str(e):
            flash('Challenge not found. Please try a different challenge.', 'error')
        elif 'database is locked' in str(e):
            flash('Database is busy. Please wait a moment and try again.', 'error')
        else:
            flash('Could not start challenge. Please try again.', 'error')

    return redirect(url_for('main.game', section='challenges'))


# Profile Update Route (form submission)
@bp.route('/update_profile', methods=['POST'])
@login_required
def update_profile_form():
    """Handle profile form submission from profile tab."""
    if 'top_sport_category' in request.form:
        current_user.top_sport_category = request.form.get('top_sport_category')
        current_user.last_sport_update = datetime.utcnow()
        db.session.commit()
        flash('Profile updated successfully!', 'success')
    return redirect(url_for('main.game', section='profile'))

# Auth Route for Login and Signup
@bp.route('/auth', methods=['GET', 'POST'])
def auth():
    # Initialize forms
    login_form = LoginForm()
    signup_form = RegistrationForm()
    
    if request.method == 'POST':
        form_type = request.form.get('form_type')
        
        # Handle login form submission
        if form_type == 'login':
            username = request.form.get('username')
            password = request.form.get('password')
            
            try:
                user = User.query.filter_by(username=username).first()
                if user and user.check_password(password):
                    login_user(user)
                    flash('Login successful!', 'success')
                    # Redirect to the challenges section of the game page
                    return redirect(url_for('main.game', section='challenges'))
                else:
                    flash('Invalid username or password.', 'error')
            except Exception as e:
                current_app.logger.error(f"Login error: {str(e)}")
                flash('An error occurred during login. Please try again.', 'error')
        
        # Handle signup form submission
        elif form_type == 'signup':
            username = request.form.get('username')
            password = request.form.get('password')
            confirm = request.form.get('confirm_password')
            
            if password != confirm:
                flash('Passwords do not match.', 'error')
                return render_template('game/auth.html', login_form=login_form, signup_form=signup_form)
                
            # Check if username already exists
            try:
                existing_user = User.query.filter_by(username=username).first()
                if existing_user:
                    flash('Username already taken.', 'error')
                    return render_template('game/auth.html', login_form=login_form, signup_form=signup_form)
            except Exception as e:
                current_app.logger.error(f"Error checking existing user: {str(e)}")
                flash('Database error. Please try again.', 'error')
                return render_template('game/auth.html', login_form=login_form, signup_form=signup_form)
            
            # Create new user
            try:
                # Create a new user object
                new_user = User(username=username)
                new_user.set_password(password)
                
                # Generate unique backup and personal codes if the columns exist
                try:
                    new_user.generate_backup_code()
                    new_user.generate_personal_code()
                    current_app.logger.info(f"Generated backup and personal codes for user {username}")
                except Exception as e:
                    current_app.logger.warning(f"Could not generate backup and personal codes: {str(e)}")
                    # Continue with user creation even if the codes can't be generated
                
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
    
    # GET request or form validation failed
    # For direct access to auth page, redirect to game page with auth section
    if request.method == 'GET':
        return redirect(url_for('main.game', section='auth'))
    
    # For failed form validation, show the game page with auth section
    return redirect(url_for('main.game', section='auth'))

# Friend Challenge Completion Route
@bp.route('/challenge/<int:challenge_id>/complete-with-friend', methods=['POST'])
@login_required
def complete_challenge_with_friend(challenge_id):
    # Get the friend's personal code from the form
    friend_code = request.form.get('friend_code')
    
    if not friend_code:
        flash('Friend code is required.', 'error')
        return redirect(url_for('main.game', section='challenges'))
    
    # Find the friend by personal code
    friend = User.query.filter_by(personal_code=friend_code).first()
    
    if not friend:
        flash('Invalid friend code. Please check and try again.', 'error')
        return redirect(url_for('main.game', section='challenges'))
    
    if friend.id == current_user.id:
        flash('You cannot complete a challenge with yourself.', 'error')
        return redirect(url_for('main.game', section='challenges'))
    
    # Get the challenge
    challenge = Challenge.query.get_or_404(challenge_id)
    
    # Check if the user has this challenge in progress
    user_challenge = UserChallenge.query.filter_by(
        user_id=current_user.id,
        challenge_id=challenge_id,
        status='pending'
    ).first()
    
    if not user_challenge:
        flash('Challenge not found or not in progress.', 'error')
        return redirect(url_for('main.game', section='challenges'))
    
    try:
        # Create or update the friend challenge link
        existing_link = FriendChallengeLink.query.filter(
            ((FriendChallengeLink.user1_id == current_user.id) & (FriendChallengeLink.user2_id == friend.id)) |
            ((FriendChallengeLink.user1_id == friend.id) & (FriendChallengeLink.user2_id == current_user.id))
        ).filter_by(challenge_id=challenge_id).first()
        
        if existing_link:
            # Update the existing link
            if existing_link.user1_id == current_user.id:
                existing_link.user1_confirmed = True
            else:
                existing_link.user2_confirmed = True
                
            # If both users have confirmed, complete the challenge for both
            if existing_link.is_complete():
                # Complete the challenge for the current user
                user_challenge.status = 'completed'
                user_challenge.completed_at = datetime.utcnow()
                user_challenge.points_earned = challenge.points * 1.5  # 50% bonus for friend completion
                
                # Find and complete the challenge for the friend if they have it in progress
                friend_challenge = UserChallenge.query.filter_by(
                    user_id=friend.id,
                    challenge_id=challenge_id,
                    status='pending'
                ).first()
                
                if friend_challenge:
                    friend_challenge.status = 'completed'
                    friend_challenge.completed_at = datetime.utcnow()
                    friend_challenge.points_earned = challenge.points * 1.5  # 50% bonus for friend completion
                
                flash('Challenge completed with your friend! You both earned bonus points!', 'success')
            else:
                flash('Your completion has been recorded. Waiting for your friend to complete their part.', 'success')
        else:
            # Create a new friend challenge link
            new_link = FriendChallengeLink(
                challenge_id=challenge_id,
                user1_id=current_user.id,
                user2_id=friend.id,
                user1_confirmed=True,
                user2_confirmed=False,
                expires_at=datetime.utcnow() + timedelta(days=3)  # Link expires in 3 days
            )
            db.session.add(new_link)
            flash('Your completion has been recorded. Waiting for your friend to complete their part.', 'success')
        
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in friend challenge completion: {str(e)}")
        flash('An error occurred. Please try again.', 'error')
    
    return redirect(url_for('main.game', section='challenges'))

# Logout Route
@bp.route('/logout')
@login_required
def logout():
    """Log out the current user and redirect to game page."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.game'))

# Main Game Route
@bp.route('/game')
@bp.route('/game/<section>')
def game(section='challenges'):
    # Auth redirect
    if not current_user.is_authenticated and section not in ['leaderboard', None]:
        section = 'auth'

    # Leaderboards: all-time and weekly
    one_week_ago = datetime.utcnow() - timedelta(days=7)
    all_time_users = (
        db.session.query(
            User,
            func.coalesce(func.sum(CompletedChallenge.points_earned), 0).label('total_points')
        )
        .outerjoin(CompletedChallenge, User.id == CompletedChallenge.user_id)
        .filter(User.is_public == True)
        .group_by(User.id)
        .order_by(func.coalesce(func.sum(CompletedChallenge.points_earned), 0).desc())
        .limit(10)
        .all()
    )
    weekly_users = (
        db.session.query(
            User,
            func.coalesce(func.sum(CompletedChallenge.points_earned), 0).label('weekly_points')
        )
        .outerjoin(
            CompletedChallenge,
            (User.id == CompletedChallenge.user_id) & (CompletedChallenge.completed_at >= one_week_ago)
        )
        .filter(User.is_public == True)
        .group_by(User.id)
        .order_by(func.coalesce(func.sum(CompletedChallenge.points_earned), 0).desc())
        .limit(10)
        .all()
    )

    # Active challenge ID
    active_challenge_id = request.args.get('active', type=int)

    # User progress
    user_progress = None
    if current_user.is_authenticated:
        recent_completed = (
            CompletedChallenge.query
            .filter_by(user_id=current_user.id)
            .order_by(CompletedChallenge.completed_at.desc())
            .limit(5)
            .all()
        )
        user_pts = current_user.points or 0
        # Count users with higher points than the current user
        # Using a subquery to avoid the MultipleResultsFound error
        higher_ranked_query = (
            db.session.query(User.id)
            .join(CompletedChallenge, User.id == CompletedChallenge.user_id)
            .group_by(User.id)
            .having(func.sum(CompletedChallenge.points_earned) > user_pts)
        )
        higher_ranked = db.session.query(func.count()).select_from(higher_ranked_query.subquery()).scalar() or 0
        user_progress = {
            'completed_challenges': recent_completed,
            'total_points': user_pts,
            'rank': higher_ranked + 1,
        }

    # Weekly challenge setup
    current_week = get_current_week_info()
    current_app.logger.info("Weekly challenge setup")
    
    try:
        populate_weekly_challenge_set()
    except Exception as e:
        current_app.logger.warning(f"Error populating weekly challenge set: {str(e)}")
        db.session.rollback()
    
    if current_user.is_authenticated and current_user.is_first_visit_of_week():
        create_user_weekly_order(current_user.id)
        current_user.update_last_visit_week()
    
    # In-Progress Challenges
    in_progress, active_count = ([], 0)
    if current_user.is_authenticated:
        try:
            current_app.logger.info("Using in-progress challenges")
            in_progress, active_count = get_in_progress_challenges(
                current_user.id,
                current_week['week_number'],
                current_week['year']
            )
        except Exception as e:
            current_app.logger.warning(f"Error getting in-progress challenges: {str(e)}")
            db.session.rollback()
    
    # Build weekly slots: 4E, 3M, 2H
    display_slots = {'E': 4, 'M': 3, 'H': 2}
    challenges_by_difficulty = {'E': [], 'M': [], 'H': []}
    
    if current_user.is_authenticated:
        try:
            current_app.logger.info("Using weekly challenges")
            import random
            from app.models import WeeklyChallengeSet, Challenge
    
            weekly_challenges = WeeklyChallengeSet.query.filter_by(
                week_number=current_week['week_number'],
                year=current_week['year']
            ).all()
    
            challenges_pool = {'E': [], 'M': [], 'H': []}
    
            for wc in weekly_challenges:
                challenge = Challenge.query.get(wc.challenge_id)
                if challenge:
                    challenges_pool[wc.difficulty].append(challenge)
    
            for diff, slots in display_slots.items():
                selected = random.sample(challenges_pool[diff], min(slots, len(challenges_pool[diff])))
                for ch in selected:
                    challenges_by_difficulty[diff].append({'challenge': ch, 'all_done': False})
    
                while len(challenges_by_difficulty[diff]) < slots:
                    challenges_by_difficulty[diff].append({'challenge': None, 'all_done': False})
        except Exception as e:
            current_app.logger.warning(f"Error building weekly challenges: {str(e)}")
            db.session.rollback()
            for diff, slots in display_slots.items():
                for _ in range(slots):
                    challenges_by_difficulty[diff].append({'challenge': None, 'all_done': False})
    
    # Final context for template
    challenges = {
        'in_progress': in_progress,
        'E': challenges_by_difficulty['E'],
        'M': challenges_by_difficulty['M'],
        'H': challenges_by_difficulty['H'],
    }
    
    print("DEBUG: challenges keys →", challenges.keys())
    print("DEBUG: in_progress contents →", challenges.get('in_progress'))
    
    return render_template(
        'game.html',
        section=section,
        top_users=all_time_users,
        weekly_users=weekly_users,
        challenges=challenges,
        active_challenge_id=active_challenge_id,
        active_count=active_count,
        user_progress=user_progress,
        login_form=(LoginForm() if section == 'auth' else None),
        signup_form=(RegistrationForm() if section == 'auth' else None)
    )
