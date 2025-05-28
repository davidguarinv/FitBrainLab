-- FitBrainLab Supabase Schema
-- This script creates all tables and relationships needed for the application

-- Enable UUID extension (needed for certain ID fields)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Clear existing tables if needed (uncomment if you want to reset everything)
-- DROP TABLE IF EXISTS challenge_of_the_week CASCADE;
-- DROP TABLE IF EXISTS weekly_habit_challenge CASCADE;
-- DROP TABLE IF EXISTS user_weekly_order CASCADE;
-- DROP TABLE IF EXISTS friend_challenge_link CASCADE;
-- DROP TABLE IF EXISTS friend_token_usage CASCADE;
-- DROP TABLE IF EXISTS notification CASCADE;
-- DROP TABLE IF EXISTS user_achievement CASCADE;
-- DROP TABLE IF EXISTS achievement CASCADE;
-- DROP TABLE IF EXISTS user_challenge CASCADE;
-- DROP TABLE IF EXISTS weekly_challenge_set CASCADE;
-- DROP TABLE IF EXISTS challenge_regeneration CASCADE;
-- DROP TABLE IF EXISTS completed_challenge CASCADE;
-- DROP TABLE IF EXISTS challenge CASCADE;
-- DROP TABLE IF EXISTS "user" CASCADE;

-- -------------------------
-- User Table
-- -------------------------
CREATE TABLE IF NOT EXISTS "user" (
    id SERIAL PRIMARY KEY,
    username VARCHAR(64) UNIQUE NOT NULL,
    password_hash VARCHAR(128),
    is_public BOOLEAN DEFAULT TRUE,
    top_sport_category VARCHAR(50),
    last_sport_update TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_challenge_date DATE,
    daily_e_count INTEGER DEFAULT 0,
    daily_m_count INTEGER DEFAULT 0,
    daily_h_count INTEGER DEFAULT 0,
    last_week_visited INTEGER,
    last_year_visited INTEGER,
    backup_code VARCHAR(16) UNIQUE,
    personal_code VARCHAR(10) UNIQUE,
    weekly_e_cap INTEGER DEFAULT 9,
    weekly_m_cap INTEGER DEFAULT 6,
    weekly_h_cap INTEGER DEFAULT 3,
    weekly_e_completed INTEGER DEFAULT 0,
    weekly_m_completed INTEGER DEFAULT 0,
    weekly_h_completed INTEGER DEFAULT 0
);

-- -------------------------
-- Challenge Table
-- -------------------------
CREATE TABLE IF NOT EXISTS challenge (
    id SERIAL PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    description VARCHAR(500) NOT NULL,
    difficulty VARCHAR(1) NOT NULL,
    points INTEGER NOT NULL,
    regen_hours INTEGER DEFAULT 6,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- -------------------------
-- Completed Challenge Table
-- -------------------------
CREATE TABLE IF NOT EXISTS completed_challenge (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES "user" (id) ON DELETE CASCADE NOT NULL,
    challenge_id INTEGER REFERENCES challenge (id) ON DELETE CASCADE NOT NULL,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    points_earned INTEGER,
    week_number INTEGER,
    year INTEGER,
    friend_linked BOOLEAN DEFAULT FALSE
);

-- -------------------------
-- Challenge Regeneration Table
-- -------------------------
CREATE TABLE IF NOT EXISTS challenge_regeneration (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES "user" (id) ON DELETE CASCADE NOT NULL,
    difficulty VARCHAR(1) NOT NULL,
    regenerate_at TIMESTAMP NOT NULL,
    slot_number INTEGER NOT NULL,
    UNIQUE (user_id, difficulty, slot_number)
);

-- -------------------------
-- Weekly Challenge Set Table
-- -------------------------
CREATE TABLE IF NOT EXISTS weekly_challenge_set (
    id SERIAL PRIMARY KEY,
    week_number INTEGER NOT NULL,
    year INTEGER NOT NULL,
    difficulty VARCHAR(1) NOT NULL,
    challenge_id INTEGER REFERENCES challenge (id) ON DELETE CASCADE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (week_number, year, challenge_id)
);

-- -------------------------
-- User Challenge Table (in-progress challenges)
-- -------------------------
CREATE TABLE IF NOT EXISTS user_challenge (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES "user" (id) ON DELETE CASCADE NOT NULL,
    challenge_id INTEGER REFERENCES challenge (id) ON DELETE CASCADE NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, challenge_id)
);

