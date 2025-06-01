#!/usr/bin/env python
"""
Initialize Supabase database with required tables and structure for FitBrainLab.
This script creates all necessary tables if they don't exist.
"""

import os
import sys
from dotenv import load_dotenv
import sqlalchemy as sa
from sqlalchemy import create_engine, MetaData, Table, Column
from sqlalchemy import Integer, String, Boolean, DateTime, Float, ForeignKey, Text

# Add parent directory to path to allow importing from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Build the connection string from Supabase environment variables
def get_connection_string():
    host = os.environ.get('SUPABASE_DB_HOST')
    port = os.environ.get('SUPABASE_DB_PORT')
    dbname = os.environ.get('SUPABASE_DB_NAME')
    user = os.environ.get('SUPABASE_DB_USER')
    password = os.environ.get('SUPABASE_DB_PASSWORD')
    
    if not all([host, port, dbname, user, password]):
        print("ERROR: Missing required Supabase environment variables")
        sys.exit(1)
    
    return f"postgresql://{user}:{password}@{host}:{port}/{dbname}"

def main():
    print("Connecting to Supabase database...")
    connection_string = get_connection_string()
    
    # Create SQLAlchemy engine
    try:
        engine = create_engine(connection_string)
        connection = engine.connect()
        print("Connection successful!")
    except Exception as e:
        print(f"Connection failed: {e}")
        sys.exit(1)
    
    # Create metadata object
    metadata = MetaData()
    
    # Define User table
    user_table = Table(
        "user",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("username", String(64), unique=True, nullable=False),
        Column("password_hash", String(256), nullable=False),
        Column("created_at", DateTime, nullable=False),
        Column("last_seen", DateTime),
        Column("is_public", Boolean, default=True),
        Column("points", Integer, default=0),
        Column("weekly_points", Integer, default=0),
        Column("weekly_e_cap", Integer, default=20),
        Column("weekly_m_cap", Integer, default=15),
        Column("weekly_h_cap", Integer, default=10),
        Column("weekly_e_count", Integer, default=0),
        Column("weekly_m_count", Integer, default=0),
        Column("weekly_h_count", Integer, default=0),
        Column("personal_code", String(20), unique=True),
        Column("backup_code", String(20), unique=True),
        Column("weekly_points_last_reset", DateTime),
        schema="public"
    )
    
    # Define Challenge table
    challenge_table = Table(
        "challenge",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("title", String(128), nullable=False),
        Column("description", Text, nullable=False),
        Column("difficulty", String(1), nullable=False),  # 'E', 'M', or 'H'
        Column("points", Integer, nullable=False),
        Column("created_at", DateTime, nullable=False),
        Column("category", String(64)),
        Column("time_estimate", String(64)),
        schema="public"
    )
    
    # Define CompletedChallenge table
    completed_challenge_table = Table(
        "completed_challenge",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("user_id", Integer, ForeignKey("public.user.id"), nullable=False),
        Column("challenge_id", Integer, ForeignKey("public.challenge.id"), nullable=False),
        Column("completed_at", DateTime, nullable=False),
        Column("points_awarded", Integer, nullable=False),
        Column("week_number", Integer),
        Column("year", Integer),
        schema="public"
    )
    
    # Define UserChallenge table (for in-progress challenges)
    user_challenge_table = Table(
        "user_challenge",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("user_id", Integer, ForeignKey("public.user.id"), nullable=False),
        Column("challenge_id", Integer, ForeignKey("public.challenge.id"), nullable=False),
        Column("started_at", DateTime, nullable=False),
        schema="public"
    )
    
    # Define ChallengeRegeneration table
    challenge_regeneration_table = Table(
        "challenge_regeneration",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("user_id", Integer, ForeignKey("public.user.id"), nullable=False),
        Column("difficulty", String(1), nullable=False),  # 'E', 'M', or 'H'
        Column("slot_index", Integer, nullable=False),
        Column("regenerate_at", DateTime, nullable=False),
        schema="public"
    )
    
    # Define WeeklyChallengeSet table
    weekly_challenge_set_table = Table(
        "weekly_challenge_set",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("week_number", Integer, nullable=False),
        Column("year", Integer, nullable=False),
        Column("challenge_ids_json", Text, nullable=False),
        schema="public"
    )
    
    # Define FriendChallengeLink table
    friend_challenge_link_table = Table(
        "friend_challenge_link",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("sender_id", Integer, ForeignKey("public.user.id"), nullable=False),
        Column("receiver_code", String(20), nullable=False),
        Column("challenge_id", Integer, ForeignKey("public.challenge.id"), nullable=False),
        Column("created_at", DateTime, nullable=False),
        Column("expires_at", DateTime, nullable=False),
        Column("completed", Boolean, default=False),
        Column("expired", Boolean, default=False),
        schema="public"
    )
    
    # Define FriendTokenUsage table
    friend_token_usage_table = Table(
        "friend_token_usage",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("user_id", Integer, ForeignKey("public.user.id"), nullable=False),
        Column("tokens_used_today", Integer, default=0),
        Column("last_usage_date", DateTime, nullable=False),
        schema="public"
    )
    
    # Define FunFact table
    fun_fact_table = Table(
        "fun_fact",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("fact", Text, nullable=False),
        Column("category", String(64)),
        schema="public"
    )
    
    # Define Notification table
    notification_table = Table(
        "notification",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("user_id", Integer, ForeignKey("public.user.id"), nullable=False),
        Column("message", Text, nullable=False),
        Column("read", Boolean, default=False),
        Column("created_at", DateTime, nullable=False),
        Column("notification_type", String(64)),
        Column("link", String(256)),
        schema="public"
    )
    
    # Define WeeklyHabitChallenge table
    weekly_habit_challenge_table = Table(
        "weekly_habit_challenge",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("challenge_id", Integer, ForeignKey("public.challenge.id"), nullable=False),
        Column("week_number", Integer, nullable=False),
        Column("year", Integer, nullable=False),
        schema="public"
    )
    
    # Define UserWeeklyOrder table
    user_weekly_order_table = Table(
        "user_weekly_order",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("user_id", Integer, ForeignKey("public.user.id"), nullable=False),
        Column("week_number", Integer, nullable=False),
        Column("year", Integer, nullable=False),
        Column("order_json", Text, nullable=False),
        schema="public"
    )
    
    # Define ChallengeOfTheWeek table
    challenge_of_the_week_table = Table(
        "challenge_of_the_week",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("challenge_id", Integer, ForeignKey("public.challenge.id"), nullable=False),
        Column("week_number", Integer, nullable=False),
        Column("year", Integer, nullable=False),
        schema="public"
    )
    
    # Create all tables
    print("Creating tables if they don't exist...")
    try:
        metadata.create_all(engine)
        print("Tables created successfully!")
    except Exception as e:
        print(f"Error creating tables: {e}")
        sys.exit(1)
    
    print("Database initialization complete.")

if __name__ == "__main__":
    main()
