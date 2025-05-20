from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from datetime import datetime
from . import db
from .models import Challenge, CompletedChallenge, InProgressChallenge, User, ChallengeRegeneration

bp = Blueprint('api', __name__, url_prefix='/api')

@bp.route('/challenges/<int:challenge_id>/start', methods=['POST'])
@login_required
def start_challenge(challenge_id):
    from flask import flash, redirect, url_for
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
    
    # Set regeneration timer for this challenge slot
    # First, find which slot this challenge was in
    now = datetime.utcnow()
    all_challenges = Challenge.query.filter_by(difficulty=challenge.difficulty).all()
    available_challenges = [c for c in all_challenges if c.id != challenge_id]
    
    # Find the slot number for this difficulty
    slot_count = 3 if challenge.difficulty == 'E' else (2 if challenge.difficulty == 'M' else 1)
    
    # Find an available slot or create a new one
    regen_timer = ChallengeRegeneration.query.filter_by(
        difficulty=challenge.difficulty
    ).order_by(ChallengeRegeneration.slot_number).first()
    
    if not regen_timer:
        # Create a new regeneration timer
        slot_number = 1
        regen_timer = ChallengeRegeneration(
            difficulty=challenge.difficulty,
            slot_number=slot_number,
            regenerate_at=now + timedelta(hours=ChallengeRegeneration.get_regen_hours(challenge.difficulty))
        )
        db.session.add(regen_timer)
    else:
        # Update existing timer
        regen_timer.regenerate_at = now + timedelta(hours=ChallengeRegeneration.get_regen_hours(challenge.difficulty))
    
    db.session.commit()
    
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
