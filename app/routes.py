from datetime import datetime, timedelta
import json
import math
import sys
import random
from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify, abort, current_app, session
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from . import db
from .models import User, Challenge, CompletedChallenge, UserChallenge, \
    ChallengeRegeneration, WeeklyChallengeSet, FriendChallengeLink, \
    FriendTokenUsage, FunFact, Notification, WeeklyHabitChallenge, \
    UserWeeklyOrder, ChallengeOfTheWeek
from .forms import LoginForm, RegistrationForm
from .email_handler import send_email
import logging
import os
import json as _json
from sqlalchemy import func, text
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
        json_file = os.path.join(current_app.static_folder, 'data', 'communities.json')
        
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
        # Validate email configuration
        if not current_app.config.get('EMAIL_USER'):
            return jsonify({
                'success': False,
                'message': 'Email configuration is not set up. Please contact the administrator.'
            }), 500
            
        # Get form data
        form_data = {
            'Name': request.form.get('Name'),
            'email': request.form.get('email'),
            'Address': request.form.get('Address'),
            'Sport': request.form.get('Sport'),
            'website': request.form.get('website'),
            'image_url': request.form.get('image_url'),
            'Cost': request.form.get('Cost'),
            'Int/Dutch': request.form.get('Int/Dutch'),
            'Student-based': request.form.get('Student-based')
        }
        
        # Validate required fields
        required_fields = ['Name', 'email', 'Sport']
        for field in required_fields:
            if not form_data.get(field):
                return jsonify({
                    'success': False, 
                    'message': f'{field.replace("_", " ").title()} is required'
                }), 400
        
        # Send email
        if send_email(form_data, 'community_submission'):
            return jsonify({
                'success': True, 
                'message': 'Community submission received successfully!'
            })
        else:
            return jsonify({
                'success': False, 
                'message': 'Failed to send submission. Please try again.'
            }), 500
            
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
        json_file = os.path.join(current_app.static_folder, 'data', 'communities.json')
        
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

@bp.route('/research/social_gym')
def social_gym(): return render_template('research/social_gym.html')

@bp.route('/research/synergistic')
def synergistic(): return render_template('research/synergistic.html')

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
            
        # Check if this is a friend-linked challenge
        friend_link = FriendChallengeLink.query.filter_by(challenge_id=challenge_id).filter(
            ((FriendChallengeLink.user1_id == current_user.id) | (FriendChallengeLink.user2_id == current_user.id)) &
            (FriendChallengeLink.user1_confirmed == True) & 
            (FriendChallengeLink.user2_confirmed == True) &
            (FriendChallengeLink.expired == False)
        ).first()
        
        points_multiplier = 1.0
        friend_id = None
        is_second_completer = False
        
        if friend_link:
            # This is a friend-linked challenge
            if friend_link.user1_id == current_user.id:
                friend_id = friend_link.user2_id
                friend_link.user1_completed = True
                friend_link.user1_completed_at = datetime.utcnow()
                # Check if friend already completed
                if friend_link.user2_completed:
                    is_second_completer = True
            else:
                friend_id = friend_link.user1_id
                friend_link.user2_completed = True
                friend_link.user2_completed_at = datetime.utcnow()
                # Check if friend already completed
                if friend_link.user1_completed:
                    is_second_completer = True
            
            # Set expiration for the other user to complete
            if not friend_link.completion_expires_at:
                friend_link.completion_expires_at = datetime.utcnow() + timedelta(hours=24)
            
            # Check if both users have completed the challenge
            if friend_link.user1_completed and friend_link.user2_completed:
                # Both completed - award bonus points to the first completer
                friend = User.query.get(friend_id)
                
                if is_second_completer:
                    # This user is the second to complete - give them 1.5x points right away
                    points_multiplier = 1.5
                    
                    # Also update the first completer's points
                    first_user_id = friend_id  # The friend was the first to complete
                    
                    # Find the first user's completed challenge record
                    first_user_completion = CompletedChallenge.query.filter_by(
                        user_id=first_user_id, 
                        challenge_id=challenge_id
                    ).first()
                    
                    if first_user_completion:
                        # Calculate and add the bonus points (0.5x)
                        bonus_points = int(challenge.points * 0.5)
                        first_user_completion.points_earned += bonus_points
                        
                        # Notify the first user about the bonus points
                        # This will be shown next time they log in
                        notification = Notification(
                            user_id=first_user_id,
                            message=f"Your friend completed the challenge! You earned {bonus_points} bonus points!",
                            created_at=datetime.utcnow()
                        )
                        db.session.add(notification)
                    
                    if friend:
                        flash(f"You and {friend.username} both completed the challenge! Bonus points awarded!", "success")
                else:
                    # This user is the first to complete - give them 1.0x points for now
                    flash("Challenge completed! Your friend has 24 hours to complete it for bonus points.", "success")
            else:
                flash("Challenge completed! Your friend has 24 hours to complete it for bonus points.", "success")
        
        # Update user challenge status
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
            
        # Record completion and points
        points_earned = int(challenge.points * points_multiplier)
        comp = CompletedChallenge(
            user_id=current_user.id,
            challenge_id=challenge_id,
            points_earned=points_earned,
            completed_at=datetime.utcnow()
        )
        db.session.add(comp)
        
        # Get a fun fact
        fun_fact = FunFact.get_random_fact()
        if fun_fact:
            fun_fact.times_shown += 1
            fun_fact.last_shown = datetime.utcnow()
        
        # Check for new achievements
        from app.models import UserAchievement, Achievement
        newly_earned_achievements = UserAchievement.check_achievements(current_user.id)
        
        # Get full achievement details for any newly earned achievements
        new_achievements_data = []
        for achievement_info in newly_earned_achievements:
            achievement = Achievement.query.filter_by(name=achievement_info['name']).first()
            if achievement:
                new_achievements_data.append({
                    'name': achievement.name,
                    'message': achievement.message,
                    'icon_type': achievement.icon_type,
                    'condition': achievement.condition
                })
            
        db.session.commit()
        
        if not friend_link:
            flash('Challenge completed successfully!', 'success')
            
        if fun_fact:
            # Redirect instead of rendering to ensure all required variables are included
            flash('Did you know? ' + fun_fact.fact, 'fun-fact')
        
        # If there are new achievements, store them in session for the frontend to display
        if new_achievements_data:
            session['new_achievements'] = new_achievements_data
            
        return redirect(url_for('main.game', section='challenges'))
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error completing challenge: {e}")
        flash('Error completing challenge.', 'error')
        return redirect(url_for('main.game', section='challenges'))

