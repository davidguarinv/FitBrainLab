from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from datetime import datetime
from . import db
from .models import Challenge, CompletedChallenge, InProgressChallenge, User, ChallengeRegeneration

bp = Blueprint('api', __name__, url_prefix='/api')

@bp.route('/challenges/<int:challenge_id>/start', methods=['POST'])
@login_required
def start_challenge(challenge_id):
    from flask import flash, redirect, url_for, current_app, request
    from datetime import datetime, timedelta
    challenge = Challenge.query.get_or_404(challenge_id)
    
    # Check if user can take this challenge
    if not current_user.can_take_challenge(challenge.difficulty):
        flash(f'You have reached your daily limit for {challenge.difficulty} challenges', 'error')
        return redirect(url_for('main.game', section='challenges'))
    
    # Check if challenge is already in progress
    if InProgressChallenge.query.filter_by(
        user_id=current_user.id,
        challenge_id=challenge_id
    ).first():
        flash('Challenge already in progress', 'info')
        return redirect(url_for('main.game', section='challenges'))
    
    # Check if user already has 2 challenges in progress
    in_progress_count = InProgressChallenge.query.filter_by(
        user_id=current_user.id
    ).count()
    
    if in_progress_count >= 2:
        flash('You can only have 2 challenges in progress at once', 'error')
        return redirect(url_for('main.game', section='challenges'))
    
    # Start the challenge
    in_progress = InProgressChallenge(
        user_id=current_user.id,
        challenge_id=challenge_id
    )
    db.session.add(in_progress)
    
    # Get the current time
    now = datetime.utcnow()
    
    # Get the slot number from the request form data or query params
    slot_number = request.form.get('slot') or request.args.get('slot')
    if slot_number and str(slot_number).isdigit():
        slot_number = int(slot_number)
    else:
        # Default to slot 1 if no slot parameter
        slot_number = 1
        
    print(f'Starting challenge {challenge_id} from slot {slot_number}')
    
    # For testing, use a short regeneration time (30 seconds)
    # In production, use the proper hours based on difficulty
    test_mode = True
    
    if test_mode:
        # Testing: 30 seconds
        regen_time = now + timedelta(seconds=30)
    else:
        # Production: proper hours
        if challenge.difficulty == 'E':
            regen_time = now + timedelta(hours=6)  # 6 hours for Easy
        elif challenge.difficulty == 'M':
            regen_time = now + timedelta(hours=8)  # 8 hours for Medium
        else:
            regen_time = now + timedelta(hours=10)  # 10 hours for Hard
    
    # Create or update the regeneration timer
    # First, check if a timer already exists for this slot
    timer = ChallengeRegeneration.query.filter_by(
        difficulty=challenge.difficulty,
        slot_number=slot_number
    ).first()
    
    if timer:
        # Update existing timer
        print(f'Updating timer for {challenge.difficulty} slot {slot_number}')
        timer.regenerate_at = regen_time
    else:
        # Create new timer
        print(f'Creating new timer for {challenge.difficulty} slot {slot_number}')
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
    from flask import flash, redirect, url_for
    # Check if challenge is in progress
    in_progress = InProgressChallenge.query.filter_by(
        user_id=current_user.id,
        challenge_id=challenge_id
    ).first_or_404()
    
    challenge = Challenge.query.get_or_404(challenge_id)
    
    # Complete the challenge
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
    
    # Remove from in progress
    db.session.delete(in_progress)
    db.session.commit()
    
    # Redirect to the progress page
    flash('Challenge completed successfully!', 'success')
    return redirect(url_for('main.game', section='progress'))

@bp.route('/challenges/<int:challenge_id>/abandon', methods=['POST'])
@login_required
def abandon_challenge(challenge_id):
    from flask import flash, redirect, url_for
    # Check if challenge is in progress
    in_progress = InProgressChallenge.query.filter_by(
        user_id=current_user.id,
        challenge_id=challenge_id
    ).first_or_404()
    
    # Remove from in progress
    db.session.delete(in_progress)
    db.session.commit()
    
    # Redirect to the challenges page
    flash('Challenge abandoned.', 'info')
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
