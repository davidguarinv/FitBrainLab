from datetime import datetime
from .models import db, Challenge

def seed_challenges():
    """Seed the database with challenges."""
    
    # Only seed if no challenges exist
    if Challenge.query.first():
        return
        
    challenges = [
        # Easy Challenges
        {
            'title': 'Morning Stretch',
            'description': 'Start your day with 10 minutes of stretching exercises',
            'difficulty': 'E',
            'points': 50
        },
        {
            'title': 'Quick Walk',
            'description': 'Take a 15-minute walk around your neighborhood',
            'difficulty': 'E',
            'points': 50
        },
        {
            'title': 'Desk Exercises',
            'description': 'Do 5 minutes of desk exercises during your work break',
            'difficulty': 'E',
            'points': 50
        },
        {
            'title': 'Stair Climbing',
            'description': 'Take the stairs instead of elevator for all trips today',
            'difficulty': 'E',
            'points': 50
        },
        {
            'title': 'Dance Break',
            'description': 'Have a 5-minute dance break to your favorite song',
            'difficulty': 'E',
            'points': 50
        },
        
        # Medium Challenges
        {
            'title': 'Jogging Session',
            'description': 'Go for a 30-minute jog at your own pace',
            'difficulty': 'M',
            'points': 100
        },
        {
            'title': 'Strength Training',
            'description': 'Complete 3 sets of 10 pushups, squats, and lunges',
            'difficulty': 'M',
            'points': 100
        },
        {
            'title': 'Yoga Flow',
            'description': 'Follow a 30-minute yoga flow video',
            'difficulty': 'M',
            'points': 100
        },
        {
            'title': 'Cycling Adventure',
            'description': 'Go for a 45-minute bike ride',
            'difficulty': 'M',
            'points': 100
        },
        
        # Hard Challenges
        {
            'title': 'Distance Run',
            'description': 'Complete a 5K run at your own pace',
            'difficulty': 'H',
            'points': 200
        },
        {
            'title': 'HIIT Workout',
            'description': 'Complete a 45-minute high-intensity interval training session',
            'difficulty': 'H',
            'points': 200
        },
        {
            'title': 'Endurance Challenge',
            'description': 'Complete 1 hour of continuous cardio exercise',
            'difficulty': 'H',
            'points': 200
        }
    ]
    
    for c in challenges:
        challenge = Challenge(**c)
        db.session.add(challenge)
    
    db.session.commit()
