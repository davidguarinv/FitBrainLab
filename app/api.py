from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from datetime import datetime
from . import db
from .models import Challenge, CompletedChallenge, User, ChallengeRegeneration, UserChallenge, WeeklyChallengeSet, UserWeeklyOrder, WeeklyHabitChallenge

bp = Blueprint('api', __name__, url_prefix='/api')

@bp.route('/challenges/<int:challenge_id>/start', methods=['POST'])
@login_required
def start_challenge(challenge_id):
    from flask import flash, redirect, url_for, current_app, request, jsonify
    from datetime import datetime, timedelta
    from utils.scheduler import get_current_week_info
    
    challenge = Challenge.query.get_or_404(challenge_id)
    
    # Get current week info
    current_week = get_current_week_info()
    
    # Check if user can take this challenge based on weekly caps
    if not current_user.can_take_weekly_challenge(challenge.difficulty):
        flash(f'You have reached your weekly limit for {challenge.difficulty} challenges', 'error')
        return redirect(url_for('main.game', section='challenges'))
    
    # Check if challenge is already in progress
    existing_challenge = UserChallenge.query.filter_by(
        user_id=current_user.id,
        challenge_id=challenge_id,
        week_number=current_week['week_number'],
        year=current_week['year'],
        status='pending'
    ).first()
    
    if existing_challenge:
        flash('Challenge already in progress', 'info')
        return redirect(url_for('main.game', section='challenges'))
    
    # Check if user already has 2 challenges in progress
    in_progress_count = UserChallenge.query.filter_by(
        user_id=current_user.id,
        week_number=current_week['week_number'],
        year=current_week['year'],
        status='pending'
    ).count()
    
    if in_progress_count >= 2:
        flash('You can only have 2 challenges in progress at once', 'error')
        return redirect(url_for('main.game', section='challenges'))
    
    # Check if challenge already exists for this user, week, and year before creating a new one
    with db.session.no_autoflush:
        existing = UserChallenge.query.filter_by(
            user_id=current_user.id,
            challenge_id=challenge_id,
            week_number=current_week['week_number'],
            year=current_week['year']
        ).first()
        
        if existing:
            # Challenge already exists, make sure it's in pending state
            if existing.status != 'pending':
                existing.status = 'pending'
                existing.started_at = datetime.utcnow()
                existing.completed_at = None
                existing.points_earned = None
                db.session.commit()
        else:
            # Create a new UserChallenge record
            user_challenge = UserChallenge(
                user_id=current_user.id,
                challenge_id=challenge_id,
                week_number=current_week['week_number'],
                year=current_week['year'],
                status='pending',
                started_at=datetime.utcnow()
            )
            db.session.add(user_challenge)
            db.session.commit()
    

    # Get the current time
    now = datetime.utcnow()
    
    # Get the slot number from the form data - this is crucial for proper timer placement
    slot_number = request.form.get('slot')
    current_app.logger.info(f'Form data received: {request.form}')
    current_app.logger.info(f'Slot from form: {slot_number}')
    
    if slot_number and str(slot_number).isdigit():
        slot_number = int(slot_number)
        current_app.logger.info(f'Starting challenge {challenge_id} from slot {slot_number}')
    else:
        # Default to slot 1 if no slot parameter
        slot_number = 1
        current_app.logger.info(f'No slot provided, defaulting to slot {slot_number}')
    
    # Get regeneration hours from the model
    regen_hours = ChallengeRegeneration.get_regen_hours(challenge.difficulty)
    regen_time = now + timedelta(hours=regen_hours)
        
    current_app.logger.info(f'Setting regeneration timer for {challenge.difficulty} difficulty slot {slot_number}: {regen_time}')
    print(f'Challenge {challenge_id} ({challenge.difficulty}) started from slot {slot_number}. Next challenge will be available at {regen_time}')
    
    # IMPORTANT: Create or update the regeneration timer for the SPECIFIC SLOT that was used
    # First, check if a timer already exists for this slot
    timer = ChallengeRegeneration.query.filter_by(
        difficulty=challenge.difficulty,
        slot_number=slot_number
    ).first()
    
    if timer:
        # Update existing timer
        current_app.logger.info(f'Updating timer for {challenge.difficulty} slot {slot_number}')
        timer.regenerate_at = regen_time
    else:
        # Create new timer
        current_app.logger.info(f'Creating new timer for {challenge.difficulty} slot {slot_number}')
        timer = ChallengeRegeneration(
            difficulty=challenge.difficulty,
            slot_number=slot_number,
            regenerate_at=regen_time
        )
        db.session.add(timer)
    
    # Save changes
    db.session.commit()
    
    # Log the regeneration time
    time_diff = (regen_time - now).total_seconds()
    print(f'Challenge will regenerate at {regen_time} (in {time_diff:.1f} seconds)')
    
    # Redirect to the challenges page with the active challenge
    flash('Challenge started successfully!', 'success')
    return redirect(url_for('main.game', section='challenges', active=challenge_id))

