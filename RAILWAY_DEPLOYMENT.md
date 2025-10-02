# Railway Deployment Guide

This guide explains how to deploy the Podcast Search application to Railway with PostgreSQL as the database.

## Overview

The application will use:
- **Railway PostgreSQL** as the single database (no SQLite in production)
- **Railway's file system** for FAISS indexes and embeddings
- **Automatic environment configuration** via Railway

## Prerequisites

1. Railway account (sign up at [railway.app](https://railway.app))
2. Railway CLI installed: `npm install -g @railway/cli`
3. Git repository with your code

## Deployment Steps

### 1. Login to Railway

```bash
railway login
```

### 2. Create New Project

```bash
# Initialize Railway project
railway init

# Or create from existing repository
railway link
```

### 3. Add PostgreSQL Database

```bash
# Add PostgreSQL service
railway add postgresql

# This will automatically set DATABASE_URL environment variable
```

### 4. Configure Environment Variables

Set the following environment variables in Railway dashboard or via CLI:

```bash
# Application settings
railway variables set PORT=8000
railway variables set LOG_LEVEL=INFO

# RSS and scraping
railway variables set RSS_URL="https://omny.fm/shows/daniel-and-kellys-extraordinary-universe/playlists/podcast.rss"
railway variables set USER_AGENT="Podcast Search Bot 1.0"

# Embedding model
railway variables set MODEL_NAME="sentence-transformers/all-MiniLM-L6-v2"

# Chunking parameters
railway variables set CHUNK_SIZE=1200
railway variables set CHUNK_OVERLAP=200

# Search parameters
railway variables set TOP_K=10
railway variables set HYBRID_ALPHA=0.7
```

### 5. Deploy Application

```bash
# Deploy to Railway
railway up

# Or push to trigger deployment
git push origin main
```

### 6. Initialize Database and Data

After deployment, you need to populate the database and build the search index:

```bash
# Connect to Railway service
railway shell

# Update episodes and build search index
python -m app.cli update
```

## Database Schema

The application uses SQLAlchemy with the following tables:

### Episodes Table
- `id` (Primary Key)
- `guid` (Unique identifier)
- `title` (Episode title)
- `link` (Episode URL)
- `pub_date` (Publication date)
- `description` (Episode description)
- `transcript` (Full transcript text)

### Chunks Table
- `id` (Primary Key)
- `episode_id` (Foreign Key to episodes)
- `idx` (Chunk index within episode)
- `text` (Chunk text content)
- `start` (Start position in transcript)
- `end` (End position in transcript)

## File Storage

The application stores the following files in Railway's file system:
- `data/index.faiss` - FAISS vector index
- `data/embeddings.npz` - Cached embeddings

## Environment Variables

### Required (Auto-set by Railway)
- `DATABASE_URL` - PostgreSQL connection string
- `PORT` - Application port (default: 8000)

### Optional Configuration
- `RSS_URL` - Podcast RSS feed URL
- `MODEL_NAME` - Sentence transformer model
- `CHUNK_SIZE` - Text chunk size for processing
- `CHUNK_OVERLAP` - Overlap between chunks
- `TOP_K` - Number of search results to return
- `HYBRID_ALPHA` - Semantic vs lexical search weight
- `LOG_LEVEL` - Logging level (INFO, DEBUG, etc.)

## Monitoring and Logs

```bash
# View logs
railway logs

# View specific service logs
railway logs --service your-service-name

# Monitor deployment
railway status
```

## Database Management

```bash
# Connect to PostgreSQL database
railway connect postgresql

# Run database migrations (if needed)
railway shell
python -c "from app.database import db; db.init_db()"
```

## Scaling and Performance

### Database Connection Pooling
The application is configured with:
- Pool size: 10 connections
- Max overflow: 20 connections
- Connection pre-ping: enabled

### Memory Usage
- Initial data processing: ~2-4GB RAM
- Runtime: ~500MB-1GB RAM
- FAISS index: ~100-500MB disk space

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   ```bash
   # Check DATABASE_URL is set
   railway variables
   
   # Verify PostgreSQL service is running
   railway status
   ```

2. **Index Not Loading**
   ```bash
   # Rebuild search index
   railway shell
   python -m app.cli update
   ```

3. **Memory Issues**
   - Reduce `CHUNK_SIZE` environment variable
   - Process episodes in smaller batches
   - Monitor Railway metrics

4. **Search Returns No Results**
   ```bash
   # Check database has data
   railway shell
   python -c "from app.database import db; print(f'Episodes: {db.get_episode_count()}, Chunks: {db.get_chunk_count()}')"
   ```

### Health Checks

The application provides health check endpoints:
- `GET /api/stats` - Database and index statistics
- `GET /` - Main search interface

## Local Development vs Production

### Local Development
- Uses SQLite database (`data/episodes.sqlite`)
- Stores files in local `data/` directory
- Development server with hot reload

### Railway Production
- Uses PostgreSQL database
- Stores files in Railway's file system
- Production server with gunicorn

## Security Considerations

1. **Database Security**
   - Railway PostgreSQL is automatically secured
   - Connection strings are encrypted
   - No direct database access from outside Railway

2. **Application Security**
   - No sensitive data in environment variables
   - All user input is sanitized
   - CORS and security headers configured

## Cost Optimization

1. **Database**
   - Railway PostgreSQL has generous free tier
   - Monitor usage in Railway dashboard

2. **Compute**
   - Application sleeps when not in use
   - Optimize embedding generation for memory usage

## Backup and Recovery

```bash
# Backup database
railway connect postgresql
pg_dump $DATABASE_URL > backup.sql

# Restore database
psql $DATABASE_URL < backup.sql
```

## Support

- Railway Documentation: [docs.railway.app](https://docs.railway.app)
- Railway Discord: [discord.gg/railway](https://discord.gg/railway)
- Application Issues: Check logs with `railway logs`
