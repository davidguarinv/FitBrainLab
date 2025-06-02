from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    # Get all users without personal or backup codes
    users_without_codes = User.query.filter(
        (User.personal_code.is_(None)) | 
        (User.backup_code.is_(None))
    ).all()
    
    print(f"Found {len(users_without_codes)} users without codes")
    
    # Generate missing codes for each user
    for user in users_without_codes:
        if user.personal_code is None:
            user.generate_personal_code()
            print(f"Generated personal code for {user.username}: {user.personal_code}")
        
        if user.backup_code is None:
            user.generate_backup_code()
            print(f"Generated backup code for {user.username}: {user.backup_code}")
    
    # Commit changes to the database
    db.session.commit()
    print("\nAll codes generated and saved to the database")
