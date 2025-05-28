# seed_challenges.py

import sys
import os
import json

# Add parent directory to path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import db, Challenge

app = create_app()

# Define challenges list - single source of truth
challenges = [
        # --- EASY (90 × regen_hours=4) ---
        {"title":"Inbox March","description":"march in place while clearing 10 emails (7 min)","difficulty":"E","points":60},
        {"title":"Stair‑tune","description":"sing your favorite song on the stairs (5 min)","difficulty":"E","points":70},
        {"title":"Plant Patrol","description":"water 3 plants, pacing between each (8 min)","difficulty":"E","points":50},
        {"title":"Sock Slide","description":"slide in socks across a floor, return ×10 (10 reps)","difficulty":"E","points":80},
        {"title":"Desk Tap","description":"tap feet alternately under desk (10 min)","difficulty":"E","points":40},
        {"title":"Posture Reset","description":"10× shoulder‑blade squeezes (10 reps)","difficulty":"E","points":30},
        {"title":"Book Balance","description":"hold a book on head & walk back and forth (5 min)","difficulty":"E","points":55},
        {"title":"Window Watch","description":"pace reading campus news board (7 min)","difficulty":"E","points":45},
        {"title":"Coffee Stroll","description":"sip & stroll (5 min)","difficulty":"E","points":50},
        {"title":"Corridor Karaoke","description":"sing & stroll (2 min)","difficulty":"E","points":100},
        {"title":"Hallway Hop","description":"skip 10 steps down a corridor (10 reps)","difficulty":"E","points":70},
        {"title":"Fruit & Stroll","description":"eat an apple then stroll (5 min)","difficulty":"E","points":25},
        {"title":"Leg Shake","description":"shake each leg 1 min while seated (2 min)","difficulty":"E","points":20},
        {"title":"Arm Circles","description":"1 min of arm circles waiting for class","difficulty":"E","points":20},
        {"title":"Snack Fetch","description":"walk to vending machine & back (4 min)","difficulty":"E","points":15},
        {"title":"Gratitude Walk","description":"name 3 things you’re grateful for while walking (5 min)","difficulty":"E","points":60},
        {"title":"Cloud Count","description":"walk and count clouds (3 min)","difficulty":"E","points":30},
        {"title":"Leaf Collect","description":"gather 5 unique leaves on campus (8 min)","difficulty":"E","points":40},
        {"title":"Bench Balance","description":"stand on one leg on a bench (30 s each)","difficulty":"E","points":90},
        {"title":"Corridor Yoga","description":"do 3 yoga poses in hallway (5 min)","difficulty":"E","points":75},
        {"title":"Campus Loop","description":"walk a circle around the quad (7 min)","difficulty":"E","points":55},
        {"title":"Text & Trek","description":"walk 2 min while texting safely","difficulty":"E","points":20},
        {"title":"Shoe Swap","description":"walk barefoot on grass (5 min)","difficulty":"E","points":65},
        {"title":"Water Break","description":"drink 2 glasses, pace for 2 min","difficulty":"E","points":30},
        {"title":"Brain Break","description":"5 min mindful walk","difficulty":"E","points":40},
        {"title":"Calf Raises","description":"15 reps during study break","difficulty":"E","points":60},
        {"title":"Wrist Rolls","description":"2 min of wrist rotations","difficulty":"E","points":20},
        {"title":"Seated Twist","description":"2 min twisting stretch","difficulty":"E","points":25},
        {"title":"Quick Jacks","description":"jumping jacks for 1 min","difficulty":"E","points":100},
        {"title":"Wall Sit","description":"30 s hold","difficulty":"E","points":110},
        {"title":"Shoulder Rolls","description":"30 s forward/back","difficulty":"E","points":20},
        {"title":"Neck Stretches","description":"2 min","difficulty":"E","points":20},
        {"title":"Hip Circles","description":"2 min","difficulty":"E","points":30},
        {"title":"Toe Touches","description":"1 min bending stretch","difficulty":"E","points":20},
        {"title":"Ankle Pumps","description":"2 min","difficulty":"E","points":20},
        {"title":"Seated Leg Lifts","description":"15 reps per leg","difficulty":"E","points":35},
        {"title":"Mini‑Plank","description":"30 s hold","difficulty":"E","points":90},
        {"title":"Side‑Leg Raises","description":"15 reps per side","difficulty":"E","points":80},
        {"title":"Cloud Stretch","description":"reach for clouds—stretch & sway (2 min)","difficulty":"E","points":20},
        {"title":"Reflection Walk","description":"pace while journaling thoughts (3 min)","difficulty":"E","points":25},
        {"title":"Garden Gaze","description":"walk through garden & smell flowers (5 min)","difficulty":"E","points":35},
        {"title":"Chalk Doodle","description":"draw sidewalk doodle, then circle it (5 min)","difficulty":"E","points":55},
        {"title":"Stair Landing Dance","description":"dance at stair landing (2 min)","difficulty":"E","points":80},
        {"title":"Phone‑Free Walk","description":"5 min without phone noticing details","difficulty":"E","points":55},
        {"title":"Poster Pace","description":"walk and read all posters on a wall (5 min)","difficulty":"E","points":35},
        {"title":"Silent Disco","description":"walk dancing 5 min with headphones","difficulty":"E","points":70},
        {"title":"Balance Book","description":"balance a book on head and walk in circle (3 min)","difficulty":"E","points":45},
        {"title":"Shadow Steps","description":"mimic your shadow while walking (4 min)","difficulty":"E","points":50},
        {"title":"Balloon Bounce","description":"keep a balloon in air using head only (2 min)","difficulty":"E","points":65},
        {"title":"Desk Yoga","description":"3 chair yoga poses (5 min)","difficulty":"E","points":50},
        {"title":"Walk & Talk","description":"pace while on a 5‑min call","difficulty":"E","points":60},
        {"title":"Pencil Balance","description":"balance pencil on finger & walk (3 min)","difficulty":"E","points":30},
        {"title":"Shoe Shuffle","description":"shuffle feet in place (3 min)","difficulty":"E","points":20},
        {"title":"Mini‑Lunge","description":"10 lunges per leg","difficulty":"E","points":75},
        {"title":"Notebook Juggle","description":"toss notebook & catch while walking (2 min)","difficulty":"E","points":90},
        {"title":"Chair Dance","description":"stand & dance around chair (3 min)","difficulty":"E","points":80},
        {"title":"Hallway High‑Five","description":"high‑five 5 friends while walking (5 min)","difficulty":"E","points":60},
        {"title":"Bubble Pop Walk","description":"pop imaginary bubbles while strolling (4 min)","difficulty":"E","points":30},
        {"title":"Desk Push‑ups","description":"10 incline push‑ups on desk","difficulty":"E","points":70},
        {"title":"Leg Cross Stretch","description":"cross one leg over knee & lean (2 min)","difficulty":"E","points":30},
        {"title":"Wall Clap","description":"clap hands overhead leaning on wall (2 min)","difficulty":"E","points":20},
        {"title":"Light Jog‑in‑Place","description":"jog for 1 min","difficulty":"E","points":90},
        {"title":"Phone Plank","description":"hold plank while on phone (30 s)","difficulty":"E","points":90},
        {"title":"Book Push","description":"push book across table with nose then walk (3 min)","difficulty":"E","points":45},
        {"title":"Backpack Squats","description":"squat 10× with backpack","difficulty":"E","points":80},
        {"title":"Corridor Leap","description":"leap forward 5×","difficulty":"E","points":50},
        {"title":"Tiptoe Transit","description":"walk on tiptoes for 2 min","difficulty":"E","points":45},
        {"title":"Sideways Shuffle","description":"shuffle sideways down hallway (3 min)","difficulty":"E","points":40},
        {"title":"Plant Stretch","description":"stretch arms overhead then bend (2 min)","difficulty":"E","points":20},
        {"title":"Sit‑to‑Stand","description":"stand up & sit down slowly 10×","difficulty":"E","points":70},
        {"title":"Selfie Walk","description":"take 5 selfies at different spots (5 min)","difficulty":"E","points":55},
        {"title":"Chair Spin","description":"sit & spin 5× then walk (3 min)","difficulty":"E","points":40},
        {"title":"Puddle Jump","description":"jump over small puddles 5×","difficulty":"E","points":20},
        {"title":"Snack Balance","description":"balance snack on head then eat (3 min)","difficulty":"E","points":30},
        {"title":"Mirror Stretch","description":"mirror someone else’s stretch (2 min)","difficulty":"E","points":20},
        {"title":"Ink Walk","description":"walk while doodling on paper (5 min)","difficulty":"E","points":50},
        {"title":"Furry Friends","description":"find and pet an animal(5 min)","difficulty":"E","points":50},

        # --- MEDIUM (60 × regen_hours=6) ---
        {"title":"Café Crawl","description":"walk to 3 cafés—15 min","difficulty":"M","points":140},
        {"title":"Chalk Artist","description":"draw & admire sidewalk art—20 min","difficulty":"M","points":155},
        {"title":"Tree Hug Relay","description":"hug 5 trees, walk between them—20 min","difficulty":"M","points":130},
        {"title":"Yoga in Park","description":"follow 25 min video outside","difficulty":"M","points":210},
        {"title":"Partner Stretch","description":"partner‑assisted stretch—15 min","difficulty":"M","points":160},
        {"title":"Memory Lane Walk","description":"revisit 3 old campus spots—20 min","difficulty":"M","points":150},
        {"title":"Graffiti Tour","description":"photo 5 street‑art spots—20 min","difficulty":"M","points":145},
        {"title":"Sidewalk Picnic","description":"walk to spot, eat, walk back—20 min","difficulty":"M","points":140},
        {"title":"Pet Walk","description":"walk a friend’s pet—15 min","difficulty":"M","points":200},
        {"title":"Trail Tease","description":"nature‑trail wander—20 min","difficulty":"M","points":200},
        {"title":"Resistance Band Flow","description":"band exercises—15 min","difficulty":"M","points":135},
        {"title":"Garden Care","description":"15 min gardening—15 min","difficulty":"M","points":190},
        {"title":"Outdoor Photo Walk","description":"explore & shoot—20 min","difficulty":"M","points":125},
        {"title":"Frisbee Fun","description":"toss & walk—20 min","difficulty":"M","points":135},
        {"title":"Staircase Dance","description":"dance on stairs—5 min","difficulty":"M","points":155},
        {"title":"Mall Walk","description":"indoor mall stroll—15 min","difficulty":"M","points":145},
        {"title":"Park Bench Chat","description":"stroll & chat—15 min","difficulty":"M","points":160},
        {"title":"Campus Cleanup","description":"pick up litter—15 min","difficulty":"M","points":230},
        {"title":"Song & Stroll","description":"new playlist walk—10 min","difficulty":"M","points":165},
        {"title":"Bike Ride","description":"ride bike—15 min","difficulty":"M","points":195},
        {"title":"Dance Class Sampler","description":"online tutorial—15 min","difficulty":"M","points":200},
        {"title":"Stair Climb","description":"climb 10 floors—15 min","difficulty":"M","points":190},
        {"title":"Playground Games","description":"play tag—10 min","difficulty":"M","points":150},
        {"title":"Shadow Boxing","description":"10 min","difficulty":"M","points":170},
        {"title":"Mall Window Shop","description":"browse windows—20 min","difficulty":"M","points":150},
        {"title":"Birdwatch Stroll","description":"spot 5 birds—20 min","difficulty":"M","points":140},
        {"title":"Photo Scavenger","description":"find & photograph 5 items—25 min","difficulty":"M","points":180},
        {"title":"Stair‑step Beats","description":"step to music—15 min","difficulty":"M","points":160},
        {"title":"Coin Balance Walk","description":"balance coin on head and walk—15 min","difficulty":"M","points":130},
        {"title":"Yoga Circle","description":"join group yoga—20 min","difficulty":"M","points":210},
        {"title":"Sketch & Stretch","description":"draw then stretch—20 min","difficulty":"M","points":170},
        {"title":"Tree Sit","description":"sit in tree then climb down—15 min","difficulty":"M","points":140},
        {"title":"Parkour Basics","description":"practice simple moves—15 min","difficulty":"M","points":160},
        {"title":"Poetry Walk","description":"read poem then walk—15 min","difficulty":"M","points":130},
        {"title":"Sun Salutation","description":"15 min yoga sequence","difficulty":"M","points":200},
        {"title":"Chalk Messages","description":"write & walk—20 min","difficulty":"M","points":155},
        {"title":"Reflex Walk","description":"catch tossed ball while walking—15 min","difficulty":"M","points":170},
        {"title":"Bike Errand","description":"bike to run errand—20 min","difficulty":"M","points":195},
        {"title":"Staircase Reading","description":"read & step—15 min","difficulty":"M","points":140},
        {"title":"Flower Sketch","description":"sketch flowers then walk—20 min","difficulty":"M","points":145},
        {"title":"Yoga Duo","description":"partner yoga—20 min","difficulty":"M","points":200},
        {"title":"Hopscotch Chalk","description":"draw & play—15 min","difficulty":"M","points":170},
        {"title":"Blindfold Walk","description":"guided blindfold walk—10 min","difficulty":"M","points":180},
        {"title":"Sound Hunt","description":"identify 5 sounds—20 min","difficulty":"M","points":130},
        {"title":"Stair Plank","description":"plank on stairs 2×1 min—10 min","difficulty":"M","points":160},
        {"title":"Wall‑Sit Read","description":"wall sit while reading—10 min","difficulty":"M","points":150},
        {"title":"Photo Recreation","description":"recreate old campus photo—25 min","difficulty":"M","points":180},
        {"title":"Lab Explore","description":"Find and explore a lab near you—20 min","difficulty":"M","points":190},
        {"title":"Group Walk & Talk","description":"with 2 friends—20 min","difficulty":"M","points":160},

        # --- HARD (30 × regen_hours=8) ---
        {"title":"Sunrise Yoga Series","description":"50 min outdoors","difficulty":"H","points":330},
        {"title":"Urban Photo Marathon","description":"10 photo spots—60 min","difficulty":"H","points":350},
        {"title":"1‑Mile Fun Run","description":"≈10 min run + warm-up","difficulty":"H","points":400},
        {"title":"Dance‑Yoga Fusion","description":"flow & freestyle—45 min","difficulty":"H","points":320},
        {"title":"Community Garden Build","description":"1 h of work & walk","difficulty":"H","points":340},
        {"title":"Campus Tour","description":"1 h exploring campus","difficulty":"H","points":270},
        {"title":"3‑Day Sunrise Walk","description":"20 min/day—60 min total","difficulty":"H","points":300},
        {"title":"Stair‑Only Commute","description":"use the stairs over the elevator for 2 days","difficulty":"H","points":280},
        {"title":"Parkour Workshop","description":"1 h session","difficulty":"H","points":360},
        {"title":"Bicycle Scavenger","description":"5 stops in 1 h","difficulty":"H","points":300},
        {"title":"Dance Workshop","description":"learn routine—1 h","difficulty":"H","points":350},
        {"title":"Triathlon","description":"swim/bike/run—1 h total","difficulty":"H","points":390},
        {"title":"5×5 Plank Series","description":"5 planks×1 min—5 min total","difficulty":"H","points":260},
        {"title":"Garden Marathon","description":"weed & walk—1 h","difficulty":"H","points":330},
        {"title":"Story Walk","description":"walk and take reading breaks—1 h","difficulty":"H","points":340},
        {"title":"Campus Climb","description":"climb tallest stairs 10×","difficulty":"H","points":300},
        {"title":"Photo Story","description":"create photo story—1 h","difficulty":"H","points":350},
        {"title":"Yoga Marathon","description":"5×10 min sessions—50 min","difficulty":"H","points":330},
        {"title":"Community Clean‑up","description":"1 h + stroll","difficulty":"H","points":340},
        {"title":"2‑Day Bike Tour","description":"30 min/day—60 min total","difficulty":"H","points":310},
        {"title":"History Tour","description":"go to or give a historically focused tour 1 h","difficulty":"H","points":360},
        {"title":"Obstacle Course","description":"build & run—1 h","difficulty":"H","points":400},
        {"title":"Chalk Festival","description":"draw & wander  60 min","difficulty":"H","points":350},
        {"title":"Silent Disco Host","description":"DJ & dance—1 h","difficulty":"H","points":380},
    ]

