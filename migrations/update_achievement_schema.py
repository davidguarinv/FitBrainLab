from app import db
from app.models import Achievement
from sqlalchemy import text

def run_migration():
    # Check if icon_type column exists
    result = db.session.execute(text("PRAGMA table_info(achievement)"))
    columns = [row[1] for row in result]
    
    # Add icon_type column if it doesn't exist
    if 'icon_type' not in columns:
        db.session.execute(text("ALTER TABLE achievement ADD COLUMN icon_type VARCHAR(50)"))
        print("Added icon_type column to achievement table")
    
    # Update achievements with icon_type values
    achievements = [
        {'condition': '1_total', 'icon_type': 'first_challenge'},
        {'condition': '10_total', 'icon_type': 'getting_started'},
        {'condition': '50_total', 'icon_type': 'challenge_enthusiast'},
        {'condition': '3_weekly_streak', 'icon_type': 'weekly_streak'},
        {'condition': '10_easy', 'icon_type': 'easy_beginner'},
        {'condition': '10_medium', 'icon_type': 'medium_beginner'},
        {'condition': '10_hard', 'icon_type': 'hard_beginner'}
    ]
    
    for achievement_data in achievements:
        achievement = Achievement.query.filter_by(condition=achievement_data['condition']).first()
        if achievement:
            achievement.icon_type = achievement_data['icon_type']
    
    db.session.commit()
    print("Updated icon_type values for achievements")
    
    # Check if points_reward column exists
    result = db.session.execute(text("PRAGMA table_info(achievement)"))
    columns = [row[1] for row in result]
    
    if 'points_reward' in columns:
        # SQLite doesn't support DROP COLUMN directly, so we need to:
        # 1. Create a new table without the column
        # 2. Copy data to the new table
        # 3. Drop the old table
        # 4. Rename the new table
        
        # Create a new table without points_reward
        db.session.execute(text("""
            CREATE TABLE achievement_new (
                id INTEGER PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                condition VARCHAR(50) NOT NULL,
                message VARCHAR(200) NOT NULL,
                icon_type VARCHAR(50)
            )
        """))
        
        # Copy data to the new table
        db.session.execute(text("""
            INSERT INTO achievement_new (id, name, condition, message, icon_type)
            SELECT id, name, condition, message, icon_type FROM achievement
        """))
        
        # Drop the old table
        db.session.execute(text("DROP TABLE achievement"))
        
        # Rename the new table
        db.session.execute(text("ALTER TABLE achievement_new RENAME TO achievement"))
        
        print("Removed points_reward column from achievement table")
    
    db.session.commit()
    print("Achievement schema update complete")

if __name__ == "__main__":
    run_migration()