@bp.route('/challenges/<int:challenge_id>/complete', methods=['POST'])
@login_required
def complete_challenge(challenge_id):
    from flask import flash, redirect, url_for, current_app
    from utils.scheduler import get_current_week_info, update_habit_challenge_progress
    from datetime import timedelta
    from .challenge_timers import create_regeneration_timer
    
    # Get current week info
    current_week = get_current_week_info()
    
    # Check if challenge is in progress in the weekly system
    user_challenge = UserChallenge.query.filter_by(
        user_id=current_user.id,
        challenge_id=challenge_id,
        week_number=current_week['week_number'],
        year=current_week['year'],
        status='pending'
    ).first()
    
    if not user_challenge:
        flash('Challenge not in progress', 'error')
        return redirect(url_for('main.game', section='challenges'))
    
    challenge = Challenge.query.get_or_404(challenge_id)
    
    # Complete the challenge in the weekly system
    if user_challenge:
        user_challenge.status = 'completed'
        user_challenge.completed_at = datetime.utcnow()
        user_challenge.points_earned = challenge.points
    
    # Record the completion in the history
    completed = CompletedChallenge(
        user_id=current_user.id,
        challenge_id=challenge_id,
        points_earned=challenge.points
    )
    db.session.add(completed)
    
    # Update user stats
    if challenge.difficulty == 'E':
        current_user.daily_e_count += 1
    elif challenge.difficulty == 'M':
        current_user.daily_m_count += 1
    else:
        current_user.daily_h_count += 1
    
    # Check if this is the user's weekly habit challenge and update progress
    habit_challenge = WeeklyHabitChallenge.query.filter_by(
        user_id=current_user.id,
        challenge_id=challenge_id,
        week_number=current_week['week_number'],
        year=current_week['year']
    ).first()
    
    if habit_challenge:
        update_habit_challenge_progress(current_user.id, challenge_id)
        flash('Habit challenge completed for today!', 'success')
    
    # Remove from in progress (old system)
    if in_progress:
        db.session.delete(in_progress)
    
    db.session.commit()
    
    # Create a regeneration timer for this challenge's difficulty
    # Pass slot_number=None to let the utility function find the first available slot
    try:
        current_app.logger.info(f'Attempting to create regeneration timer for {challenge.difficulty} difficulty')
        regen_time = create_regeneration_timer(challenge.difficulty, slot_number=None)
        current_app.logger.info(f'Successfully created timer for {challenge.difficulty} difficulty, regenerates at {regen_time}')
        print(f'SUCCESS: Created regeneration timer for {challenge.difficulty} difficulty, regenerates at {regen_time}')
    except Exception as e:
        current_app.logger.error(f'Failed to create regeneration timer: {str(e)}')
        print(f'ERROR: Failed to create regeneration timer: {str(e)}')
        # We still want to complete the challenge even if timer creation fails
    
    # Redirect to the progress page
    flash('Challenge completed successfully!', 'success')
    return redirect(url_for('main.game', section='progress'))