@bp.route('/challenges/<int:challenge_id>/abandon', methods=['POST'])
@login_required
def abandon_challenge(challenge_id):
    from flask import request, jsonify
    
    success = False
    message = ''
    
    try:
        # Get current week info
        from utils.scheduler import get_current_week_info
        current_week = get_current_week_info()
        
        # Find the user challenge
        uc = UserChallenge.query.filter_by(
            user_id=current_user.id, 
            challenge_id=challenge_id, 
            status='pending',
            week_number=current_week['week_number'],
            year=current_week['year']
        ).first()
        
        if not uc:
            message = 'Challenge not found or not in progress'
            flash(message, 'error')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': message})
            return redirect(url_for('main.game', section='challenges'))
            
        # Mark as abandoned
        uc.status = 'abandoned'
        
        # Check if this is a friend-linked challenge
        friend_link = FriendChallengeLink.query.filter_by(challenge_id=challenge_id).filter(
            ((FriendChallengeLink.user1_id == current_user.id) | (FriendChallengeLink.user2_id == current_user.id)) &
            (FriendChallengeLink.user1_confirmed == True) & 
            (FriendChallengeLink.user2_confirmed == True) &
            (FriendChallengeLink.expired == False)
        ).first()
        
        # Get the challenge details
        challenge = Challenge.query.get_or_404(challenge_id)
        
        # Find the order entry for this challenge
        order_entry = UserWeeklyOrder.query.filter_by(
            user_id=current_user.id,
            challenge_id=challenge_id,
            week_number=current_week['week_number'],
            year=current_week['year']
        ).first()
        
        if order_entry:
            # Get all entries for this user/week/difficulty, ordered
            all_entries = UserWeeklyOrder.query.filter_by(
                user_id=current_user.id,
                week_number=current_week['week_number'],
                year=current_week['year'],
                difficulty=order_entry.difficulty
            ).order_by(UserWeeklyOrder.order_position).all()
            
            if all_entries:
                # Get the maximum position in the queue
                max_position = max(e.order_position for e in all_entries)
                
                # Move the abandoned challenge to the end of the queue (one position after the current max)
                order_entry.order_position = max_position + 1
        
        if friend_link:
            # Mark the link as expired so it doesn't show up as a friend challenge anymore
            friend_link.expired = True
            
            # Get friend username for the notification
            friend_id = friend_link.user2_id if friend_link.user1_id == current_user.id else friend_link.user1_id
            friend = User.query.get(friend_id)
            
            if friend:
                message = f'Friend challenge with {friend.username} has been abandoned. It will now appear at the end of the rotation for this week.'
            else:
                message = 'Friend challenge has been abandoned. It will now appear at the end of the rotation for this week.'
        else:
            message = 'Challenge abandoned. It will now appear at the end of the rotation for this week.'
            
        flash(message, 'info')
        success = True
            
        # Commit all changes in a single transaction
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error abandoning challenge: {str(e)}")
        message = 'Error abandoning challenge.'
        flash(message, 'error')
        success = False

    # Handle AJAX requests differently than regular form submissions
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': success,
            'message': message,
            'redirect': url_for('main.game', section='challenges') if success else None
        })
    
    return redirect(url_for('main.game', section='challenges'))

