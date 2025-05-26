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
    from .simple_models import SimpleUser
    
    @login_manager.user_loader
    def load_user(user_id):
        # First try to load from the original User model
        user = User.query.get(int(user_id))
        if user:
            return user
        
        # If not found, try to load from the SimpleUser model
        return SimpleUser.query.get(int(user_id))
    
    app = Flask(__name__, 
                static_folder='../static',
                template_folder='../templates')
    
    # Configuration
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Import models (so they are registered with SQLAlchemy)
    from .models import User, Challenge, CompletedChallenge, FunFact

    # Register blueprints
    from .routes import bp as main_bp
    app.register_blueprint(main_bp, url_prefix='')
    
    # Register the simple auth blueprint
    from .simple_auth import bp as simple_auth_bp
    app.register_blueprint(simple_auth_bp, url_prefix='')

    # Create tables
    with app.app_context():
        db.create_all()
        
        # Import fun facts from JSON file
        FunFact.import_from_json(app)

    return app
