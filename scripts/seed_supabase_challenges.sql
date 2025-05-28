-- FitBrainLab Challenge Seed Script for Supabase
-- This script adds the initial challenges to the database

-- First, let's clear existing challenges if needed
-- TRUNCATE TABLE challenge CASCADE;

-- Seed the challenges table with initial challenges
INSERT INTO challenge (title, description, difficulty, points, regen_hours)
VALUES
    -- Easy Challenges (E)
    ('Inbox March', 'march in place while clearing 10 emails (7 min)', 'E', 60, 4),
    ('Stair‑tune', 'sing your favorite song on the stairs (5 min)', 'E', 70, 4),
    ('Plant Patrol', 'water 3 plants, pacing between each (8 min)', 'E', 50, 4),
    ('Sock Slide', 'slide in socks across a floor, return ×10 (10 reps)', 'E', 80, 4),
    ('Desk Tap', 'tap feet alternately under desk (10 min)', 'E', 40, 4),
    ('Posture Reset', '10× shoulder‑blade squeezes (10 reps)', 'E', 30, 4),
    ('Book Balance', 'hold a book on head & walk back and forth (5 min)', 'E', 55, 4),
    ('Window Watch', 'pace reading campus news board (7 min)', 'E', 45, 4),
    ('Coffee Stroll', 'sip & stroll (5 min)', 'E', 50, 4),
    ('Corridor Karaoke', 'sing & stroll (2 min)', 'E', 100, 4),
    ('Hallway Hop', 'skip 10 steps down a corridor (10 reps)', 'E', 70, 4),
    ('Fruit & Stroll', 'eat an apple then stroll (5 min)', 'E', 25, 4),
    ('Leg Shake', 'shake each leg 1 min while seated (2 min)', 'E', 20, 4),
    ('Arm Circles', '1 min of arm circles waiting for class', 'E', 20, 4),
    ('Snack Fetch', 'walk to vending machine & back (4 min)', 'E', 15, 4),
    ('Gratitude Walk', 'name 3 things you''re grateful for while walking (5 min)', 'E', 60, 4),
    ('Cloud Count', 'walk and count clouds (3 min)', 'E', 30, 4),
    ('Leaf Collect', 'gather 5 unique leaves on campus (8 min)', 'E', 40, 4),
    ('Bench Balance', 'stand on one leg on a bench (30 s each)', 'E', 90, 4),
    ('Corridor Yoga', 'do 3 yoga poses in hallway (5 min)', 'E', 75, 4),
    ('Campus Loop', 'walk a circle around the quad (7 min)', 'E', 55, 4),
    ('Text & Trek', 'walk 2 min while texting safely', 'E', 20, 4),
    ('Shoe Swap', 'walk barefoot on grass (5 min)', 'E', 65, 4),
    ('Water Break', 'drink 2 glasses, pace for 2 min', 'E', 30, 4),
    ('Brain Break', '5 min mindful walk', 'E', 40, 4),
    ('Calf Raises', '15 reps during study break', 'E', 60, 4),
    ('Wrist Rolls', '2 min of wrist rotations', 'E', 20, 4),
    ('Seated Twist', '2 min twisting stretch', 'E', 25, 4),
    ('Quick Jacks', 'jumping jacks for 1 min', 'E', 100, 4),
    ('Wall Sit', '30 s hold', 'E', 110, 4),

    -- Medium Challenges (M)
    ('Café Crawl', 'walk to 3 cafés—15 min', 'M', 140, 6),
    ('Chalk Artist', 'draw & admire sidewalk art—20 min', 'M', 155, 6),
    ('Tree Hug Relay', 'hug 5 trees, walk between them—20 min', 'M', 130, 6),
    ('Yoga in Park', 'follow 25 min video outside', 'M', 210, 6),
    ('Dog Watch Walk', 'count dogs while walking—15 min', 'M', 120, 6),
    ('Campus Map', 'draw map while exploring—30 min', 'M', 175, 6),
    ('Trail Tease', 'nature‑trail wander—20 min', 'M', 200, 6),
    ('Resistance Band Flow', 'band exercises—15 min', 'M', 135, 6),
    ('Garden Care', '15 min gardening—15 min', 'M', 190, 6),
    ('Outdoor Photo Walk', 'explore & shoot—20 min', 'M', 125, 6),
    ('Frisbee Fun', 'toss & walk—20 min', 'M', 135, 6),
    ('Staircase Dance', 'dance on stairs—5 min', 'M', 155, 6),
    ('Bike Bloom', 'bike to see flowers—15 min', 'M', 145, 6),

    -- Hard Challenges (H)
    ('Sunrise Yoga Series', '50 min outdoors', 'H', 330, 8),
    ('Urban Photo Marathon', '10 photo spots—60 min', 'H', 350, 8),
    ('1‑Mile Fun Run', '≈10 min run + warm-up', 'H', 400, 8),
    ('Dance‑Yoga Fusion', 'flow & freestyle—45 min', 'H', 320, 8),
    ('Community Garden Build', '1 h of work & walk', 'H', 340, 8),
    ('Campus Tour', '1 h exploring campus', 'H', 270, 8),
    ('3‑Day Sunrise Walk', '20 min/day—60 min total', 'H', 300, 8),
    ('Stair‑Only Commute', 'use the stairs over the elevator for 2 days', 'H', 280, 8),
    ('Parkour Workshop', '1 h session', 'H', 360, 8),
    ('Bicycle Scavenger', '5 stops in 1 h', 'H', 300, 8);