# API endpoint to start (add to in-progress) a challenge
@bp.route('/api/challenges/<int:challenge_id>/start', methods=['POST'])
@login_required
def start_challenge(challenge_id):
    """Mark a challenge as in-progress (pending), enforcing limits on challenges per week and per difficulty."""
    try:
        # Get the challenge to check its difficulty
        challenge = Challenge.query.get(challenge_id)
        if not challenge:
            flash('Challenge not found. Please try a different challenge.', 'error')
            return redirect(url_for('main.game', section='challenges'))
            
        difficulty = challenge.difficulty
        
        # Check if user has reached their weekly limit for this difficulty
        weekly_challenge_counts = current_user.get_weekly_challenge_counts()
        weekly_challenge_caps = User.WEEKLY_CHALLENGE_CAPS  # Use the class variable
        
        if weekly_challenge_counts[difficulty] >= weekly_challenge_caps[difficulty]:
            flash(f'You have reached your weekly limit for {difficulty} challenges!', 'warning')
            return redirect(url_for('main.game', section='challenges'))
        
        # Get current week info
        week = get_current_week_info()
        
        # Get in-progress challenges
        in_prog, count = get_in_progress_challenges(
            current_user.id,
            week['week_number'],
            week['year']
        )
        
        # Check if user already has 2 challenges in progress
        if count >= 2:
            flash('You already have 2 challenges in progress!', 'warning')
            return redirect(url_for('main.game', section='challenges'))
        
        # Check if user already has a challenge of this difficulty in progress
        # when they only have 1 challenge left for the week
        in_progress_of_same_difficulty = 0
        for challenge_in_prog in in_prog:
            if Challenge.query.get(challenge_in_prog.challenge_id).difficulty == difficulty:
                in_progress_of_same_difficulty += 1
        
        remaining_challenges = weekly_challenge_caps[difficulty] - weekly_challenge_counts[difficulty]
        if in_progress_of_same_difficulty > 0 and remaining_challenges <= 1:
            flash(f'You can\'t have two {difficulty} challenges in progress when you only have {remaining_challenges} left for the week!', 'warning')
            return redirect(url_for('main.game', section='challenges'))

        # Check if challenge is already in progress
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
                return redirect(url_for('main.game', section='auth'))
                
            # Check if username already exists
            try:
                existing_user = User.query.filter_by(username=username).first()
                if existing_user:
                    flash('Username already taken.', 'error')
                    return redirect(url_for('main.game', section='auth'))
            except Exception as e:
                current_app.logger.error(f"Error checking existing user: {str(e)}")
                flash('Database error. Please try again.', 'error')
                return redirect(url_for('main.game', section='auth'))
            
            # Create new user
            try:
                current_app.logger.info(f"Attempting to create user with direct SQL: {username}")
                
                # Create user with direct SQL for maximum Supabase compatibility
                try:
                    # Hash the password
                    from werkzeug.security import generate_password_hash
                    password_hash = generate_password_hash(password)
                    
                    # Current time and week info
                    now = datetime.utcnow()
                    iso_calendar = now.isocalendar()
                    week_number = iso_calendar[1]  # ISO week number
                    year = iso_calendar[0]  # Year
                    
                    # First check if a user with this username already exists
                    # Use public schema explicitly for PostgreSQL
                    check_sql = "SELECT id FROM public.\"user\" WHERE username = :username"
                    result = db.session.execute(db.text(check_sql), {"username": username}).fetchone()
                    
                    if result:
                        flash('Username already taken.', 'error')
                        return redirect(url_for('main.game', section='auth'))
                    
                    # Insert user with minimal required fields
                    # Use public schema explicitly for PostgreSQL
                    sql = """
                    INSERT INTO public."user" (username, password_hash, created_at, is_public) 
                    VALUES (:username, :password_hash, :created_at, :is_public)
                    RETURNING id
                    """
                    
                    params = {
                        "username": username,
                        "password_hash": password_hash,
                        "created_at": now,
                        "is_public": True
                    }
                    
                    current_app.logger.info("Executing SQL insert")
                    result = db.session.execute(db.text(sql), params)
                    user_id = result.fetchone()[0]
                    db.session.commit()
                    
                    current_app.logger.info(f"User created with ID: {user_id}")
                    
                    # Now load the user and log them in
                    new_user = User.query.get(user_id)
                    if new_user:
                        # Generate personal and backup codes for the new user
                        new_user.generate_personal_code()
                        new_user.generate_backup_code()
                        db.session.commit()
                        
                        login_user(new_user)
                        flash('Account created successfully!', 'success')
                        return redirect(url_for('main.game', section='challenges'))
                    else:
                        flash('User was created but could not be loaded. Please try logging in.', 'warning')
                        return redirect(url_for('main.game', section='auth'))
                        
                except Exception as sql_err:
                    db.session.rollback()
                    current_app.logger.error(f"SQL error creating user: {str(sql_err)}")
                    import traceback
                    error_details = traceback.format_exc()
                    current_app.logger.error(error_details)
                    
                    # Check for PostgreSQL-specific errors
                    error_str = str(sql_err).lower()
                    if "duplicate key" in error_str or "already exists" in error_str:
                        flash('Username already taken.', 'error')
                    elif "permission denied" in error_str or "access denied" in error_str:
                        flash('Database permission error. Please contact administrator.', 'error')
                        current_app.logger.critical(f"SUPABASE PERMISSIONS ERROR: {error_str}")
                    elif "relation" in error_str and "does not exist" in error_str:
                        flash('Database schema error. Tables may not exist.', 'error')
                        current_app.logger.critical(f"SUPABASE SCHEMA ERROR: {error_str}")
                    else:
                        flash('Database error during registration. Please try again.', 'error')
                    
                    return redirect(url_for('main.game', section='auth'))
                    
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error during signup: {str(e)}")
                import traceback
                error_details = traceback.format_exc()
                current_app.logger.error(error_details)
                
                # Log detailed Supabase-specific information
                current_app.logger.critical(f"SUPABASE CONNECTION DETAILS (check these):\n" 
                                          f"Host: {os.environ.get('SUPABASE_DB_HOST')}\n"
                                          f"Port: {os.environ.get('SUPABASE_DB_PORT')}\n"
                                          f"DB Name: {os.environ.get('SUPABASE_DB_NAME')}\n"
                                          f"User: {os.environ.get('SUPABASE_DB_USER')}\n"
                                          f"Error: {str(e)}")
                
                # Provide more specific error messages based on the exception
                error_str = str(e).lower()
                if 'already exists' in error_str or 'unique constraint' in error_str or 'duplicate key' in error_str:
                    flash('This username is already taken. Please try a different one.', 'error')
                elif 'syntax error' in error_str:
                    flash('Database syntax error. Contact support.', 'error')
                elif 'schema' in error_str or 'relation' in error_str:
                    flash('Database schema error. Contact support.', 'error')
                elif 'permission' in error_str or 'access' in error_str:
                    flash('Database permission error. Contact support.', 'error')
                elif 'connection' in error_str or 'connect' in error_str:
                    flash('Database connection error. Contact support.', 'error')
                else:
                    flash('An error occurred during signup. Please try again.', 'error')
    
    # GET request or form validation failed
    # For direct access to auth page, redirect to game page with auth section
    if request.method == 'GET':
        return redirect(url_for('main.game', section='auth'))
    
    # For failed form validation, show the game page with auth section
    return redirect(url_for('main.game', section='auth'))

