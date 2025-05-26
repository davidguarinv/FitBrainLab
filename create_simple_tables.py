from app import create_app, db
from app.simple_models import SimpleUser

app = create_app()

with app.app_context():
    print("Creating simple_user table...")
    db.create_all()
    print("Tables created successfully!")
    
    # Check if the table was created
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print(f"Available tables: {tables}")
    
    if 'simple_user' in tables:
        print("simple_user table created successfully!")
        # Check columns
        columns = [col['name'] for col in inspector.get_columns('simple_user')]
        print(f"Columns in simple_user table: {columns}")
    else:
        print("simple_user table not created!")
