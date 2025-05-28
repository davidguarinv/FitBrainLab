from app import create_app
from config import Config

# Create application with production configuration
app = create_app(Config)
