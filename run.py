from app import create_app
from config import Config
import argparse

# Parse command line arguments
def parse_args():
    parser = argparse.ArgumentParser(description='Run the FitBrainLab application')
    parser.add_argument('--port', type=int, default=5004, help='Port to run the server on')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    return parser.parse_args()

app = create_app(Config)

# Initialize the weekly challenge scheduler
from utils.scheduler import init_app
init_app(app)

if __name__ == '__main__':
    args = parse_args()
    app.run(debug=args.debug or True, host='0.0.0.0', port=args.port)
