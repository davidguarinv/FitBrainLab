from app import create_app
from config import Config

app = create_app(Config)

# Initialize the weekly challenge scheduler
from utils.scheduler import init_app
init_app(app)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5006)
