from app import create_app
from app.models import db, Achievement

app = create_app()

with app.app_context():
    # First clear existing achievements
    Achievement.query.delete()
    db.session.commit()
    
    # Seed new achievements
    count = Achievement.seed_achievements()
    print(f"Successfully seeded {count} achievements")