# Friend Challenge Route

@bp.route('/challenge/<int:challenge_id>/complete-with-friend', methods=['POST'])
@login_required
def complete_challenge_with_friend(challenge_id):
    friend_code = request.form.get('friend_code')

    if not friend_code:
        flash('Friend code is required.', 'error')
        return redirect(url_for('main.game', section='challenges'))

    if friend_code == current_user.personal_code:
        flash("You can't complete a challenge with yourself.", 'error')
        return redirect(url_for('main.game', section='challenges'))

    # Ensure user has this challenge in progress
    challenge = Challenge.query.get_or_404(challenge_id)
    user_challenge = UserChallenge.query.filter_by(
        user_id=current_user.id, challenge_id=challenge_id, status='pending'
    ).first()

    if not user_challenge:
        flash("You haven't started this challenge.", 'error')
        return redirect(url_for('main.game', section='challenges'))

    # Check weekly friend token usage (limit 3)
    tokens_left = get_friend_tokens_left(current_user)
    if tokens_left <= 0:
        flash("You've used all 3 friend tokens this week.", 'error')
        return redirect(url_for('main.game', section='challenges'))

    # Lookup friend
    friend = User.query.filter_by(personal_code=friend_code).first()
    if not friend:
        flash("Invalid friend code.", 'error')
        return redirect(url_for('main.game', section='challenges'))

    if friend.id == current_user.id:
        flash("You can't use your own code.", 'error')
        return redirect(url_for('main.game', section='challenges'))

    # Friend must also have challenge in progress
    friend_challenge = UserChallenge.query.filter_by(
        user_id=friend.id, challenge_id=challenge_id, status='pending'
    ).first()
    if not friend_challenge:
        flash("Waiting for friend to start challenge.", 'error')
        return redirect(url_for('main.game', section='challenges'))

    try:
        # Cleanup expired links
        FriendChallengeLink.query.filter(FriendChallengeLink.expires_at < datetime.utcnow()).delete()
        db.session.commit()

        # Check if there's already a link
        link = FriendChallengeLink.query.filter_by(challenge_id=challenge_id).filter(
            ((FriendChallengeLink.user1_id == current_user.id) & (FriendChallengeLink.user2_id == friend.id)) |
            ((FriendChallengeLink.user1_id == friend.id) & (FriendChallengeLink.user2_id == current_user.id))
        ).first()

        if link:
            if link.expires_at < datetime.utcnow():
                db.session.delete(link)
                db.session.commit()
                flash("This friend request expired. Please try again.", "error")
                return redirect(url_for('main.game', section='challenges'))

            # Mark confirmation
            if current_user.id == link.user1_id:
                link.user1_confirmed = True
            else:
                link.user2_confirmed = True

            db.session.commit()

            # If both confirmed, mark as friend-linked but don't complete yet
            if link.user1_confirmed and link.user2_confirmed:
                # Only add token usage for the second user (first user already used token when creating the link)
                if current_user.id == link.user2_id:
                    # The second user needs to use a token too
                    # We already checked tokens at the beginning, but we need to check again
                    # in case another process used a token while this request was processing
                    current_tokens_left = get_friend_tokens_left(current_user)
                    if current_tokens_left <= 0:
                        flash("You've used all your friend tokens this week.", "error")
                        return redirect(url_for('main.game', section='challenges'))
                    
                    # Add token usage record
                    db.session.add(FriendTokenUsage(user_id=current_user.id, used_at=datetime.utcnow()))
                    
                flash("Challenge successfully linked with your friend! Complete it within 24 hours of each other for bonus points.", "success")
            else:
                flash("Friend request updated. Waiting for the other user to confirm.", "info")
        else:
            # Check if the user has only 1 token left and has a pending friend request
            tokens_left = get_friend_tokens_left(current_user)
            
            # Check for pending friend requests initiated by this user
            pending_requests = FriendChallengeLink.query.filter(
                FriendChallengeLink.user1_id == current_user.id,
                FriendChallengeLink.user2_confirmed == False,
                FriendChallengeLink.expires_at > datetime.utcnow()
            ).all()
            
            pending_request_count = len(pending_requests)
            
            # Log token usage and pending requests for debugging
            current_app.logger.info(f"User {current_user.id} has {tokens_left} tokens left and {pending_request_count} pending requests")
            
            if tokens_left == 1 and pending_request_count > 0:
                flash("You cannot send a new friend request when you have only 1 token left and another request is pending.", "error")
                return redirect(url_for('main.game', section='challenges'))
            
            # New link
            new_link = FriendChallengeLink(
                challenge_id=challenge_id,
                user1_id=current_user.id,
                user2_id=friend.id,
                user1_confirmed=True,
                user2_confirmed=False,
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(hours=24)
            )
            db.session.add(new_link)
            db.session.add(FriendTokenUsage(user_id=current_user.id, used_at=datetime.utcnow()))
            flash("Challenge linked. Waiting for your friend to confirm within 24 hours.", "info")

        db.session.commit()

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"[Friend Challenge Error] {str(e)}")
        flash("Something went wrong while linking with your friend.", "error")

    return redirect(url_for('main.game', section='challenges'))

def get_friend_tokens_left(user):
    now = datetime.utcnow()
    week_start = now - timedelta(days=now.weekday())
    # Force a fresh query with no caching
    db.session.expire_all()
    tokens_used = FriendTokenUsage.query.filter(
        FriendTokenUsage.user_id == user.id,
        FriendTokenUsage.used_at >= week_start
    ).count()
    return 3 - tokens_used