@bp.route('/challenges/<int:challenge_id>/abandon', methods=['POST'])
@login_required
def abandon_challenge(challenge_id):
    from flask import flash, redirect, url_for
    from utils.scheduler import get_current_week_info
    
    # Get current week info
    current_week = get_current_week_info()
    
    # Check if challenge is in progress in the weekly system
    user_challenge = UserChallenge.query.filter_by(
        user_id=current_user.id,
        challenge_id=challenge_id,
        week_number=current_week['week_number'],
        year=current_week['year'],
        status='pending'
    ).first()
    
    if not user_challenge:
        flash('Challenge not in progress', 'error')
        return redirect(url_for('main.game', section='challenges'))
    
    challenge = Challenge.query.get_or_404(challenge_id)
    difficulty = challenge.difficulty
    
    # Mark as abandoned in the weekly system
    user_challenge.status = 'abandoned'
    
    # SIMPLIFIED APPROACH: Delete and recreate the order entry to avoid unique constraints
    # Get the current order entry
    order_entry = UserWeeklyOrder.query.filter_by(
        user_id=current_user.id,
        challenge_id=challenge_id,
        week_number=current_week['week_number'],
        year=current_week['year']
    ).first()
    
    if order_entry:
        # Get all order entries for this difficulty
        all_entries = UserWeeklyOrder.query.filter_by(
            user_id=current_user.id,
            week_number=current_week['week_number'],
            year=current_week['year'],
            difficulty=difficulty
        ).order_by(UserWeeklyOrder.order_position).all()
        
        # Get the highest position number
        highest_position = 0
        for entry in all_entries:
            if entry.order_position > highest_position:
                highest_position = entry.order_position
        
        # Simply update the position to be at the end
        order_entry.order_position = highest_position + 1
        print(f'Moved abandoned challenge {challenge_id} to position {highest_position + 1} in {difficulty} rotation')
    
    # Commit changes
    try:
        db.session.commit()
        flash('Challenge abandoned. It will now appear at the end of the rotation for this week.', 'info')
    except Exception as e:
        db.session.rollback()
        print(f'Error abandoning challenge: {str(e)}')
        flash('There was an error abandoning the challenge. Please try again.', 'error')

    
    # Redirect to the challenges page
    return redirect(url_for('main.game', section='challenges'))

@bp.route('/profile/toggle-visibility', methods=['POST'])
@login_required
def toggle_profile_visibility():
    current_user.is_public = not current_user.is_public
    db.session.commit()
    return jsonify({
        'success': True,
        'is_public': current_user.is_public
    })

@bp.route('/habit-challenge/select', methods=['POST'])
@login_required
def select_habit_challenge():
    from flask import request, flash, redirect, url_for
    from utils.scheduler import get_current_week_info
    
    # Get the selected challenge ID from the form
    challenge_id = request.form.get('challenge_id')
    if not challenge_id or not challenge_id.isdigit():
        flash('Invalid challenge selection', 'error')
        return redirect(url_for('main.game', section='challenges'))
    
    challenge_id = int(challenge_id)
    challenge = Challenge.query.get_or_404(challenge_id)
    
    # Check if the challenge is valid (Easy or Medium only)
    if challenge.difficulty not in ['E', 'M']:
        flash('Only Easy or Medium challenges can be selected as habit challenges', 'error')
        return redirect(url_for('main.game', section='challenges'))
    
    # Get current week info
    current_week = get_current_week_info()
    
    # Check if user already has a habit challenge for this week
    existing_habit = WeeklyHabitChallenge.query.filter_by(
        user_id=current_user.id,
        week_number=current_week['week_number'],
        year=current_week['year']
    ).first()
    
    if existing_habit:
        flash('You already have a habit challenge for this week', 'info')
        return redirect(url_for('main.game', section='challenges'))
    
    # Create the weekly habit challenge
    habit_challenge = WeeklyHabitChallenge(
        user_id=current_user.id,
        challenge_id=challenge_id,
        week_number=current_week['week_number'],
        year=current_week['year'],
        days_completed=0,
        bonus_points_earned=0
    )
    db.session.add(habit_challenge)
    db.session.commit()
    
    flash(f'Challenge "{challenge.title}" set as your weekly habit challenge!', 'success')
    return redirect(url_for('main.game', section='challenges'))