-- -------------------------
-- Achievement Table
-- -------------------------
CREATE TABLE IF NOT EXISTS achievement (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    message VARCHAR(200) NOT NULL,
    icon_type VARCHAR(50) NOT NULL,
    criteria VARCHAR(100) NOT NULL,
    threshold INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- -------------------------
-- User Achievement Table
-- -------------------------
CREATE TABLE IF NOT EXISTS user_achievement (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES "user" (id) ON DELETE CASCADE NOT NULL,
    achievement_id INTEGER NOT NULL,
    achieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, achievement_id)
);

-- -------------------------
-- Notification Table
-- -------------------------
CREATE TABLE IF NOT EXISTS notification (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES "user" (id) ON DELETE CASCADE NOT NULL,
    title VARCHAR(100) NOT NULL,
    message VARCHAR(500) NOT NULL,
    type VARCHAR(50) DEFAULT 'info',
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- -------------------------
-- Friend Token Usage Table
-- -------------------------
CREATE TABLE IF NOT EXISTS friend_token_usage (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES "user" (id) ON DELETE CASCADE NOT NULL,
    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_weekly BOOLEAN DEFAULT FALSE,
    week_number INTEGER,
    year INTEGER
);

-- Create a partial unique index for weekly token usage
CREATE UNIQUE INDEX IF NOT EXISTS idx_friend_token_weekly
ON friend_token_usage (user_id, week_number, year)
WHERE is_weekly = TRUE;

-- -------------------------
-- Friend Challenge Link Table
-- -------------------------
CREATE TABLE IF NOT EXISTS friend_challenge_link (
    id SERIAL PRIMARY KEY,
    challenge_id INTEGER REFERENCES challenge (id) ON DELETE CASCADE NOT NULL,
    initiator_id INTEGER REFERENCES "user" (id) ON DELETE CASCADE NOT NULL,
    recipient_code VARCHAR(10) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    expires_at TIMESTAMP,
    expired BOOLEAN DEFAULT FALSE,
    recipient_id INTEGER REFERENCES "user" (id) ON DELETE CASCADE
);

-- -------------------------
-- User Weekly Order Table
-- -------------------------
CREATE TABLE IF NOT EXISTS user_weekly_order (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES "user" (id) ON DELETE CASCADE NOT NULL,
    week_number INTEGER NOT NULL,
    year INTEGER NOT NULL,
    challenge_order JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, week_number, year)
);

-- -------------------------
-- Weekly Habit Challenge Table
-- -------------------------
CREATE TABLE IF NOT EXISTS weekly_habit_challenge (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES "user" (id) ON DELETE CASCADE NOT NULL,
    week_number INTEGER NOT NULL,
    year INTEGER NOT NULL,
    title VARCHAR(100) NOT NULL,
    description VARCHAR(500) NOT NULL,
    points INTEGER NOT NULL,
    last_checkin DATE,
    checkin_streak INTEGER DEFAULT 0,
    completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, week_number, year)
);

-- -------------------------
-- Challenge of the Week Table
-- -------------------------
CREATE TABLE IF NOT EXISTS challenge_of_the_week (
    id SERIAL PRIMARY KEY,
    week_number INTEGER NOT NULL,
    year INTEGER NOT NULL,
    challenge_id INTEGER REFERENCES challenge (id) ON DELETE CASCADE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (week_number, year)
);

-- Create indexes for frequently queried fields
CREATE INDEX IF NOT EXISTS idx_user_username ON "user" (username);
CREATE INDEX IF NOT EXISTS idx_completed_challenge_user_id ON completed_challenge (user_id);
CREATE INDEX IF NOT EXISTS idx_completed_challenge_week_year ON completed_challenge (week_number, year);
CREATE INDEX IF NOT EXISTS idx_user_challenge_user_id ON user_challenge (user_id);
CREATE INDEX IF NOT EXISTS idx_weekly_challenge_set_week_year ON weekly_challenge_set (week_number, year);
