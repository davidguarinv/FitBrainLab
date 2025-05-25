"""
Update achievements in the database with specific achievements requested by the user.
"""

import os
import sys
import sqlite3
from datetime import datetime

# Add the project directory to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from config import Config

def update_achievements():
    """Update achievements in the database with specific user-requested achievements."""
    print("Starting achievement update...")
    
    # Connect to the database
    db_path = Config.DATABASE_PATH
    print(f"Connecting to database at: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if icon column exists, add it if it doesn't
        cursor.execute("PRAGMA table_info(achievement)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "icon" not in columns:
            print("Adding icon column to achievement table")
            cursor.execute("ALTER TABLE achievement ADD COLUMN icon TEXT")
            conn.commit()
        
        # Clear existing achievements
        cursor.execute("DELETE FROM achievement")
        print("Cleared existing achievements")
        
        # Define new achievements
        achievements = [
            {
                "name": "Centurion",
                "condition": "100_total",
                "message": "You're on fire! Great job for staying on track and working on being more active one day at a time. Let's celebrate by attempting another challenge!",
                "points_reward": 200,
                "icon": "🔥"
            },
            {
                "name": "Challenge Master",
                "condition": "200_total",
                "message": "You have probably seen every challenge we have to offer. What a menace! Keep it up!",
                "points_reward": 400,
                "icon": "🏆"
            },
            {
                "name": "Easy Expert",
                "condition": "50_easy",
                "message": "You are starting to master bite sized activity boosts. Look at you thrive!",
                "points_reward": 150,
                "icon": "🌱"
            },
            {
                "name": "Medium Maven",
                "condition": "25_medium",
                "message": "You are on your way to becoming a superstar! We can't wait to see your life transform for the more active!",
                "points_reward": 200,
                "icon": "⭐"
            },
            {
                "name": "Hard Conqueror",
                "condition": "10_hard",
                "message": "Boss moves! What a tough cookie you are…",
                "points_reward": 250,
                "icon": "💪"
            },
            {
                "name": "Point Prodigy",
                "condition": "points_50000",
                "message": "Wowza! We notice your potential and drive. Incredible performance out there!",
                "points_reward": 500,
                "icon": "🌟"
            },
            {
                "name": "Ultimate Champion",
                "condition": "points_100000",
                "message": "We didn't think anyone would make it this far. You are officially insane and we hope you're enjoying the game.",
                "points_reward": 1000,
                "icon": "👑"
            }
        ]
        
        # Insert new achievements
        created_at = datetime.utcnow().isoformat()
        for achievement in achievements:
            cursor.execute(
                "INSERT INTO achievement (name, condition, message, points_reward, icon, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    achievement["name"],
                    achievement["condition"],
                    achievement["message"],
                    achievement["points_reward"],
                    achievement["icon"],
                    created_at
                )
            )
        
        # Commit changes
        conn.commit()
        
        # Verify achievements were inserted
        cursor.execute("SELECT COUNT(*) FROM achievement")
        count = cursor.fetchone()[0]
        print(f"Successfully inserted {count} achievements")
        
        # Show the achievements
        cursor.execute("SELECT id, name, condition, message, points_reward, icon FROM achievement")
        all_achievements = cursor.fetchall()
        for ach in all_achievements:
            print(f"ID: {ach[0]}, Name: {ach[1]}, Condition: {ach[2]}, Message: {ach[3]}, Points: {ach[4]}, Icon: {ach[5]}")
            
        # Add a total_points column to the user table if it doesn't exist
        cursor.execute("PRAGMA table_info(user)")
        columns = [col[1] for col in cursor.fetchall()]
        if "total_points" not in columns:
            print("Adding total_points column to user table")
            cursor.execute("ALTER TABLE user ADD COLUMN total_points INTEGER DEFAULT 0")
            conn.commit()
        
    except Exception as e:
        print(f"Error updating achievements: {str(e)}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()
    
    print("Achievement update completed successfully!")
    return True

if __name__ == "__main__":
    update_achievements()
