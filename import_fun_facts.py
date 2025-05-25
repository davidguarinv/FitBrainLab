import os
import json
import sys
from datetime import datetime

# Add the project directory to the path so we can import the app
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models import FunFact

def import_fun_facts():
    """
    Import all fun facts from the JSON file into the database.
    This script should be run once to ensure all facts are in the database
    before the JSON file is deleted.
    """
    app = create_app()
    
    with app.app_context():
        print("Starting fun facts import...")
        
        json_file = os.path.join(app.static_folder, 'data', 'fun_facts.json')
        if not os.path.exists(json_file):
            print(f"Error: Fun facts JSON file not found at {json_file}")
            return False
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check if we have exercise facts
            if 'exercise_facts' not in data:
                print("Error: No exercise_facts found in JSON file")
                return False
            
            # Get existing fact IDs to avoid duplicates
            existing_facts = {fact.id: fact for fact in FunFact.query.all()}
            print(f"Found {len(existing_facts)} existing facts in database")
            
            # Import facts
            total_facts = len(data['exercise_facts'])
            imported_count = 0
            already_exists_count = 0
            
            for fact_data in data['exercise_facts']:
                # Skip if already exists
                if fact_data['id'] in existing_facts:
                    already_exists_count += 1
                    continue
                
                new_fact = FunFact(
                    id=fact_data['id'],
                    fact=fact_data['fact'],
                    source=fact_data.get('source', '')
                )
                db.session.add(new_fact)
                imported_count += 1
            
            if imported_count > 0:
                db.session.commit()
                print(f"Successfully imported {imported_count} new fun facts")
            
            print(f"Import summary:")
            print(f"- Total facts in JSON: {total_facts}")
            print(f"- Already in database: {already_exists_count}")
            print(f"- Newly imported: {imported_count}")
            print(f"- Total facts in database: {len(existing_facts) + imported_count}")
            
            # Verify all facts are in the database
            all_db_facts = FunFact.query.count()
            if all_db_facts == total_facts:
                print("✅ All fun facts are now in the database!")
                print("✅ The JSON file can now be safely deleted.")
            else:
                print(f"⚠️ Warning: Database has {all_db_facts} facts, but JSON has {total_facts}")
                print("⚠️ Some facts may not have been imported correctly.")
            
            return True
        
        except Exception as e:
            print(f"Error importing fun facts: {str(e)}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    import_fun_facts()
