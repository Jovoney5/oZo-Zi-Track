# Deployment Checklist for Render

## ✅ Pre-Deployment Checklist

### Files Created
- [x] `requirements.txt` - All Python dependencies
- [x] `runtime.txt` - Python version (3.11.0)
- [x] `render.yaml` - Render configuration
- [x] `Procfile` - Alternative deployment config
- [x] `.gitignore` - Git ignore rules
- [x] `README.md` - Documentation

### Code Ready
- [x] App uses `PORT` environment variable
- [x] App binds to `0.0.0.0`
- [x] WebSocket configured for production
- [x] Database auto-initializes on startup

## 📦 Deployment Steps

### 1. Push to GitHub/GitLab

```bash
# If not already initialized
git init

# Add all files
git add .

# Commit
git commit -m "Ready for Render deployment"

# Create GitHub repo and push
git remote add origin https://github.com/yourusername/jdf-tracker.git
git branch -M main
git push -u origin main
```

### 2. Deploy on Render

1. Visit [render.com](https://render.com)
2. Sign up or log in
3. Click **"New +"** → **"Web Service"**
4. Connect your repository
5. Render will auto-detect settings from `render.yaml`
6. Click **"Create Web Service"**
7. Wait for deployment (2-5 minutes)

### 3. Verify Deployment

Visit your Render URL and check:
- [ ] Login page loads
- [ ] Can login with demo credentials
- [ ] Commander dashboard shows map
- [ ] Map displays Jamaica correctly
- [ ] Soldier markers appear on map
- [ ] Real-time updates work
- [ ] Can add new soldier
- [ ] GPS capture works (if on mobile/HTTPS)

## 🔍 Troubleshooting

### Build Fails
- Check Render logs for Python errors
- Verify all dependencies in `requirements.txt`
- Ensure Python version matches `runtime.txt`

### App Doesn't Start
- Check start command: `gunicorn --worker-class eventlet -w 1 app:app`
- Verify PORT environment variable is set
- Check logs for errors

### WebSocket Not Working
- Ensure using `eventlet` worker class
- Check CORS settings in app.py
- Verify client connects to correct URL

### Database Issues
- On free tier, database resets on restart (normal behavior)
- Default users recreated automatically
- For persistent data, upgrade to paid tier

## 🌐 Share Your Demo

Once deployed, share this with your officer:

```
Demo URL: https://your-app.onrender.com

Login Credentials:
- Commander: commander / commander123
- Sergeant: sergeant / sergeant123

Features to Show:
1. Login with commander credentials
2. View real-time map with soldiers
3. Click soldier markers for details
4. Add new soldier (if on mobile, GPS will work)
5. Watch vitals update smoothly
6. Show alert system
```

## ⚠️ Free Tier Limitations

Remember to mention:
- Service spins down after 15 mins inactivity
- First request after sleep takes ~30 seconds
- Database resets on restart
- For production, recommend paid tier

## 🚀 Next Steps

After demo approval:
1. Consider paid Render tier for persistence
2. Add PostgreSQL database
3. Add user registration
4. Implement real GPS device integration
5. Add data export features
