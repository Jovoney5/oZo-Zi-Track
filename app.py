from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash
from flask_socketio import SocketIO, emit
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import random
import time
from datetime import datetime, timedelta
import json
import sqlite3
from functools import wraps
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'military_fitness_secret_2024')
# Use threading mode instead of eventlet for better compatibility
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database setup
def init_db():
    conn = sqlite3.connect('jdf_tracker.db')
    c = conn.cursor()

    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  role TEXT NOT NULL,
                  name TEXT NOT NULL)''')

    # Soldiers table
    c.execute('''CREATE TABLE IF NOT EXISTS soldiers
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  rank TEXT NOT NULL,
                  unit TEXT NOT NULL,
                  lat REAL,
                  lng REAL,
                  active INTEGER DEFAULT 1)''')

    # Check if default users exist
    c.execute('SELECT COUNT(*) FROM users')
    if c.fetchone()[0] == 0:
        # Add default users
        default_users = [
            ('commander', generate_password_hash('commander123'), 'Commander', 'Commander Smith'),
            ('sergeant', generate_password_hash('sergeant123'), 'Sergeant', 'Sergeant Johnson'),
            ('corporal', generate_password_hash('corporal123'), 'Corporal', 'Corporal Brown'),
        ]
        c.executemany('INSERT INTO users (username, password, role, name) VALUES (?, ?, ?, ?)', default_users)

    # Check if default soldiers exist
    c.execute('SELECT COUNT(*) FROM soldiers')
    if c.fetchone()[0] == 0:
        # Add default soldiers
        default_soldiers = [
            ("CPL Johnson", "Corporal", "Alpha Squad", 18.0179, -76.8099),
            ("PTE Williams", "Private", "Alpha Squad", 18.0210, -76.8020),
            ("SGT Brown", "Sergeant", "Bravo Squad", 18.0150, -76.8150),
            ("PTE Davis", "Private", "Bravo Squad", 18.0250, -76.8100),
            ("CPL Martinez", "Corporal", "Charlie Squad", 18.0100, -76.8050),
            ("PTE Anderson", "Private", "Charlie Squad", 18.0300, -76.8200),
            ("LT Thompson", "Lieutenant", "Command", 18.0050, -76.7950),
            ("PTE Wilson", "Private", "Alpha Squad", 18.0280, -76.8050),
        ]
        c.executemany('INSERT INTO soldiers (name, rank, unit, lat, lng) VALUES (?, ?, ?, ?, ?)', default_soldiers)

    conn.commit()
    conn.close()

init_db()

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username, role, name):
        self.id = id
        self.username = username
        self.role = role
        self.name = name

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect('jdf_tracker.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user_data = c.fetchone()
    conn.close()
    if user_data:
        return User(user_data[0], user_data[1], user_data[3], user_data[4])
    return None

# Role-based access decorator
def role_required(roles):
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if current_user.role not in roles:
                flash('You do not have permission to access this page.')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Helper function to get soldiers from database
def get_soldiers_from_db():
    conn = sqlite3.connect('jdf_tracker.db')
    c = conn.cursor()
    c.execute('SELECT id, name, rank, unit, lat, lng FROM soldiers WHERE active = 1')
    soldiers_data = c.fetchall()
    conn.close()
    return [{"id": s[0], "name": s[1], "rank": s[2], "unit": s[3], "lat": s[4], "lng": s[5]} for s in soldiers_data]

# Track current activity state for each soldier and when it was last changed
soldier_states = {}
last_activity_change = {}
# Track GPS positions for realistic movement
soldier_positions = {}
# Store previous vitals for smooth transitions
soldier_vitals = {}

# Initialize soldier states and positions from database
def initialize_soldier_states():
    soldiers = get_soldiers_from_db()
    for soldier in soldiers:
        soldier_id = soldier['id']

        if soldier_id not in soldier_states:
            # Assign initial activities
            activities = ['resting', 'walking', 'running', 'training']
            soldier_states[soldier_id] = random.choice(activities)
            last_activity_change[soldier_id] = datetime.now()

        # Initialize GPS positions from database or set default
        if soldier['lat'] and soldier['lng']:
            soldier_positions[soldier_id] = {'lat': soldier['lat'], 'lng': soldier['lng']}
        else:
            # Default to Kingston if no position
            soldier_positions[soldier_id] = {'lat': 18.0179, 'lng': -76.8099}

initialize_soldier_states()


def update_soldier_activity_if_needed(soldier_id):
    """Update soldier activity every 5 minutes"""
    current_time = datetime.now()
    time_since_change = (current_time - last_activity_change[soldier_id]).total_seconds()

    # Change activity every 5 minutes (300 seconds)
    if time_since_change >= 300:  # 5 minutes
        current_activity = soldier_states[soldier_id]

        # Define logical activity transitions
        activity_transitions = {
            'resting': ['walking', 'resting'],  # From resting, can walk or stay resting
            'walking': ['running', 'training', 'resting'],  # From walking, can run, train, or rest
            'running': ['walking', 'training', 'resting'],  # From running, can walk, train, or rest
            'training': ['resting', 'walking']  # From training, can rest or walk
        }

        # Choose next activity from valid transitions
        possible_next = activity_transitions.get(current_activity, ['walking', 'resting'])
        new_activity = random.choice(possible_next)

        soldier_states[soldier_id] = new_activity
        last_activity_change[soldier_id] = current_time
        print(f"Soldier {soldier_id} changed activity: {current_activity} -> {new_activity}")

    return soldier_states[soldier_id]


def update_soldier_position(soldier_id, activity_level):
    """Update soldier GPS position based on activity level"""
    if soldier_id not in soldier_positions:
        soldier_positions[soldier_id] = {'lat': 18.0179, 'lng': -76.8099}

    current_pos = soldier_positions[soldier_id]

    # Movement speed based on activity (in degrees, roughly 0.0001 degrees = ~11 meters)
    if activity_level == 'resting':
        # Very minimal movement (maybe shifting position)
        lat_change = random.uniform(-0.00002, 0.00002)
        lng_change = random.uniform(-0.00002, 0.00002)
    elif activity_level == 'walking':
        # Walking speed ~5 km/h = ~0.00015 degrees per update
        lat_change = random.uniform(-0.0002, 0.0002)
        lng_change = random.uniform(-0.0002, 0.0002)
    elif activity_level == 'running':
        # Running speed ~10 km/h = ~0.0003 degrees per update
        lat_change = random.uniform(-0.0004, 0.0004)
        lng_change = random.uniform(-0.0004, 0.0004)
    else:  # training
        # Training - more erratic movement
        lat_change = random.uniform(-0.0003, 0.0003)
        lng_change = random.uniform(-0.0003, 0.0003)

    # Update position
    new_lat = current_pos['lat'] + lat_change
    new_lng = current_pos['lng'] + lng_change

    # Keep within bounds (all of Jamaica)
    # Jamaica bounds: lat 17.7-18.6, lng -78.4 to -76.2
    new_lat = max(17.7, min(18.6, new_lat))
    new_lng = max(-78.4, min(-76.2, new_lng))

    soldier_positions[soldier_id] = {'lat': new_lat, 'lng': new_lng}

    # Update database with new position
    conn = sqlite3.connect('jdf_tracker.db')
    c = conn.cursor()
    c.execute('UPDATE soldiers SET lat = ?, lng = ? WHERE id = ?', (new_lat, new_lng, soldier_id))
    conn.commit()
    conn.close()

    return soldier_positions[soldier_id]


def generate_soldier_vitals(soldier_id):
    """Generate realistic vital signs for a soldier with smooth transitions"""
    # Get current activity (updates every 5 minutes)
    activity_level = update_soldier_activity_if_needed(soldier_id)

    # Initialize vitals if this is the first time
    if soldier_id not in soldier_vitals:
        # Set initial base values
        base_hr = random.randint(65, 75)
        soldier_vitals[soldier_id] = {
            'heart_rate': base_hr,
            'steps': 0,
            'calories': 0,
            'body_temp': 36.6,
            'stress_level': 20,
            'hydration': 85,
            'fatigue': 15,
            'blood_oxygen': 98
        }

    # Get previous vitals
    prev = soldier_vitals[soldier_id]

    # Define target ranges based on activity
    if activity_level == 'resting':
        target_hr = random.randint(65, 75)
        step_increment = random.randint(0, 2)
        calorie_increment = random.randint(0, 1)
        target_temp = 36.6
        target_hydration = 85
        target_fatigue = 15
    elif activity_level == 'walking':
        target_hr = random.randint(90, 105)
        step_increment = random.randint(8, 12)
        calorie_increment = random.randint(2, 4)
        target_temp = 36.9
        target_hydration = 75
        target_fatigue = 30
    elif activity_level == 'running':
        target_hr = random.randint(130, 150)
        step_increment = random.randint(20, 30)
        calorie_increment = random.randint(5, 8)
        target_temp = 37.4
        target_hydration = 60
        target_fatigue = 65
    else:  # training
        target_hr = random.randint(140, 165)
        step_increment = random.randint(15, 25)
        calorie_increment = random.randint(6, 10)
        target_temp = 37.6
        target_hydration = 55
        target_fatigue = 70

    # Gradually move towards target values (smooth transitions)
    heart_rate = prev['heart_rate'] + (target_hr - prev['heart_rate']) * 0.15
    heart_rate = int(heart_rate + random.randint(-2, 2))  # Small random variation

    # Accumulate steps and calories
    steps = prev['steps'] + step_increment
    calories = prev['calories'] + calorie_increment

    # Gradually adjust temperature
    temp_change = (target_temp - prev['body_temp']) * 0.1
    body_temp = round(prev['body_temp'] + temp_change + random.uniform(-0.05, 0.05), 1)

    # Gradually adjust hydration
    hydration_change = (target_hydration - prev['hydration']) * 0.1
    hydration = int(prev['hydration'] + hydration_change + random.randint(-1, 1))
    hydration = max(40, min(100, hydration))

    # Gradually adjust fatigue
    fatigue_change = (target_fatigue - prev['fatigue']) * 0.1
    fatigue = int(prev['fatigue'] + fatigue_change + random.randint(-1, 1))
    fatigue = max(0, min(100, fatigue))

    # Calculate stress level based on heart rate and temperature
    stress_level = min(100, int((heart_rate - 60) * 1.0 + (body_temp - 36.5) * 15))

    # Blood oxygen stays relatively stable
    blood_oxygen = prev['blood_oxygen'] + random.randint(-1, 1)
    blood_oxygen = max(95, min(100, blood_oxygen))

    # Update GPS position
    location = update_soldier_position(soldier_id, activity_level)

    # Store current vitals for next update
    soldier_vitals[soldier_id] = {
        'heart_rate': heart_rate,
        'steps': steps,
        'calories': calories,
        'body_temp': body_temp,
        'stress_level': stress_level,
        'hydration': hydration,
        'fatigue': fatigue,
        'blood_oxygen': blood_oxygen
    }

    return {
        'heart_rate': max(60, min(200, heart_rate)),
        'steps': steps,
        'calories': calories,
        'body_temp': body_temp,
        'activity': activity_level,
        'stress_level': stress_level,
        'hydration': hydration,
        'fatigue': fatigue,
        'blood_oxygen': blood_oxygen,
        'location': location
    }


@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = sqlite3.connect('jdf_tracker.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username = ?', (username,))
        user_data = c.fetchone()
        conn.close()

        if user_data and check_password_hash(user_data[2], password):
            user = User(user_data[0], user_data[1], user_data[3], user_data[4])
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'Commander':
        return redirect(url_for('commander'))
    else:
        return render_template('index.html', user=current_user)


@app.route('/commander')
@role_required(['Commander'])
def commander():
    return render_template('commander.html', user=current_user)


@app.route('/add-soldier', methods=['GET', 'POST'])
@role_required(['Commander', 'Sergeant'])
def add_soldier():
    if request.method == 'POST':
        name = request.form.get('name')
        rank = request.form.get('rank')
        unit = request.form.get('unit')
        lat = request.form.get('lat')
        lng = request.form.get('lng')

        conn = sqlite3.connect('jdf_tracker.db')
        c = conn.cursor()
        c.execute('INSERT INTO soldiers (name, rank, unit, lat, lng) VALUES (?, ?, ?, ?, ?)',
                  (name, rank, unit, float(lat) if lat else None, float(lng) if lng else None))
        conn.commit()
        new_id = c.lastrowid
        conn.close()

        # Initialize state for new soldier
        initialize_soldier_states()

        flash(f'Soldier {name} added successfully!')
        return redirect(url_for('commander'))

    return render_template('add_soldier.html', user=current_user)


@app.route('/soldier/<int:soldier_id>')
@login_required
def soldier_detail(soldier_id):
    soldiers = get_soldiers_from_db()
    soldier = next((s for s in soldiers if s['id'] == soldier_id), None)
    if soldier:
        return render_template('soldier_detail.html', soldier=soldier, user=current_user)
    return "Soldier not found", 404


@app.route('/analytics')
@role_required(['Commander', 'Sergeant'])
def analytics():
    return render_template('analytics.html', user=current_user)


@app.route('/api/soldiers')
@login_required
def get_soldiers():
    return jsonify(get_soldiers_from_db())


@app.route('/api/soldier/<int:soldier_id>/vitals')
@login_required
def get_soldier_vitals(soldier_id):
    soldiers = get_soldiers_from_db()
    soldier = next((s for s in soldiers if s['id'] == soldier_id), None)
    if soldier:
        vitals = generate_soldier_vitals(soldier_id)
        return jsonify({**soldier, **vitals})
    return jsonify({"error": "Soldier not found"}), 404


@app.route('/api/unit/summary')
@login_required
def get_unit_summary():
    soldiers = get_soldiers_from_db()
    summary = {
        'total_soldiers': len(soldiers),
        'active': random.randint(6, 8),
        'resting': random.randint(0, 2),
        'alerts': random.randint(0, 2),
        'avg_heart_rate': random.randint(80, 110),
        'avg_stress': random.randint(30, 60),
        'avg_hydration': random.randint(60, 85)
    }
    return jsonify(summary)


# WebSocket events for real-time updates
@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('connection_response', {'data': 'Connected to Military Fitness Tracker'})


@socketio.on('request_vitals')
def handle_vitals_request(data):
    soldier_id = data.get('soldier_id')
    if soldier_id:
        soldiers = get_soldiers_from_db()
        soldier = next((s for s in soldiers if s['id'] == soldier_id), None)
        if soldier:
            vitals = generate_soldier_vitals(soldier_id)
            emit('vitals_update', {**soldier, **vitals})


def background_updates():
    """Send periodic updates to all connected clients"""
    while True:
        socketio.sleep(2.5)  # Update every 2.5 seconds for smoother experience
        soldiers = get_soldiers_from_db()
        for soldier in soldiers:
            vitals = generate_soldier_vitals(soldier['id'])
            socketio.emit('vitals_update', {**soldier, **vitals})


@socketio.on('start_monitoring')
def handle_start_monitoring():
    print('Starting real-time monitoring')
    socketio.start_background_task(background_updates)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'True') == 'True'
    socketio.run(app, debug=debug, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)