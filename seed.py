from app import create_app
from app.seed import seed_challenges

app = create_app()

with app.app_context():
    seed_challenges()
