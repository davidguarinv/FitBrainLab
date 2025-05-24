from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import os
from config import Config

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'main.game'  # Redirect to game page which has login form

def create_app(config_class=Config):
    # Import models here to avoid circular imports
    from .models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    app = Flask(__name__, 
                static_folder='static',
                template_folder='templates')
    
    # Configuration
    app.config.from_object(config_class)
    app.config['DEBUG'] = True  # Enable debug mode
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Import models (so they are registered with SQLAlchemy)
    from .models import User, Challenge, CompletedChallenge, InProgressChallenge

    # Register blueprints with explicit URL prefixes
    from .routes import bp as main_bp
    from .api import bp as api_bp
    
    # Register main blueprint with explicit prefix
    app.register_blueprint(main_bp, url_prefix='/')
    
    # Register API blueprint
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Add detailed logging for route registration
    print("\nRegistered routes:")
    for rule in app.url_map.iter_rules():
        print(f"Endpoint: {rule.endpoint}, Methods: {rule.methods}, Rule: {rule}")
    print("\n")
    
    # Verify blueprint registration
    print("Blueprints registered:")
    for bp_name, bp in app.blueprints.items():
        print(f"Blueprint: {bp_name}, URL Prefix: {bp.url_prefix}")
    print("\n")

    # Create tables
    with app.app_context():
        db.create_all()

    # Print all routes for debugging
    print("\nRegistered routes:")
    for rule in app.url_map.iter_rules():
        print(f"Endpoint: {rule.endpoint}, Methods: {rule.methods}, Rule: {rule}")
    print("\n")

    return app
