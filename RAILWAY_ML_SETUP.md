# Railway ML Data Setup Guide

## 🚨 Problem
Railway deployment is missing ML files (embeddings + FAISS index) because they're too large for GitHub:
- `embeddings.npz`: 217MB
- `index.faiss`: 216MB  
- `episodes.sqlite`: 22MB
- **Total**: 455MB (GitHub limit: 100MB per file)

## 🚀 Solutions (Choose One)

### Option 1: Railway Volume Storage (Recommended)

1. **Add Volume to Railway Service:**
   ```bash
   # In Railway dashboard:
   # 1. Go to your service
   # 2. Click "Volumes" tab
   # 3. Add new volume
   # 4. Mount at `/data`
   ```

2. **Upload Files via Railway CLI:**
   ```bash
   # Install Railway CLI
   npm install -g @railway/cli
   
   # Login to Railway
   railway login
   
   # Upload files to volume
   railway volume upload /data/embeddings.npz
   railway volume upload /data/index.faiss
   railway volume upload /data/episodes.sqlite
   ```

### Option 2: Cloud Storage Download

1. **Upload to Cloud Storage:**
   - Upload `ml_data.tar.gz` (358MB) to AWS S3, Google Cloud, or Dropbox
   - Get a public download URL

2. **Set Environment Variable:**
   ```bash
   # In Railway dashboard, add environment variable:
   ML_DATA_URL=https://your-cloud-storage-url/ml_data.tar.gz
   ```

3. **Update App to Download:**
   ```python
   # The app will automatically download and extract on startup
   ```

### Option 3: Railway File Upload

1. **Use Railway File Upload:**
   ```bash
   # Upload files directly to Railway
   railway files upload data/embeddings.npz
   railway files upload data/index.faiss
   railway files upload data/episodes.sqlite
   ```

### Option 4: Build-Time Generation

1. **Generate ML Data During Build:**
   ```python
   # Add to requirements.txt:
   sentence-transformers
   faiss-cpu
   
   # Add build script that generates embeddings on Railway
   ```

## 🔧 Implementation

### Update App Startup
```python
# In app/api.py startup event:
@app.on_event("startup")
async def startup_event():
    # Try to load existing ML data
    if not load_ml_data():
        # If missing, try to download or generate
        setup_ml_data()
```

### Environment Variables
```bash
# Railway environment variables:
ML_DATA_URL=https://your-storage-url/ml_data.tar.gz
RAILWAY_VOLUME_MOUNT_PATH=/data
```

## 📊 Expected Results

After setup, Railway logs should show:
```
INFO:app.embed:Loaded embeddings from data/embeddings.npz
INFO:app.index:FAISS index loaded with 147678 vectors
INFO:app.api:Search index loaded successfully.
```

Instead of:
```
WARNING:app.index:No FAISS index found
```

## 🎯 Recommended Approach

**Use Railway Volume Storage** - it's the most reliable and doesn't require external services.

1. Add volume to Railway service
2. Upload files via Railway CLI
3. Update app to use volume path
4. Redeploy

This gives you persistent storage that survives deployments and provides full hybrid search functionality.
