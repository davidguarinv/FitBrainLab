from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from . import db
from .models import User

# Create blueprint
bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/about')
def about():
    return render_template('about.html')

@bp.route('/research')
def research():
    return render_template('research.html')

@bp.route('/publications')
def publications():
    return render_template('publications.html')

@bp.route('/communities')
def communities():
    return render_template('communities.html')

@bp.route('/game')
def game():
    # Get sample challenges and top users for the leaderboard
    sample_challenges = [
        {
            'title': 'Morning Run',
            'description': 'Start your day with a 20-minute jog',
            'difficulty': 'E',
            'points': 100
        },
        {
            'title': 'HIIT Session',
            'description': '30-minute high-intensity interval training',
            'difficulty': 'M',
            'points': 200
        },
        {
            'title': 'Marathon Training',
            'description': '2-hour endurance run',
            'difficulty': 'H',
            'points': 300
        }
    ]

    with current_app.app_context():
        top_users = User.query.filter_by(is_public=True).order_by(User.id.desc()).limit(10).all()
    return render_template('game.html', sample_challenges=sample_challenges, top_users=top_users)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        with current_app.app_context():
            user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.game'))
        else:
            flash('Invalid email or password')
            return redirect(url_for('main.game'))
            
    return redirect(url_for('main.game'))

@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Email and password are required')
            return redirect(url_for('main.game'))
            
        with current_app.app_context():
            if User.query.filter_by(email=email).first():
                flash('Email already registered')
                return redirect(url_for('main.game'))
                
            user = User(
                username=User.generate_username(),
                email=email,
                is_public=True
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            login_user(user)
            return redirect(url_for('main.game'))
            
    return redirect(url_for('main.game'))

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('main.game'))
