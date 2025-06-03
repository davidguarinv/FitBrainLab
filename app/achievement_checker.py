"""
Achievement checker for FitBrainLab.
This module handles checking achievement conditions and awarding achievements.
"""

from flask import flash
from sqlalchemy import func
from datetime import datetime

from app.models import (
    db, User, Achievement, UserAchievement, Challenge, 
    CompletedChallenge, FriendChallengeLink, WeeklyHabitChallenge
)

def check_user_achievements(user_id):
    """
    Check if the user has earned any new achievements.
    
    Args:
        user_id: ID of the user to check achievements for
        
    Returns:
        List of newly earned achievements
    """
    # Get the user
    user = User.query.get(user_id)
    if not user:
        return []
    
    # Get achievements the user has already earned
    earned_achievement_ids = [ua.achievement_id for ua in UserAchievement.query.filter_by(user_id=user_id).all()]
    
    # Get all possible achievements
    all_achievements = Achievement.query.all()
    
    newly_earned = []
    
    for achievement in all_achievements:
        # Skip if already earned
        if achievement.id in earned_achievement_ids:
            continue
            
        # Check conditions
        condition = achievement.condition
        earned = False
        
        # Total challenges
        if condition.endswith('_total'):
            count = int(condition.split('_')[0])
            total_completed = CompletedChallenge.query.filter_by(user_id=user_id).count()
            earned = total_completed >= count
            
        # Easy challenges
        elif condition.endswith('_easy'):
            count = int(condition.split('_')[0])
            easy_completed = CompletedChallenge.query.join(Challenge).filter(
                CompletedChallenge.user_id == user_id,
                Challenge.difficulty == 'E'
            ).count()
            earned = easy_completed >= count
            
        # Medium challenges
        elif condition.endswith('_medium'):
            count = int(condition.split('_')[0])
            medium_completed = CompletedChallenge.query.join(Challenge).filter(
                CompletedChallenge.user_id == user_id,
                Challenge.difficulty == 'M'
            ).count()
            earned = medium_completed >= count
            
        # Hard challenges
        elif condition.endswith('_hard'):
            count = int(condition.split('_')[0])
            hard_completed = CompletedChallenge.query.join(Challenge).filter(
                CompletedChallenge.user_id == user_id,
                Challenge.difficulty == 'H'
            ).count()
            earned = hard_completed >= count
            
        # Points threshold
        elif condition.startswith('points_'):
            points_threshold = int(condition.split('_')[1])
            
            # Calculate total points earned
            points_query = db.session.query(func.sum(CompletedChallenge.points_earned)).filter(
                CompletedChallenge.user_id == user_id
            )
            total_points = points_query.scalar() or 0
            
            earned = total_points >= points_threshold
            
        # Weekly all
        elif condition == 'weekly_all':
            earned = (user.weekly_e_completed >= user.weekly_e_cap and
                     user.weekly_m_completed >= user.weekly_m_cap and
                     user.weekly_h_completed >= user.weekly_h_cap)
            
        # Streak
        elif condition.startswith('streak_'):
            days = int(condition.split('_')[1])
            earned = user.daily_streak >= days
            
        # Friend challenges
        elif condition.startswith('friend_'):
            count = int(condition.split('_')[1])
            friend_completed = db.session.query(func.count(FriendChallengeLink.id)).filter(
                ((FriendChallengeLink.user1_id == user_id) & FriendChallengeLink.user1_confirmed) |
                ((FriendChallengeLink.user2_id == user_id) & FriendChallengeLink.user2_confirmed)
            ).scalar()
            earned = friend_completed >= count
            
        # Habit challenges
        elif condition.startswith('habit_'):
            count = int(condition.split('_')[1])
            habit_completed = WeeklyHabitChallenge.query.filter(
                WeeklyHabitChallenge.user_id == user_id,
                WeeklyHabitChallenge.days_completed == 7
            ).count()
            earned = habit_completed >= count
            
        # If earned, create a new UserAchievement
        if earned:
            new_achievement = UserAchievement(user_id=user_id, achievement_id=achievement.id)
            db.session.add(new_achievement)
            newly_earned.append({
                'id': achievement.id,
                'name': achievement.name,
                'message': achievement.message,
                'icon_type': achievement.icon_type,
                'condition': achievement.condition,
                'points_reward': achievement.points_reward
            })
            
            # Add the achievement points to the user's total
            # We would need to add a total_points field to the User model to track this
            
    if newly_earned:
        db.session.commit()
        
    return newly_earned


def display_achievement_notifications(achievements):
    """Display flash notifications for earned achievements."""
    for achievement in achievements:
        # Create a JavaScript object for the achievement data
        achievement_json = {
            'id': achievement['id'],
            'name': achievement['name'],
            'message': achievement['message'],
            'icon_type': achievement['icon_type'],
            'condition': achievement.get('condition', ''),
            'points_reward': achievement.get('points_reward', 0)
        }
        
        # Create a script tag that will call the showAchievementUnlock function
        flash(
            f"<script>"
            f"document.addEventListener('DOMContentLoaded', function() {{"
            f"    setTimeout(function() {{"
            f"        showAchievementUnlock({achievement_json});"
            f"    }}, 1000);"
            f"}});"
            f"</script>",
            'achievement'
        )