# Functions for managing challenges
def export_challenges_to_json(challenges, filepath):
    """Export challenges list to a JSON file"""
    with open(filepath, 'w') as f:
        json.dump(challenges, f, indent=4)
    print(f"Successfully exported {len(challenges)} challenges to {filepath}")

def import_challenges_from_json(filepath):
    """Import challenges from a JSON file"""
    with open(filepath, 'r') as f:
        challenges = json.load(f)
    print(f"Successfully imported {len(challenges)} challenges from {filepath}")
    return challenges

def import_challenges_from_js(js_file_path):
    """Import challenges from the JavaScript file"""
    try:
        with open(js_file_path, 'r') as f:
            content = f.read()
            
        # Extract challenges array from the JavaScript file
        import re
        pattern = r'const challenges = \[(.*?)\];'  # Match content between brackets
        match = re.search(pattern, content, re.DOTALL)
        
        if not match:
            print("Error: Could not parse challenges from JavaScript file")
            return []
            
        challenges_str = match.group(1).strip()
        
        # Convert JavaScript syntax to Python
        challenges_str = challenges_str.replace('// ---', '# ---')  # Convert comments
        
        # Convert the string to a Python list using eval
        # This is normally dangerous, but we control the file content
        challenges_list = eval(f"[{challenges_str}]")
        print(f"Successfully imported {len(challenges_list)} challenges from {js_file_path}")
        return challenges_list
    except Exception as e:
        print(f"Error importing challenges: {e}")
        return []

