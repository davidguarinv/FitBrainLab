from app import create_app
from config import Config

app = create_app(Config)

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5004)
