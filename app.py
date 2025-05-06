from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import os
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'main.game'  # Redirect unauthorized users to the game page which has the login form

@login_manager.user_loader
def load_user(id):
    from app.models import User
    return User.query.get(int(id))

def create_app(config_class=Config):
    app = Flask(__name__, 
                template_folder=os.path.join('app', 'templates'),
                static_folder=os.path.join('app', 'static'))
    
    # Configuration
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Import models (so they are registered with SQLAlchemy)
    from app.models import User, Challenge, CompletedChallenge, InProgressChallenge

    # Register blueprints
    from app.main_routes import bp as main_bp
    app.register_blueprint(main_bp)

    return app
