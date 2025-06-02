from app import create_app, db
from app.models import WeeklyChallengeSet, Challenge
from utils.scheduler import get_current_week_info

app = create_app()
with app.app_context():
    week = get_current_week_info()
    s = WeeklyChallengeSet.query.filter_by(week_number=week['week_number'], year=week['year']).all()
    print(f'WEEK {week["week_number"]}, {week["year"]}')
    for w in s:
        c = Challenge.query.get(w.challenge_id)
        print(f'{w.difficulty}: {c.id} - {c.title}')
