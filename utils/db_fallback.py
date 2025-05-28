"""Database Fallback Handler

This module provides fallback mechanisms when the database is disabled or unavailable.
It allows the application to continue functioning with static data from JavaScript files.
"""

import json
import os
import re
from flask import current_app

# Cache for challenges and other data to avoid repeated parsing
_challenges_cache = None

def get_challenges_from_js():
    """Extract challenges from the JavaScript file when database is unavailable"""
    global _challenges_cache
    
    # Return cached challenges if available
    if _challenges_cache is not None:
        return _challenges_cache
    
    # Path to the challenges.js file
    js_file_path = os.path.join(current_app.root_path, 'static', 'js', 'challenges.js')
    
    try:
        with open(js_file_path, 'r') as f:
            content = f.read()
            
        # Extract challenges array from the JavaScript file
        pattern = r'const challenges = \[(.*?)\];'
        match = re.search(pattern, content, re.DOTALL)
        
        if not match:
            current_app.logger.error("Could not parse challenges from JavaScript file")
            return []
            
        challenges_str = match.group(1).strip()
        
        # Convert JavaScript syntax to Python
        challenges_str = challenges_str.replace('//', '#')  # Convert comments
        
        # Convert the string to a Python list
        challenges_list = json.loads(f"[{challenges_str}]")
        
        # Cache the result
        _challenges_cache = challenges_list
        return challenges_list
        
    except Exception as e:
        current_app.logger.error(f"Error importing challenges: {e}")
        return []

# Mock Challenge class for DB-less operation
class MockChallenge:
    """Mock Challenge class that mimics the database model for DB-less operation"""
    
    def __init__(self, data):
        self.id = data.get('id', 0)
        self.title = data.get('title', '')
        self.description = data.get('description', '')
        self.difficulty = data.get('difficulty', 'E')
        self.points = data.get('points', 0)
        self.regen_hours = 4 if data.get('difficulty') == 'E' else 6 if data.get('difficulty') == 'M' else 8
        
    @classmethod
    def query(cls):
        return MockQuery(cls)

class MockQuery:
    """Mock Query class to simulate database queries"""
    
    def __init__(self, model_class):
        self.model_class = model_class
        self.filters = []
    
    def filter_by(self, **kwargs):
        self.filters.append(kwargs)
        return self
    
    def all(self):
        if self.model_class == MockChallenge:
            challenges = get_challenges_from_js()
            # Apply filters if any
            if self.filters:
                for filter_dict in self.filters:
                    challenges = [c for c in challenges if all(
                        c.get(k) == v for k, v in filter_dict.items()
                    )]
            return [MockChallenge(c) for c in challenges]
        return []
