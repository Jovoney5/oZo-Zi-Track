# JDF Military Fitness Tracker

A real-time GPS tracking and fitness monitoring system for Jamaica Defence Force personnel. Track soldiers' vital signs, location, and activity levels in real-time with an intuitive commander dashboard.

## Features

- 🔐 **Secure Login System** with role-based access control
- 🗺️ **Live GPS Tracking** on interactive map (covers all of Jamaica)
- 📊 **Real-time Vitals Monitoring** (heart rate, temperature, hydration, etc.)
- ➕ **Add New Soldiers** with GPS location capture
- 📍 **Location-based Tracking** anywhere in Jamaica
- ⚡ **WebSocket Updates** for smooth, real-time data flow
- 🎯 **Commander Dashboard** with tactical overview

## Demo Credentials

- **Commander**: `commander` / `commander123`
- **Sergeant**: `sergeant` / `sergeant123`
- **Corporal**: `corporal` / `corporal123`

## Local Development

### Prerequisites

- Python 3.11+
- pip

### Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd "oZo-Zi Track"
```

2. Create and activate virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python app.py
```

5. Open your browser and navigate to:
```
http://localhost:5000
```

## Deploying to Render (Free Tier)

### Step 1: Prepare Your Repository

1. Initialize git repository (if not already done):
```bash
git init
git add .
git commit -m "Initial commit"
```

2. Create a new repository on GitHub/GitLab

3. Push your code:
```bash
git remote add origin <your-repo-url>
git branch -M main
git push -u origin main
```

### Step 2: Deploy on Render

1. Go to [https://render.com](https://render.com) and sign up/login

2. Click **"New +"** → **"Web Service"**

3. Connect your GitHub/GitLab repository

4. Configure the service:
   - **Name**: `jdf-fitness-tracker` (or your preferred name)
   - **Region**: Choose closest to Jamaica (US East recommended)
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT app:app`

5. Select **Free** plan

6. Click **"Create Web Service"**

7. Wait for deployment (usually 2-5 minutes)

8. Once deployed, Render will provide a URL like: `https://jdf-fitness-tracker.onrender.com`

### Step 3: Access Your Deployed App

1. Visit your Render URL
2. Login with demo credentials
3. Start tracking!

## Important Notes for Render Free Tier

⚠️ **Database Persistence**: The free tier uses ephemeral storage, meaning:
- The SQLite database will reset when the service restarts
- Default users and soldiers will be recreated on each restart
- Any new soldiers added will be lost on restart

💡 **Recommendations**:
- Use this for demos and prototypes
- For production, upgrade to paid tier or use external database (PostgreSQL)
- Service spins down after 15 minutes of inactivity (first request after may be slow)

## Project Structure

```
oZo-Zi Track/
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── runtime.txt            # Python version for deployment
├── render.yaml            # Render deployment configuration
├── .gitignore             # Git ignore rules
├── jdf_tracker.db         # SQLite database (auto-created)
└── templates/
    ├── login.html         # Login page
    ├── index.html         # Main dashboard
    ├── commander.html     # Commander tactical view
    ├── add_soldier.html   # Add new soldier form
    ├── soldier_detail.html # Individual soldier details
    └── analytics.html     # Analytics page
```

## Technology Stack

- **Backend**: Flask, Flask-SocketIO, Flask-Login
- **Database**: SQLite3
- **Real-time**: WebSocket (Socket.IO)
- **Maps**: Leaflet.js with OpenStreetMap
- **Frontend**: HTML5, CSS3, JavaScript
- **Deployment**: Gunicorn + Eventlet

## Features in Detail

### Commander Dashboard
- View all soldiers on interactive Jamaica map
- Real-time position updates
- Click markers to see soldier details
- Color-coded status indicators (green/yellow/red)
- Unit readiness statistics

### Add Soldier
- Capture GPS location using browser geolocation
- Works anywhere (not limited to Jamaica for testing)
- Select rank and unit
- Immediate map integration

### Real-time Tracking
- Smooth data transitions (updates every 2.5 seconds)
- Gradual vitals changes (no jumpy numbers)
- Activity-based movement simulation
- Persistent soldier positions

## Support

For issues or questions, please contact the development team.

## License

© 2024 Jamaica Defence Force - Fitness Tracker Prototype