# Function to handle expired friend challenges
def check_expired_friend_challenges():
    """Check for expired friend challenges and update their status"""
    try:
        now = datetime.utcnow()
        
        # Find links where completion time has expired
        expired_links = FriendChallengeLink.query.filter(
            FriendChallengeLink.completion_expires_at < now,
            ((FriendChallengeLink.user1_completed == True) & (FriendChallengeLink.user2_completed == False)) |
            ((FriendChallengeLink.user1_completed == False) & (FriendChallengeLink.user2_completed == True))
        ).all()
        
        for link in expired_links:
            # Determine which user completed the challenge
            if link.user1_completed and not link.user2_completed:
                # User 1 completed, User 2 didn't
                current_app.logger.info(f"Friend challenge {link.id} expired: User {link.user1_id} completed, User {link.user2_id} did not")
            elif link.user2_completed and not link.user1_completed:
                # User 2 completed, User 1 didn't
                current_app.logger.info(f"Friend challenge {link.id} expired: User {link.user2_id} completed, User {link.user1_id} did not")
            
            # Mark the link as expired
            link.expired = True
        
        db.session.commit()
        current_app.logger.info(f"Processed {len(expired_links)} expired friend challenges")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error checking expired friend challenges: {e}")


# Add the expired field to the FriendChallengeLink model
if not hasattr(FriendChallengeLink, 'expired'):
    FriendChallengeLink.expired = db.Column(db.Boolean, default=False)

# Password Recovery Routes
@bp.route('/recover-password', methods=['GET', 'POST'])
def recover_password():
    if request.method == 'POST':
        username = request.form.get('username')
        backup_code = request.form.get('backup_code')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate input
        if not all([username, backup_code, new_password, confirm_password]):
            flash('All fields are required.', 'error')
            return redirect(url_for('main.recover_password'))
            
        if new_password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('main.recover_password'))
            
        # Find user by username and backup code
        user = User.query.filter_by(username=username, backup_code=backup_code).first()
        
        if user:
            # Update password
            user.set_password(new_password)
            # Generate a new backup code for security
            user.generate_backup_code()
            db.session.commit()
            
            flash('Password has been reset successfully. Please log in with your new password.', 'success')
            return redirect(url_for('main.game', section='auth'))
        else:
            flash('Invalid username or backup code.', 'error')
            return redirect(url_for('main.recover_password'))
    
    # GET request - show the recovery form
    return render_template('recover_password.html')

# Logout Route
@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.game', section='auth'))

