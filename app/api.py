from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from datetime import datetime
from . import db
from .models import Challenge, CompletedChallenge, InProgressChallenge, User

bp = Blueprint('api', __name__, url_prefix='/api')

@bp.route('/challenges/<int:challenge_id>/start', methods=['POST'])
@login_required
def start_challenge(challenge_id):
    challenge = Challenge.query.get_or_404(challenge_id)
    
    # Check if user can take this challenge
    if not current_user.can_take_challenge(challenge.difficulty):
        return jsonify({
            'success': False,
            'message': f'You have reached your daily limit for {challenge.difficulty} challenges'
        })
    
    # Check if challenge is already in progress
    if InProgressChallenge.query.filter_by(
        user_id=current_user.id,
        challenge_id=challenge_id
    ).first():
        return jsonify({
            'success': False,
            'message': 'Challenge already in progress'
        })
    
    # Start the challenge
    in_progress = InProgressChallenge(
        user_id=current_user.id,
        challenge_id=challenge_id
    )
    db.session.add(in_progress)
    db.session.commit()
    
    return jsonify({'success': True})

@bp.route('/challenges/<int:challenge_id>/complete', methods=['POST'])
@login_required
def complete_challenge(challenge_id):
    # Check if challenge is in progress
    in_progress = InProgressChallenge.query.filter_by(
        user_id=current_user.id,
        challenge_id=challenge_id
    ).first_or_404()
    
    challenge = Challenge.query.get_or_404(challenge_id)
    
    # Complete the challenge
    completed = CompletedChallenge(
        user_id=current_user.id,
        challenge_id=challenge_id
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
    
    return jsonify({'success': True})

@bp.route('/challenges/<int:challenge_id>/abandon', methods=['POST'])
@login_required
def abandon_challenge(challenge_id):
    # Check if challenge is in progress
    in_progress = InProgressChallenge.query.filter_by(
        user_id=current_user.id,
        challenge_id=challenge_id
    ).first_or_404()
    
    # Remove from in progress
    db.session.delete(in_progress)
    db.session.commit()
    
    return jsonify({'success': True})

@bp.route('/profile/toggle-visibility', methods=['POST'])
@login_required
def toggle_profile_visibility():
    current_user.is_public = not current_user.is_public
    db.session.commit()
    return jsonify({
        'success': True,
        'is_public': current_user.is_public
    })