def seed_database(challenges=None, js_file_path=None):
    """Seed the database with challenges"""
    if challenges is None and js_file_path is not None:
        challenges = import_challenges_from_js(js_file_path)
    elif challenges is None:
        # Default to the global challenges list if it exists
        challenges = globals().get('challenges', [])
        
    if not challenges:
        print("No challenges to seed. Please provide a valid challenges list or JS file path.")
        return
        
    with app.app_context():
        # Delete existing challenges
        Challenge.query.delete()
        db.session.commit()
        
        # Insert with correct regen_hours
        for c in challenges:
            regen = 4 if c["difficulty"]=="E" else 6 if c["difficulty"]=="M" else 8
            db.session.add(Challenge(
                title=c["title"],
                description=c["description"],
                difficulty=c["difficulty"],
                points=c["points"],
                regen_hours=regen
            ))

        db.session.commit()
        print(f"Successfully seeded {len(challenges)} challenges.")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Manage challenges in the FitBrainLab database')
    parser.add_argument('--export', help='Export challenges to JSON file', action='store_true')
    parser.add_argument('--js-import', help='Import challenges from JS file', action='store_true')
    parser.add_argument('--seed', help='Seed database with challenges', action='store_true')
    parser.add_argument('--file', help='JSON file path', default='../challenges.json')
    parser.add_argument('--js-file', help='JS file path', default='../static/js/challenges.js')
    parser.add_argument('--supabase', help='Use Supabase database connection', action='store_true')
    
    args = parser.parse_args()
    
    # Path to JS file is relative to this script
    js_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), args.js_file)
    
    # Setup for Supabase if requested
    if args.supabase:
        print("Setting up Supabase connection")
        # Load environment variables from .env file
        from dotenv import load_dotenv
        load_dotenv()
        
        # Set environment variable to use Supabase
        os.environ['USE_SUPABASE'] = 'true'
        
        # Import Supabase helper
        try:
            from utils.supabase_helper import get_supabase_connection_string
            # Test connection string formation
            connection_string = get_supabase_connection_string()
            print(f"Using Supabase connection: {connection_string.replace(os.environ.get('SUPABASE_DB_PASSWORD', ''), '[PASSWORD]')}")
        except Exception as e:
            print(f"Error setting up Supabase: {e}")
            print("Make sure your .env file contains all necessary Supabase credentials")
            exit(1)
    
    if args.export and args.js_import:
        print("Cannot use both --export and --js-import at the same time")
    elif args.export:
        # Export the in-memory challenges to JSON
        export_challenges_to_json(challenges, args.file)
    elif args.js_import and args.seed:
        # Import from JS file and seed database
        seed_database(js_file_path=js_file_path)
    elif args.js_import:
        # Just import from JS, don't seed
        import_challenges_from_js(js_file_path)
    elif args.seed:
        # Seed using the in-memory challenges list
        seed_database()
    else:
        # Default: Import from JS file and seed the database
        print(f"Using default behavior: import from {js_file_path} and seed database")
        seed_database(js_file_path=js_file_path)
