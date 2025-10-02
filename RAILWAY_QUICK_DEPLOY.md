# Railway Quick Deploy Commands

## 🚀 Complete Deployment Sequence

```bash
# 1. Login to Railway
railway login

# 2. Initialize project
railway init

# 3. Add PostgreSQL database
railway add postgresql

# 4. Set environment variables
railway variables set PORT=8000
railway variables set LOG_LEVEL=INFO
railway variables set RSS_URL='https://omny.fm/shows/daniel-and-kellys-extraordinary-universe/playlists/podcast.rss'
railway variables set USER_AGENT='Podcast Search Bot 1.0'
railway variables set MODEL_NAME='sentence-transformers/all-MiniLM-L6-v2'
railway variables set CHUNK_SIZE=1200
railway variables set CHUNK_OVERLAP=200
railway variables set TOP_K=10
railway variables set HYBRID_ALPHA=0.7

# 5. Deploy application
railway up

# 6. Initialize database (after deployment)
railway shell
python -m app.cli update

# 7. Check status
railway status
railway logs
```

## 🔍 Monitoring Commands

```bash
# View logs
railway logs

# Check service status
railway status

# Connect to service
railway shell

# View environment variables
railway variables
```

## 🛠️ Troubleshooting

```bash
# Restart service
railway redeploy

# View specific service logs
railway logs --service your-service-name

# Connect to database
railway connect postgresql
```

## 📋 What Happens During Deployment

1. **Railway builds** your application using the `railway.json` configuration
2. **PostgreSQL database** is automatically provisioned
3. **Environment variables** are set for the application
4. **Application starts** using the `Procfile` configuration
5. **Health checks** run against `/api/stats` endpoint
6. **Database initialization** happens when you run `python -m app.cli update`

## ✅ Success Indicators

- `railway status` shows "Deployed"
- `railway logs` shows no errors
- `/api/stats` endpoint returns episode and chunk counts
- Search functionality works at your Railway URL
