import sys
import os

# Add parent directory to path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import Achievement

app = create_app()

with app.app_context():
    # With the new Achievement implementation, we just need to call the seed method
    # which refreshes the in-memory cache
    count = Achievement.seed_achievements()
    print(f"Successfully initialized {count} achievements")
