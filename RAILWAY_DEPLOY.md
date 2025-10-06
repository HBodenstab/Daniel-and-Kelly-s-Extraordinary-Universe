# Railway Deployment Guide

## Quick Deploy to Railway

### 1. Connect Repository
1. Go to [Railway](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository: `Daniel-and-Kelly-s-Extraordinary-Universe`

### 2. Automatic Detection
Railway will automatically:
- ✅ Detect Python project
- ✅ Use `Procfile` for start command
- ✅ Install dependencies from `requirements.txt`
- ✅ Set up environment variables

### 3. Deploy
- Railway will build and deploy automatically
- Your app will be available at: `https://your-app-name.railway.app`

## Configuration

### Procfile
```
web: uvicorn app.api:app --host 0.0.0.0 --port $PORT
```

### railway.json
- Health check: `/health`
- Start command: Auto-detected from Procfile
- Restart policy: On failure

## Environment Variables
- `PORT`: Automatically set by Railway
- `DATABASE_URL`: Uses SQLite by default (included in data/)

## Data Files
The deployment includes:
- ✅ `data/embeddings.npz` - Pre-built semantic embeddings
- ✅ `data/episodes.sqlite` - Episode database
- ✅ `data/index.faiss` - FAISS vector index

## Health Check
Visit `/health` to verify deployment:
```json
{
  "status": "healthy",
  "message": "Podcast Search API is running"
}
```

## Troubleshooting

### If deployment fails:
1. Check Railway logs for errors
2. Ensure all data files are committed
3. Verify Python version compatibility

### Common issues:
- **Missing data files**: Make sure `data/` directory is in repository
- **Port binding**: Railway sets `$PORT` automatically
- **Dependencies**: All requirements in `requirements.txt`

## Success! 🚀
Your search engine will be live at your Railway URL with:
- Smart hybrid search
- 744 episodes indexed
- 147,678 searchable chunks
- Fast semantic + lexical search
