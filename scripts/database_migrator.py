#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Database Migration Utility

This script helps migrate FitBrainLab from SQLite to a production database.
It extracts data from a SQLite database and creates JSON files that can be used
to seed a new database in production environments.

Usage:
    python database_migrator.py extract  # Extract data from SQLite
    python database_migrator.py create   # Create tables in new database
"""

import os
import sys
import json
import datetime
from app import create_app, db
from app.models import User, Challenge, CompletedChallenge, Achievement, UserAchievement
from config import Config

app = create_app(Config)

# Helper function for JSON serialization
def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def extract_challenges():
    """Extract challenges from SQLite to JSON"""
    with app.app_context():
        challenges = Challenge.query.all()
        data = []
        for challenge in challenges:
            data.append({
                'id': challenge.id,
                'title': challenge.title,
                'description': challenge.description,
                'category': challenge.category,
                'difficulty': challenge.difficulty,
                'tips': challenge.tips,
                'default_duration': challenge.default_duration,
                'equipment_required': challenge.equipment_required,
                'variation_parent_id': challenge.variation_parent_id,
                'created_at': json_serial(challenge.created_at),
                'active': challenge.active
            })
        
        output_file = os.path.join(app.root_path, '..', 'data', 'challenges.json')
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({'challenges': data}, f, indent=2, default=json_serial)
            
        print(f"Extracted {len(data)} challenges to {output_file}")

def extract_user_achievements():
    """Extract user achievements from SQLite to JSON"""
    with app.app_context():
        user_achievements = UserAchievement.query.all()
        data = []
        for ua in user_achievements:
            data.append({
                'id': ua.id,
                'user_id': ua.user_id,
                'achievement_id': ua.achievement_id,
                'achieved_at': json_serial(ua.achieved_at)
            })
        
        output_file = os.path.join(app.root_path, '..', 'data', 'user_achievements.json')
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({'user_achievements': data}, f, indent=2, default=json_serial)
            
        print(f"Extracted {len(data)} user achievements to {output_file}")

def extract_completed_challenges():
    """Extract completed challenges from SQLite to JSON"""
    with app.app_context():
        completed = CompletedChallenge.query.all()
        data = []
        for cc in completed:
            data.append({
                'id': cc.id,
                'user_id': cc.user_id,
                'challenge_id': cc.challenge_id,
                'completed_at': json_serial(cc.completed_at),
                'duration': cc.duration,
                'notes': cc.notes,
                'points': cc.points
            })
        
        output_file = os.path.join(app.root_path, '..', 'data', 'completed_challenges.json')
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({'completed_challenges': data}, f, indent=2, default=json_serial)
            
        print(f"Extracted {len(data)} completed challenges to {output_file}")

def extract_users():
    """Extract user data from SQLite to JSON"""
    with app.app_context():
        users = User.query.all()
        data = []
        for user in users:
            # Exclude sensitive information and include only essential fields
            data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'points': user.points,
                'weekly_e_cap': user.weekly_e_cap,
                'weekly_m_cap': user.weekly_m_cap,
                'weekly_h_cap': user.weekly_h_cap,
                'weekly_e_completed': user.weekly_e_completed,
                'weekly_m_completed': user.weekly_m_completed,
                'weekly_h_completed': user.weekly_h_completed,
                'last_weekly_reset': json_serial(user.last_weekly_reset) if user.last_weekly_reset else None,
                'last_login': json_serial(user.last_login) if user.last_login else None,
                'created_at': json_serial(user.created_at)
            })
        
        output_file = os.path.join(app.root_path, '..', 'data', 'users.json')
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({'users': data}, f, indent=2, default=json_serial)
            
        print(f"Extracted {len(data)} users to {output_file}")

def create_database_tables():
    """Create database tables in the new database"""
    with app.app_context():
        db.create_all()
        print("Created all database tables")

def main():
    if len(sys.argv) < 2:
        print("Usage: python database_migrator.py [extract|create]")
        sys.exit(1)
        
    command = sys.argv[1].lower()
    
    if command == 'extract':
        print("Extracting data from SQLite database...")
        # Make sure data directory exists
        os.makedirs(os.path.join(app.root_path, '..', 'data'), exist_ok=True)
        
        extract_challenges()
        extract_user_achievements()
        extract_completed_challenges()
        extract_users()
        print("Data extraction complete")
        
    elif command == 'create':
        print("Creating tables in new database...")
        create_database_tables()
        print("Database creation complete")
        
    else:
        print(f"Unknown command: {command}")
        print("Usage: python database_migrator.py [extract|create]")
        sys.exit(1)

if __name__ == "__main__":
    main()