-- Add a few default achievements
INSERT INTO achievement (name, message, icon_type, criteria, threshold)
VALUES
    ('First Steps', 'You completed your first challenge!', 'basic', 'challenges_completed', 1),
    ('Getting Started', 'You completed 5 challenges!', 'basic', 'challenges_completed', 5),
    ('Active Participant', 'You completed 25 challenges!', 'silver', 'challenges_completed', 25),
    ('Challenge Master', 'You completed 100 challenges!', 'gold', 'challenges_completed', 100),
    ('Point Collector', 'You earned your first 100 points', 'basic', 'points_earned', 100),
    ('Point Hunter', 'You earned 500 points', 'silver', 'points_earned', 500),
    ('Point Master', 'You earned 1000 points', 'gold', 'points_earned', 1000),
    ('Friend Challenge', 'You completed your first challenge with a friend', 'social', 'friend_challenges', 1),
    ('Social Butterfly', 'You completed 5 challenges with friends', 'social', 'friend_challenges', 5),
    ('Streak Starter', 'You logged in 3 days in a row', 'basic', 'login_streak', 3),
    ('Consistent Player', 'You logged in 7 days in a row', 'silver', 'login_streak', 7),
    ('Daily Devotee', 'You logged in 30 days in a row', 'gold', 'login_streak', 30);

-- Set up the initial weekly challenge set for the current week
DO $$
DECLARE
    current_week INTEGER;
    current_year INTEGER;
BEGIN
    -- Get current week number and year
    SELECT EXTRACT(WEEK FROM CURRENT_DATE) INTO current_week;
    SELECT EXTRACT(YEAR FROM CURRENT_DATE) INTO current_year;
    
    -- Insert Easy challenges for current week
    INSERT INTO weekly_challenge_set (week_number, year, difficulty, challenge_id)
    SELECT 
        current_week,
        current_year,
        difficulty,
        id
    FROM challenge 
    WHERE difficulty = 'E'
    ORDER BY RANDOM() 
    LIMIT 9;
    
    -- Insert Medium challenges for current week
    INSERT INTO weekly_challenge_set (week_number, year, difficulty, challenge_id)
    SELECT 
        current_week,
        current_year,
        difficulty,
        id
    FROM challenge 
    WHERE difficulty = 'M'
    ORDER BY RANDOM() 
    LIMIT 6;
    
    -- Insert Hard challenges for current week
    INSERT INTO weekly_challenge_set (week_number, year, difficulty, challenge_id)
    SELECT 
        current_week,
        current_year,
        difficulty,
        id
    FROM challenge 
    WHERE difficulty = 'H'
    ORDER BY RANDOM() 
    LIMIT 3;
    
    -- Set up a challenge of the week
    INSERT INTO challenge_of_the_week (week_number, year, challenge_id)
    SELECT 
        current_week,
        current_year,
        id
    FROM challenge
    WHERE difficulty = 'M'
    ORDER BY RANDOM()
    LIMIT 1;
END $$;
