from app import create_app
from config import Config

app = create_app(Config)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5004)
    
from flask import Flask, render_template
import pandas as pd

app = Flask(__name__)

@app.route("/communities")
def communities():
    df = pd.read_csv("data/migrations/List of Communities - Sheet1 (1).csv")
    df.columns = df.columns.str.strip()  # Clean column names
    return render_template("communities5.html", communities=df.to_dict(orient="records"))

if __name__ == "__main__":
    app.run(debug=True)
