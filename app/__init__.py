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
    
    # Register API blueprint
    from .api import bp as api_bp
    app.register_blueprint(api_bp)

    # Check if database is disabled
    disable_db = app.config.get('SQLALCHEMY_DATABASE_URI') is None or \
                 os.environ.get('DISABLE_DB', 'false').lower() == 'true'
                 
    if not disable_db:
        # Create tables if database is enabled
        with app.app_context():
            try:
                db.create_all()
                
                # Import fun facts from JSON file
                FunFact.import_from_json(app)
            except Exception as e:
                app.logger.error(f"Error during database initialization: {e}")
    else:
        # Apply patches for database-disabled mode
        try:
            from utils.app_patches import patch_app_for_db_disabled
            with app.app_context():
                patch_app_for_db_disabled(app)
        except Exception as e:
            app.logger.error(f"Error applying DB-disabled patches: {e}")

    return app
