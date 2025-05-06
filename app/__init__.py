from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'main.game'  # Redirect to game page which has login form

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Flask extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Import models here so Alembic and login manager can access them
    with app.app_context():
        from .models import User
        
        @login_manager.user_loader
        def load_user(id):
            return User.query.get(int(id))

    # Register blueprints
    from .main_routes import bp as main_bp
    app.register_blueprint(main_bp)

    # Create tables
    with app.app_context():
        db.create_all()

    return app
