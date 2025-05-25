from datetime import datetime, timedelta
import json
import math
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from . import db
from .models import User, Challenge, CompletedChallenge, ChallengeRegeneration, UserChallenge, WeeklyChallengeSet, UserWeeklyOrder, WeeklyHabitChallenge, FunFact
from .forms import LoginForm, RegistrationForm
from .email_handler import send_email
import logging
import os
import json
from sqlalchemy import func
import uuid
import re
import math

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

@bp.route('/api/challenges/<int:challenge_id>/complete', methods=['POST'])
@login_required
def complete_challenge(challenge_id):
    """Complete a challenge and return a random fun fact"""
    try:
        # Find the challenge
        challenge = Challenge.query.get_or_404(challenge_id)
        
        # Check if the user already completed this challenge
        existing = CompletedChallenge.query.filter_by(
            user_id=current_user.id,
            challenge_id=challenge_id
        ).first()
        
        if existing:
            flash('You have already completed this challenge!', 'info')
            return redirect(url_for('main.game', section='challenges'))
        
        # Create or update user challenge record
        user_challenge = UserChallenge.query.filter_by(
            user_id=current_user.id,
            challenge_id=challenge_id,
            status='pending'
        ).first()
        
        if not user_challenge:
            user_challenge = UserChallenge(
                user_id=current_user.id,
                challenge_id=challenge_id,
                status='pending',
                week_number=datetime.utcnow().isocalendar()[1],
                year=datetime.utcnow().year,
                started_at=datetime.utcnow()
            )
            db.session.add(user_challenge)
            
        # Remove from completed challenges if it was there
        completed = CompletedChallenge.query.filter_by(
            user_id=current_user.id,
            challenge_id=challenge_id
        ).first()
        
        if completed:
            db.session.delete(completed)
        
        # Get a random fun fact
        fun_fact = FunFact.get_random_fact()
        if fun_fact:
            # Update its display stats
            fun_fact.times_shown += 1
            fun_fact.last_shown = datetime.utcnow()
        
        # Create regeneration timer for this challenge
        regen = ChallengeRegeneration(
            user_id=current_user.id,
            difficulty=challenge.difficulty,
            regenerate_at=datetime.utcnow() + timedelta(hours=challenge.regen_hours),
            slot_number=int(request.args.get('slot', 1))
        )
        db.session.add(regen)
        
        # Update user daily stats
        if current_user.last_challenge_date != datetime.utcnow().date():
            current_user.daily_e_count = 0
            current_user.daily_m_count = 0
            current_user.daily_h_count = 0
            current_user.last_challenge_date = datetime.utcnow().date()
            
            
        # Update daily and weekly counters based on challenge difficulty
        if challenge.difficulty == 'E':
            current_user.daily_e_count += 1
            current_user.weekly_e_completed += 1
        elif challenge.difficulty == 'M':
            current_user.daily_m_count += 1
            current_user.weekly_m_completed += 1
        elif challenge.difficulty == 'H':
            current_user.daily_h_count += 1
            current_user.weekly_h_completed += 1
        
        # Check if this is a friend challenge link
        friend_link = None
        friend_code = request.form.get('friend_code')
        if friend_code:
            friend = User.query.filter_by(personal_code=friend_code).first()
            if friend:
                friend_link = FriendChallengeLink.query.filter(
                    FriendChallengeLink.challenge_id == challenge_id,
                    ((FriendChallengeLink.user1_id == current_user.id) & (FriendChallengeLink.user2_id == friend.id)) |
                    ((FriendChallengeLink.user1_id == friend.id) & (FriendChallengeLink.user2_id == current_user.id))
                ).first()
                
                if not friend_link:
                    # Create a new friend link
                    friend_link = FriendChallengeLink(
                        challenge_id=challenge_id,
                        user1_id=current_user.id,
                        user2_id=friend.id,
                        user1_confirmed=True,
                        expires_at=datetime.utcnow() + timedelta(days=1)
                    )
                    db.session.add(friend_link)
                elif friend_link.user1_id == current_user.id and not friend_link.user1_confirmed:
                    friend_link.user1_confirmed = True
                    # If both users have confirmed, award bonus points
                    if friend_link.user2_confirmed:
                        # Award 50% bonus points
                        bonus_points = int(challenge.points * 0.5)
                        completed.points_earned += bonus_points
                        flash(f'You earned {bonus_points} bonus points for completing this challenge with a friend!', 'success')
                elif friend_link.user2_id == current_user.id and not friend_link.user2_confirmed:
                    friend_link.user2_confirmed = True
                    # If both users have confirmed, award bonus points
                    if friend_link.user1_confirmed:
                        # Award 50% bonus points
                        bonus_points = int(challenge.points * 0.5)
                        completed.points_earned += bonus_points
                        flash(f'You earned {bonus_points} bonus points for completing this challenge with a friend!', 'success')
        
        # Check for Challenge of the Week completion
        cotw = ChallengeOfTheWeek.query.filter_by(
            user_id=current_user.id,
            challenge_id=challenge_id,
            week_number=datetime.utcnow().isocalendar()[1],
            year=datetime.utcnow().isocalendar()[0]
        ).first()
        
        if cotw and cotw.can_complete_today():
            bonus_points = cotw.complete_daily()
            completed.points_earned += bonus_points
            flash(f'You earned {bonus_points} bonus points for completing your Challenge of the Week!', 'success')
        
        db.session.commit()
        
        # Check if the user has earned any achievements
        from app.models import UserAchievement
        new_achievements = UserAchievement.check_achievements(current_user.id)
        
        if new_achievements:
            for achievement in new_achievements:
                flash(f"Achievement Unlocked: {achievement['name']} - {achievement['message']} (+{achievement['points_reward']} points)", 'achievement')
                # Add achievement points to user
        
        # Success message with fun fact
        flash('Challenge completed successfully!', 'success')
        
        # Use different success messages randomly
        success_messages = [
            'Nicely done!', 
            'Good one champ!', 
            'Way to go!', 
            'Nice moves!', 
            'You\'re incredible!', 
            'You\'re a step closer to being Stresilient!'
        ]
        
        # Return fun fact information along with redirect
        if fun_fact:
            return render_template('game.html', 
                              section='challenges',
                              fun_fact=fun_fact,
                              success_message=random.choice(success_messages))
        else:
            return redirect(url_for('main.game', section='challenges'))
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error completing challenge: {str(e)}")
        flash(f'Error completing challenge: {str(e)}', 'error')
        return redirect(url_for('main.game', section='challenges'))

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
    user_achievements = None
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
        
        # Get user's achievements for the profile section
        from app.models import UserAchievement, Achievement
        achievements_data = db.session.query(UserAchievement, Achievement)\
            .join(Achievement, UserAchievement.achievement_id == Achievement.id)\
            .filter(UserAchievement.user_id == current_user.id)\
            .order_by(UserAchievement.achieved_at.desc())\
            .all()
            
        # Process achievements for easy template rendering
        user_achievements = []
        for ua, achievement in achievements_data:
            user_achievements.append({
                'id': achievement.id,
                'name': achievement.name,
                'message': achievement.message,
                'points_reward': achievement.points_reward,
                'icon': achievement.icon,
                'achieved_at': ua.achieved_at
            })
            
        user_progress = {
            'completed_challenges': completed,
            'total_points': user_points,
            'rank': user_rank,
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
        from app.utils.game_helpers import get_in_progress_challenges
        in_progress_challenges, in_progress_count = get_in_progress_challenges(
            current_user.id,
            current_week['week_number'],
            current_week['year']
        )
    
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
            
            # Check if a specific challenge should be shown for this slot
            available_challenge = None
            i = 0
            
            # Try to assign a challenge from the user's weekly order
            while i < len(user_order) and not available_challenge:
                order_item = user_order[i]
                i += 1
                
                # Skip if this challenge has already been attempted
                if order_item.challenge_id in attempted_ids:
                    continue
                    
                # Get the challenge details
                challenge = Challenge.query.get(order_item.challenge_id)
                if challenge:
                    available_challenge = challenge
                    break
            
            # If we couldn't get a challenge from the user's weekly order, create a dummy one
            # This is for testing purposes and will be shown instead of "Challenge Available Soon"
            if not available_challenge:
                # Let's check if we have any challenges in the database first
                all_challenges = Challenge.query.filter_by(difficulty=difficulty).all()
                if all_challenges:
                    # Use a random existing challenge
                    import random
                    available_challenge = random.choice(all_challenges)
                else:
                    # Create a dummy challenge - this would be a temporary fix
                    dummy_challenge = Challenge(
                        title=f"{difficulty} Challenge #{slot_number}",
                        description="Complete this challenge to earn points and unlock a fun fact about exercise and brain health!",
                        difficulty=difficulty,
                        points=10 * (3 if difficulty == 'H' else 2 if difficulty == 'M' else 1),
                        regen_hours=8
                    )
                    db.session.add(dummy_challenge)
                    db.session.commit()
                    available_challenge = dummy_challenge

            # For each slot
            for slot_number in range(1, display_counts[difficulty] + 1):
                # Check if this slot has an active regeneration timer
                timer_key = (difficulty, slot_number)
                is_regenerating = False
                time_remaining = None
                regenerate_at = None
                
                if timer_key in regeneration_by_slot:
                    timer = regeneration_by_slot[timer_key]
                    time_remaining = (timer.regenerate_at - now).total_seconds()
                    
                    if time_remaining > 0:
                        # This slot is still regenerating
                        is_regenerating = True
                        regenerate_at = timer.regenerate_at.isoformat()

                # Only assign a challenge if there's no active regeneration timer
                if not is_regenerating and available_challenge:
                    challenges_by_difficulty[difficulty].append({
                        'challenge': available_challenge,
                        'regenerating': False,
                        'slot_number': slot_number
                    })
                    
                    # Make sure we don't reuse this challenge
                    available_challenge = None
                    
                    # Try to find the next available challenge
                    while i < len(user_order) and not available_challenge:
                        order_item = user_order[i]
                        i += 1
                        
                        # Skip if this challenge has already been attempted
                        if order_item.challenge_id in attempted_ids:
                            continue
                            
                        # Get the challenge details
                        challenge = Challenge.query.get(order_item.challenge_id)
                        if challenge:
                            available_challenge = challenge
                            break
                else:
                    # Either regenerating or no available challenge
                    challenges_by_difficulty[difficulty].append({
                        'challenge': None,
                        'regenerating': is_regenerating,
                        'regenerate_at': regenerate_at,
                        'regenerate_time': format_time_remaining(time_remaining) if time_remaining else None,
                        'slot_number': slot_number,
                        'all_done': False
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
    
    # Build the challenges dictionary with the new structure
    challenges = {
        'in_progress': in_progress_challenges,
        'E': [c['challenge'] for c in challenges_by_difficulty.get('E', []) if c.get('challenge')][:4],  # Max 4 easy challenges
        'M': [c['challenge'] for c in challenges_by_difficulty.get('M', []) if c.get('challenge')][:3],  # Max 3 medium challenges
        'H': [c['challenge'] for c in challenges_by_difficulty.get('H', []) if c.get('challenge')][:2]   # Max 2 hard challenges
    }
    
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
                           challenges=challenges,
                           active_challenge_id=active_challenge_id,
                           active_count=in_progress_count,
                           login_form=login_form,
                           signup_form=signup_form,
                           user_achievements=user_achievements)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.game'))
    
    # Handle login form submission
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember_me = request.form.get('remember_me') == 'on'
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user, remember=remember_me)
            flash('Logged in successfully!', 'success')
            next_page = request.args.get('next') or url_for('main.game')
            return redirect(next_page)
        else:
            flash('Invalid username or password', 'error')
            return redirect(url_for('main.game', section='auth'))
        
    return redirect(url_for('main.game', section='auth'))


@bp.route('/recover-password', methods=['GET', 'POST'])
def recover_password():
    """Password recovery using backup codes"""
    if current_user.is_authenticated:
        return redirect(url_for('main.game'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        backup_code = request.form.get('backup_code')
        
        if not username or not backup_code:
            flash('Please provide both username and backup code', 'error')
            return render_template('recover_password.html')
        
        user = User.query.filter_by(username=username).first()
        
        if not user:
            flash('Username not found', 'error')
            return render_template('recover_password.html')
        
        if user.backup_code != backup_code:
            flash('Invalid backup code', 'error')
            return render_template('recover_password.html')
        
        # If we get here, the backup code is valid
        # Generate a reset token and redirect to reset password page
        session['reset_user_id'] = user.id
        return redirect(url_for('main.reset_password'))
    
    return render_template('recover_password.html')


@bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """Reset password after successful backup code verification"""
    if current_user.is_authenticated:
        return redirect(url_for('main.game'))
    
    # Check if user is authorized to reset password
    user_id = session.get('reset_user_id')
    if not user_id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('main.login'))
    
    user = User.query.get(user_id)
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('main.login'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not password or not confirm_password:
            flash('Please provide both password fields', 'error')
            return render_template('reset_password.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('reset_password.html')
        
        if len(password) < 8:
            flash('Password must be at least 8 characters long', 'error')
            return render_template('reset_password.html')
        
        # Update the password and generate a new backup code
        user.set_password(password)
        user.generate_backup_code()  # Generate a new backup code for security
        db.session.commit()
        
        # Clear the session and redirect to login
        session.pop('reset_user_id', None)
        flash('Password has been reset successfully. Please login with your new password.', 'success')
        return redirect(url_for('main.game', section='auth'))
    
    return render_template('reset_password.html')

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
        UserChallenge.started_at
    ).join(
        UserChallenge,
        Challenge.id == UserChallenge.challenge_id
    ).filter(
        UserChallenge.user_id == current_user.id,
        UserChallenge.status == 'pending'
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
        
        # Clean up user challenges
        UserChallenge.query.filter_by(user_id=current_user.id, status='pending').delete()
        
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