# Main Game Route
@bp.route('/game')
@bp.route('/game/<section>')
def game(section='leaderboard'):
    # Auth redirect
    if not current_user.is_authenticated and section not in ['leaderboard', None]:
        section = 'auth'
        
    # Recent global challenges for non-authenticated users
    recent_global_challenges = None
    if not current_user.is_authenticated:
        from app.models import Challenge  # Import Challenge model here to ensure it's available
        recent_global_challenges = (
            CompletedChallenge.query
            .join(Challenge, CompletedChallenge.challenge_id == Challenge.id)
            .join(User, CompletedChallenge.user_id == User.id)
            .filter(User.is_public == True)
            .order_by(CompletedChallenge.completed_at.desc())
            .limit(5)
            .all()
        )

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
        .limit(20)
        .all()
    )
    
    # Get current user's rank in all-time leaderboard if authenticated
    current_user_rank = None
    current_user_points = None
    if current_user.is_authenticated:
        # Subquery to get all users and their points
        all_users_ranked = db.session.query(
            User.id,
            func.coalesce(func.sum(CompletedChallenge.points_earned), 0).label('points'),
            func.rank().over(
                order_by=func.coalesce(func.sum(CompletedChallenge.points_earned), 0).desc()
            ).label('rank')
        ).outerjoin(
            CompletedChallenge, User.id == CompletedChallenge.user_id
        ).group_by(User.id).subquery()
        
        # Get current user's rank
        user_rank_query = db.session.query(
            all_users_ranked.c.rank,
            all_users_ranked.c.points
        ).filter(all_users_ranked.c.id == current_user.id).first()
        
        if user_rank_query:
            current_user_rank = user_rank_query[0]
            current_user_points = user_rank_query[1]
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
        .limit(20)
        .all()
    )
    
    # Get current user's rank in weekly leaderboard if authenticated
    current_user_weekly_rank = None
    current_user_weekly_points = None
    if current_user.is_authenticated:
        # Subquery to get all users and their weekly points
        weekly_users_ranked = db.session.query(
            User.id,
            func.coalesce(func.sum(CompletedChallenge.points_earned), 0).label('points'),
            func.rank().over(
                order_by=func.coalesce(func.sum(CompletedChallenge.points_earned), 0).desc()
            ).label('rank')
        ).outerjoin(
            CompletedChallenge, 
            (User.id == CompletedChallenge.user_id) & (CompletedChallenge.completed_at >= one_week_ago)
        ).group_by(User.id).subquery()
        
        # Get current user's weekly rank
        user_weekly_rank_query = db.session.query(
            weekly_users_ranked.c.rank,
            weekly_users_ranked.c.points
        ).filter(weekly_users_ranked.c.id == current_user.id).first()
        
        if user_weekly_rank_query:
            current_user_weekly_rank = user_weekly_rank_query[0]
            current_user_weekly_points = user_weekly_rank_query[1]

    # Active challenge ID
    from flask import request  # Ensure request is imported locally
    active_challenge_id = request.args.get('active', type=int)

    # User progress and achievements
    user_progress = None
    user_achievements = []
    next_achievements = []
    
    if current_user.is_authenticated:
        # Get completed challenges
        recent_completed = (
            CompletedChallenge.query
            .filter_by(user_id=current_user.id)
            .order_by(CompletedChallenge.completed_at.desc())
            .limit(5)
            .all()
        )
        
        # Get total points
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
        
        # Get total number of completed challenges - force to integer to ensure proper display
        try:
            total_completed_count = db.session.query(func.count(CompletedChallenge.id)).filter(CompletedChallenge.user_id == current_user.id).scalar() or 0
            # Ensure it's an integer for display
            total_completed_count = int(total_completed_count)
        except Exception as e:
            current_app.logger.error(f'Error getting challenge count: {e}')
            total_completed_count = 0
        
        # User progress data
        user_progress = {
            'completed_challenges': recent_completed,
            'challenges_completed': total_completed_count,
            'total_points': user_pts,
            'rank': higher_ranked + 1  # Add rank as current position (higher_ranked + 1)
        } if current_user.is_authenticated else None
        
        # Get user's earned achievements
        from app.models import UserAchievement, Achievement, Challenge
        # Get earned achievements directly from UserAchievement without joining
        earned_user_achievements = UserAchievement.query.filter_by(user_id=current_user.id).order_by(UserAchievement.achieved_at.desc()).all()
        
        # Now we'll fetch the achievement data from our in-memory Achievement model
        earned_achievement_ids = []
        for ua in earned_user_achievements:
            earned_achievement_ids.append(ua.achievement_id)
            user_achievements.append({
                'name': ua.name,  # Using the property from UserAchievement model
                'message': ua.message,  # Using the property from UserAchievement model
                'icon': ua.icon_type,  # Using the property from UserAchievement model
                'achieved_at': ua.achieved_at
            })
        
        # Get achievements the user hasn't earned yet using our in-memory Achievement model
        unearned_achievements = [a for a in Achievement.get_all() if a.id not in earned_achievement_ids]
        
        # Calculate progress toward each unearned achievement
        achievement_progress = []
        
        for achievement in unearned_achievements:
            condition = achievement.condition
            progress = 0
            target = 0
            
            # Total challenges
            if condition.endswith('_total'):
                target = int(condition.split('_')[0])
                progress = CompletedChallenge.query.filter_by(user_id=current_user.id).count()
            
            # Easy challenges
            elif condition.endswith('_easy'):
                target = int(condition.split('_')[0])
                progress = CompletedChallenge.query.join(Challenge).filter(
                    CompletedChallenge.user_id == current_user.id,
                    Challenge.difficulty == 'E'
                ).count()
            
            # Medium challenges
            elif condition.endswith('_medium'):
                target = int(condition.split('_')[0])
                progress = CompletedChallenge.query.join(Challenge).filter(
                    CompletedChallenge.user_id == current_user.id,
                    Challenge.difficulty == 'M'
                ).count()
            
            # Hard challenges
            elif condition.endswith('_hard'):
                target = int(condition.split('_')[0])
                progress = CompletedChallenge.query.join(Challenge).filter(
                    CompletedChallenge.user_id == current_user.id,
                    Challenge.difficulty == 'H'
                ).count()
            
            # Weekly streak
            elif condition.endswith('_weekly_streak'):
                target = int(condition.split('_')[0])
                # This would require more complex logic to track weekly streaks
                # For now, we'll use a placeholder value
                progress = 0
            
            # Calculate percentage and add to list
            if target > 0:
                percentage = min(100, int((progress / target) * 100))
                achievement_progress.append({
                    'achievement': achievement,
                    'progress': progress,
                    'target': target,
                    'percentage': percentage
                })
        
        # Sort by percentage completion (highest first) and take top 3
        achievement_progress.sort(key=lambda x: x['percentage'], reverse=True)
        next_achievements = achievement_progress[:3]
        
        # Build user progress object
        user_progress = {
            'completed_challenges': recent_completed,
            'total_points': user_pts,
            'rank': higher_ranked + 1
        }

    # Get current week info
    if 'utils' not in sys.modules:
        # Add parent directory to path if needed
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    
    from utils.scheduler import get_current_week_info, populate_weekly_challenge_set
    current_week = get_current_week_info()
    current_app.logger.info(f"Current week info: week={current_week['week_number']}, year={current_week['year']}")
    current_app.logger.info("Weekly challenge setup")
    
    try:
        populate_weekly_challenge_set()
    except Exception as e:
        current_app.logger.warning(f"Error populating weekly challenge set: {str(e)}")
        db.session.rollback()
    
    # Ensure user has a weekly order for this week
    if current_user.is_authenticated:
        from app.models import UserWeeklyOrder
        current_week = get_current_week_info()
        week_number = current_week['week_number']
        year = current_week['year']
        has_order = UserWeeklyOrder.query.filter_by(user_id=current_user.id, week_number=week_number, year=year).first()
        if not has_order:
            create_user_weekly_order(current_user.id)
            current_user.update_last_visit_week()
    
    # In-Progress Challenges
    in_progress, active_count = ([], 0)
    friend_linked_challenges = {}
    pending_friend_requests = {}
    
    if current_user.is_authenticated:
        try:
            current_app.logger.info("Using in-progress challenges")
            in_progress, active_count = get_in_progress_challenges(
                current_user.id,
                current_week['week_number'],
                current_week['year']
            )
            
            # Get friend-linked challenges
            friend_links = FriendChallengeLink.query.filter(
                ((FriendChallengeLink.user1_id == current_user.id) | (FriendChallengeLink.user2_id == current_user.id)) &
                (FriendChallengeLink.user1_confirmed == True) & 
                (FriendChallengeLink.user2_confirmed == True) &
                (FriendChallengeLink.expired == False)
            ).all()
            
            for link in friend_links:
                # Get friend username
                friend_id = link.user2_id if link.user1_id == current_user.id else link.user1_id
                friend = User.query.get(friend_id)
                
                if friend:
                    # Check if current user has completed this challenge
                    user_completed = link.user1_completed if link.user1_id == current_user.id else link.user2_completed
                    friend_completed = link.user2_completed if link.user1_id == current_user.id else link.user1_completed
                    
                    friend_linked_challenges[link.challenge_id] = {
                        'friend_username': friend.username,
                        'user_completed': user_completed,
                        'friend_completed': friend_completed,
                        'completion_expires_at': link.completion_expires_at
                    }
            
            # Get pending friend requests (where user is either initiator or receiver)
            pending_requests = FriendChallengeLink.query.filter(
                (((FriendChallengeLink.user1_id == current_user.id) & (FriendChallengeLink.user1_confirmed == True) & (FriendChallengeLink.user2_confirmed == False)) |
                ((FriendChallengeLink.user2_id == current_user.id) & (FriendChallengeLink.user2_confirmed == False))) &
                (FriendChallengeLink.expired == False) &
                (FriendChallengeLink.expires_at > datetime.utcnow())
            ).all()
            
            for request in pending_requests:
                # Determine if user is initiator or receiver
                is_initiator = request.user1_id == current_user.id
                other_user_id = request.user2_id if is_initiator else request.user1_id
                other_user = User.query.get(other_user_id)
                
                if other_user:
                    pending_friend_requests[request.challenge_id] = {
                        'friend_username': other_user.username,
                        'is_initiator': is_initiator,
                        'expires_at': request.expires_at
                    }
        except Exception as e:
            current_app.logger.warning(f"Error getting in-progress challenges: {str(e)}")
            db.session.rollback()
    
    # Build weekly slots: 4E, 3M, 2H
    display_slots = {'E': 4, 'M': 3, 'H': 2}
    challenges_by_difficulty = {'E': [], 'M': [], 'H': []}
    
    if current_user.is_authenticated:
        try:
            # Challenge regeneration feature is disabled, using empty regeneration timers
            regen_timers = {}
            
            # Get current week info for weekly challenges
            current_week = get_current_week_info()
            
            # Query weekly challenge sets for current week/year
            weekly_challenges = WeeklyChallengeSet.query.filter_by(
                week_number=current_week['week_number'],
                year=current_week['year']
            ).all()
            
            current_app.logger.info(f"Found {len(weekly_challenges)} weekly challenge sets")
            
            # Debug: List all weekly challenges by ID
            wc_ids = [f"{wc.challenge_id} (diff={wc.difficulty})" for wc in weekly_challenges]
            current_app.logger.info(f"Weekly challenge IDs: {wc_ids}")
            
            # Make sure we can access the Challenge table directly first
            all_challenges = Challenge.query.limit(5).all()
            challenge_sample = [f"{c.id}: {c.title}" for c in all_challenges]
            current_app.logger.info(f"Sample of challenges in DB: {challenge_sample}")
            
            # Build pools by difficulty
            challenges_pool = {'E': [], 'M': [], 'H': []}
            missing_ids = []
    
            # Try a more direct approach to load challenges
            challenge_ids = [wc.challenge_id for wc in weekly_challenges]
                
            # Load all challenges at once to avoid n+1 query problem
            challenges_by_id = {}
            if challenge_ids:
                challenges = Challenge.query.filter(Challenge.id.in_(challenge_ids)).all()
                challenges_by_id = {c.id: c for c in challenges}
                current_app.logger.info(f"Loaded {len(challenges)} challenges by ID lookup")
                
            missing_ids = []
            for wc in weekly_challenges:
                challenge = challenges_by_id.get(wc.challenge_id)
                if not challenge:
                    # Try a direct get as fallback
                    challenge = Challenge.query.get(wc.challenge_id)
                
                if challenge:
                    challenges_pool[wc.difficulty].append(challenge)
                    current_app.logger.info(f"Added challenge {challenge.id}: {challenge.title[:20]} to {wc.difficulty} pool")
                else:
                    missing_ids.append(wc.challenge_id)
                    current_app.logger.warning(f"Challenge ID {wc.challenge_id} not found in database")
            
            if missing_ids:
                current_app.logger.error(f"Missing challenge IDs: {missing_ids}")
    
            
            # Weekly challenges are now enabled, using the pools we built above
            current_app.logger.info("Weekly challenges are now enabled")
    
            # Log pool sizes
            for diff in ['E', 'M', 'H']:
                current_app.logger.info(f"Pool size for {diff}: {len(challenges_pool[diff])}")
    
            # Sample challenges for each difficulty and create slots
            for diff, slots in display_slots.items():
                # Check if we have any challenges for this difficulty
                if challenges_pool[diff]:
                    # Sample from available challenges
                    sample_size = min(slots, len(challenges_pool[diff]))
                    selected = random.sample(challenges_pool[diff], sample_size)
                    
                    for i, ch in enumerate(selected):
                        # Create slot with challenge and NO regeneration timer
                        challenges_by_difficulty[diff].append({
                            'challenge': ch,
                            'all_done': False,
                            'regenerate_at': None,  # No regeneration timer needed for active challenges
                            'regenerate_time': None
                        })
                
                # Fill in empty slots with regeneration timers if available
                while len(challenges_by_difficulty[diff]) < slots:
                    slot_num = len(challenges_by_difficulty[diff])
                    regen_key = f"{diff}_{slot_num}"
                    
                    if regen_key in regen_timers:
                        # Use existing regeneration timer
                        challenges_by_difficulty[diff].append({
                            'challenge': None,
                            'all_done': False,
                            'regenerate_at': regen_timers[regen_key]['regenerate_at'],
                            'regenerate_time': regen_timers[regen_key]['regenerate_time']
                        })
                    else:
                        # No regeneration timer, just an empty slot
                        challenges_by_difficulty[diff].append({
                            'challenge': None,
                            'all_done': False,
                            'regenerate_at': None,
                            'regenerate_time': None
                        })
        except Exception as e:
            current_app.logger.error(f"Error building weekly challenges: {str(e)}", exc_info=True)
            import traceback
            current_app.logger.error(traceback.format_exc())
            db.session.rollback()
            # Create empty slots for all difficulties
            for diff, slots in display_slots.items():
                for _ in range(slots):
                    challenges_by_difficulty[diff].append({
                        'challenge': None,
                        'all_done': False,
                        'regenerate_at': None,
                        'regenerate_time': None
                    })
    
    # Only show weekly challenges not completed or in progress by the user this week, in user-specific order
    user_challenge_ids_to_exclude = set()
    if current_user.is_authenticated:
        from app.models import UserChallenge
        # Get both completed and in-progress challenges to exclude from available challenges
        excluded_statuses = UserChallenge.query.filter(
            UserChallenge.user_id == current_user.id,
            UserChallenge.week_number == current_week['week_number'],
            UserChallenge.year == current_week['year'],
            UserChallenge.status.in_(['completed', 'pending'])
        ).all()
        user_challenge_ids_to_exclude = {uc.challenge_id for uc in excluded_statuses}

    # Get user-specific order for the week
    user_order = {'E': [], 'M': [], 'H': []}
    if current_user.is_authenticated:
        from app.models import UserWeeklyOrder
        user_orders = UserWeeklyOrder.query.filter_by(
            user_id=current_user.id,
            week_number=current_week['week_number'],
            year=current_week['year']
        ).order_by(UserWeeklyOrder.difficulty, UserWeeklyOrder.order_position).all()
        for uo in user_orders:
            if uo.challenge_id not in user_challenge_ids_to_exclude:
                user_order[uo.difficulty].append(uo.challenge)

    # Build display slots for each difficulty
    display_slots = {'E': 4, 'M': 3, 'H': 2}
    challenges_by_difficulty = {'E': [], 'M': [], 'H': []}
    for diff, slots in display_slots.items():
        added = 0
        for ch in user_order[diff]:
            if added < slots:
                challenges_by_difficulty[diff].append({'challenge': ch, 'all_done': False, 'regenerate_at': None, 'regenerate_time': None})
                added += 1
        # Fill empty slots if needed
        while len(challenges_by_difficulty[diff]) < slots:
            challenges_by_difficulty[diff].append({'challenge': None, 'all_done': False, 'regenerate_at': None, 'regenerate_time': None})

    # Final context for template
    challenges = {
        'in_progress': in_progress,
        'E': challenges_by_difficulty['E'],
        'M': challenges_by_difficulty['M'],
        'H': challenges_by_difficulty['H'],
    }
    
    # Detailed logging of what's in the challenges variable
    current_app.logger.info(f"Challenge keys: {challenges.keys()}")
    current_app.logger.info(f"In-progress count: {len(challenges.get('in_progress', []))}")
    
    # Log what's actually in each difficulty slot
    for diff in ['E', 'M', 'H']:
        slot_data = []
        for i, slot in enumerate(challenges.get(diff, [])):
            if slot.get('challenge'):
                slot_data.append(f"Slot {i}: {slot['challenge'].title[:20]}")
            elif slot.get('regenerate_at'):
                slot_data.append(f"Slot {i}: Regenerating ({slot['regenerate_time']})")
            else:
                slot_data.append(f"Slot {i}: Empty")
        current_app.logger.info(f"{diff} challenges: {slot_data}")
    
    if not any(slot.get('challenge') for diff in ['E', 'M', 'H'] for slot in challenges.get(diff, [])):
        current_app.logger.warning("WARNING: No challenge objects found in any slots!")
        
        # Check if weekly challenge population might be needed
        try:
            # Try populating weekly challenges if needed
            from utils.scheduler import populate_weekly_challenge_set
            current_app.logger.info("Attempting to populate weekly challenge set...")
            # Call the function with no arguments as it gets the current week internally
            populated = populate_weekly_challenge_set()
            current_app.logger.info(f"Weekly challenge population result: True if populated else False")
            
            if populated:
                flash("Weekly challenges have been refreshed. Please reload the page.", "info")
        except Exception as pop_err:
            current_app.logger.error(f"Error attempting to populate challenges: {str(pop_err)}")
    
    # Get friend tokens left and weekly challenge counts
    friend_tokens_left = None
    weekly_challenge_counts = None
    weekly_challenge_caps = None
    
    if current_user.is_authenticated:
        # Force a database refresh to get accurate token count
        db.session.expire_all()
        friend_tokens_left = get_friend_tokens_left(current_user)
        weekly_challenge_counts = current_user.get_weekly_challenge_counts()
        # Use the centralized weekly challenge caps
        weekly_challenge_caps = User.WEEKLY_CHALLENGE_CAPS
    
    # Check for new achievements in the session
    new_achievements = session.pop('new_achievements', None)
    
    return render_template(
        'game.html',
        section=section,
        top_users=all_time_users,
        weekly_users=weekly_users,
        challenges=challenges,
        active_challenge_id=active_challenge_id,
        active_count=active_count,
        user_progress=user_progress,
        user_achievements=user_achievements,
        next_achievements=next_achievements,
        friend_tokens_left=friend_tokens_left,
        weekly_challenge_counts=weekly_challenge_counts,
        weekly_challenge_caps=weekly_challenge_caps,
        friend_linked_challenges=friend_linked_challenges,
        pending_friend_requests=pending_friend_requests,
        current_user_rank=current_user_rank,
        current_user_points=current_user_points,
        current_user_weekly_rank=current_user_weekly_rank,
        current_user_weekly_points=current_user_weekly_points,
        recent_global_challenges=recent_global_challenges,
        login_form=(LoginForm() if section == 'auth' else None),
        signup_form=(RegistrationForm() if section == 'auth' else None),
        new_achievements=new_achievements
    )
