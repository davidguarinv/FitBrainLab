import sqlite3
import os

# Ensure the instance directory exists
os.makedirs('instance', exist_ok=True)

# Create a test database
try:
    conn = sqlite3.connect('instance/fitbrainlab.db')
    print("Successfully created/connected to the database!")
    conn.close()
except Exception as e:
    print(f"Error creating database: {e}")

# Check if file was created
if os.path.exists('instance/fitbrainlab.db'):
    print("Database file exists at:", os.path.abspath('instance/fitbrainlab.db'))
else:
    print("Failed to create database file")
