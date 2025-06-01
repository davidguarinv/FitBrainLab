#!/usr/bin/env python
"""
Script to directly fix the Supabase database by executing raw SQL files
and manually adding challenges and weekly challenge sets.
"""

import os
import sys
import logging
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Database connection parameters
DB_HOST = os.getenv("SUPABASE_DB_HOST")
DB_PORT = os.getenv("SUPABASE_DB_PORT")
DB_NAME = os.getenv("SUPABASE_DB_NAME")
DB_USER = os.getenv("SUPABASE_DB_USER")
DB_PASSWORD = os.getenv("SUPABASE_DB_PASSWORD")

def connect_to_db():
    """Connect to the Supabase PostgreSQL database."""
    logger.info("Connecting to Supabase PostgreSQL database...")
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        raise

def execute_sql_file(conn, file_path):
    """Execute a SQL file."""
    logger.info(f"Executing SQL from: {file_path}")
    try:
        with open(file_path, 'r') as file:
            sql = file.read()
            
        with conn.cursor() as cursor:
            cursor.execute(sql)
            conn.commit()
        
        logger.info(f"Successfully executed: {file_path}")
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"Error executing {file_path}: {e}")
        return False

def check_challenges(conn):
    """Check if challenges exist in the database."""
    with conn.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM challenge")
        count = cursor.fetchone()[0]
    return count

def check_weekly_challenges(conn):
    """Check if weekly challenges exist for the current week."""
    now = datetime.now()
    week_number = now.isocalendar()[1]
    year = now.year
    
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*) FROM weekly_challenge_set WHERE week_number = %s AND year = %s",
            (week_number, year)
        )
        count = cursor.fetchone()[0]
    
    return count, week_number, year

def create_challenges(conn):
    """Create basic challenges if none exist."""
    try:
        with conn.cursor() as cursor:
            # Insert some basic challenges
            difficulties = ['E', 'M', 'H']
            challenge_template = """
            INSERT INTO challenge (
                title, description, instructions, points, difficulty, 
                duration_minutes, category, content_url, needs_review, badge_id
            ) VALUES (
                %s, %s, %s, %s, %s, 
                %s, %s, %s, %s, NULL
            )
            """
            
            # Define some example challenges
            example_challenges = []
            
            # Easy challenges
            for i in range(1, 16):
                example_challenges.append((
                    f"Memory Match Level {i}",
                    f"Match pairs of cards to test your memory. Level {i}",
                    f"Click on cards to flip them and find matching pairs. Complete the level in under 2 minutes.",
                    10,
                    'E',
                    5,
                    'Memory',
                    f"/games/memory/{i}",
                    False
                ))
            
            # Medium challenges
            for i in range(1, 11):
                example_challenges.append((
                    f"Number Sequence Level {i}",
                    f"Find the pattern in number sequences. Level {i}",
                    f"Identify the missing number in the sequence. You have 3 minutes to solve 5 problems.",
                    20,
                    'M',
                    10,
                    'Logic',
                    f"/games/sequence/{i}",
                    False
                ))
            
            # Hard challenges
            for i in range(1, 6):
                example_challenges.append((
                    f"Word Association Master Level {i}",
                    f"Advanced word association puzzles. Level {i}",
                    f"Connect words with complex relationships. Solve 10 puzzles in 5 minutes.",
                    30,
                    'H',
                    15,
                    'Language',
                    f"/games/wordassoc/{i}",
                    False
                ))
            
            # Insert all challenges
            for challenge in example_challenges:
                cursor.execute(challenge_template, challenge)
            
            conn.commit()
            logger.info(f"Created {len(example_challenges)} sample challenges")
            return True
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating sample challenges: {e}")
        return False

def create_weekly_challenges(conn, week_number, year):
    """Create weekly challenges for the current week."""
    try:
        with conn.cursor() as cursor:
            # First get the challenge IDs by difficulty
            cursor.execute("SELECT id, difficulty FROM challenge")
            challenges = cursor.fetchall()
            
            # Group by difficulty
            by_difficulty = {'E': [], 'M': [], 'H': []}
            for challenge_id, diff in challenges:
                by_difficulty[diff].append(challenge_id)
            
            # Insert weekly challenges
            insert_sql = """
            INSERT INTO weekly_challenge_set (week_number, year, difficulty, challenge_id)
            VALUES (%s, %s, %s, %s)
            """
            
            # Select challenges per difficulty
            counts = {'E': 15, 'M': 10, 'H': 5}
            inserted = 0
            
            for diff, ids in by_difficulty.items():
                # Take up to the count needed for this difficulty
                count = min(counts[diff], len(ids))
                
                for i in range(count):
                    challenge_id = ids[i]
                    cursor.execute(insert_sql, (week_number, year, diff, challenge_id))
                    inserted += 1
            
            conn.commit()
            logger.info(f"Created {inserted} weekly challenges for week {week_number}/{year}")
            return True
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating weekly challenges: {e}")
        return False

def main():
    """Main function to fix the Supabase database."""
    try:
        conn = connect_to_db()
        
        # Check if challenges exist
        challenge_count = check_challenges(conn)
        logger.info(f"Found {challenge_count} challenges in database")
        
        # Check if weekly challenges exist
        weekly_count, week_number, year = check_weekly_challenges(conn)
        logger.info(f"Found {weekly_count} weekly challenges for week {week_number}/{year}")
        
        # If no challenges, try to execute the seed script
        if challenge_count == 0:
            logger.info("No challenges found, trying to run seed script...")
            seed_path = os.path.join(os.path.dirname(__file__), 'seed_supabase_challenges.sql')
            
            if os.path.exists(seed_path):
                success = execute_sql_file(conn, seed_path)
                if not success:
                    logger.info("Seed script failed, creating sample challenges...")
                    create_challenges(conn)
            else:
                logger.info("Seed script not found, creating sample challenges...")
                create_challenges(conn)
            
            # Check again
            challenge_count = check_challenges(conn)
            logger.info(f"Now have {challenge_count} challenges in database")
        
        # If no weekly challenges for current week, create them
        if weekly_count < 15:
            logger.info(f"Only {weekly_count} weekly challenges for current week, creating more...")
            
            # First delete existing weekly challenges to avoid conflicts
            with conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM weekly_challenge_set WHERE week_number = %s AND year = %s",
                    (week_number, year)
                )
                conn.commit()
            
            create_weekly_challenges(conn, week_number, year)
            
            # Check again
            weekly_count, _, _ = check_weekly_challenges(conn)
            logger.info(f"Now have {weekly_count} weekly challenges for current week")
        
        conn.close()
        logger.info("Database repair completed successfully")
        
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()
