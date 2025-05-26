from app import create_app, db
from app.models import FriendTokenUsage

app = create_app()

with app.app_context():
    # Check if the table already exists
    inspector = db.inspect(db.engine)
    existing_tables = inspector.get_table_names()
    
    if 'friend_token_usage' not in existing_tables:
        print("Creating friend_token_usage table...")
        # Create the table
        FriendTokenUsage.__table__.create(db.engine)
        print("friend_token_usage table created successfully!")
    else:
        print("friend_token_usage table already exists.")
