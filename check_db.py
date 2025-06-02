from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    # Check if columns exist in the model
    print('Backup code attribute exists:', hasattr(User, 'backup_code'))
    print('Personal code attribute exists:', hasattr(User, 'personal_code'))
    
    # Check if columns exist in the database
    inspector = db.inspect(db.engine)
    columns = [column['name'] for column in inspector.get_columns('user')]
    print('\nDatabase columns in user table:', columns)
    print('\nbackup_code in columns:', 'backup_code' in columns)
    print('personal_code in columns:', 'personal_code' in columns)
    
    # Check sample user data
    user = User.query.first()
    if user:
        print('\nSample user data:')
        print(f'Username: {user.username}')
        print(f'Backup code: {user.backup_code}')
        print(f'Personal code: {user.personal_code}')
    else:
        print('\nNo users found in database')
