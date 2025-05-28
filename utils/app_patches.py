"""Application Patches

Contains patches and modifications to make the application work in different
environments, including database-disabled mode for static deployments.
"""

import os
from flask import current_app

def patch_app_for_db_disabled(app):
    """Apply patches to make the app work without a database
    
    This function patches key components of the application to use
    static data from JS files when the database is disabled.
    """
    # Check if DB is disabled
    disable_db = os.environ.get('DISABLE_DB', 'false').lower() == 'true'
    
    if not disable_db:
        # Database is enabled, no need for patches
        return
    
    app.logger.warning("Database disabled mode active. Using static data fallbacks.")
    
    # Import the original models to patch
    from app.models import Challenge
    
    # Import the fallback system
    from utils.db_fallback import MockChallenge, get_challenges_from_js
    
    # Override the Challenge query property to use the mock version
    Challenge.query = MockChallenge.query()
    
    # Log the number of challenges available via static file
    challenges = get_challenges_from_js()
    app.logger.info(f"Loaded {len(challenges)} challenges from static JS file")
    
    # Disable features that require database writing
    app.config['DB_WRITE_DISABLED'] = True
    
    # Log completion of patches
    app.logger.info("Successfully applied database-disabled mode patches")
