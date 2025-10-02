#!/bin/bash

# Railway Deployment Script
# This script automates the deployment process to Railway

set -e

echo "🚀 Starting Railway deployment..."

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    npm install -g @railway/cli
fi

# Login to Railway (if not already logged in)
echo "🔐 Logging into Railway..."
railway login

# Initialize Railway project (if not already initialized)
echo "📦 Initializing Railway project..."
if [ ! -f "railway.json" ]; then
    railway init
fi

# Add PostgreSQL database
echo "🗄️ Adding PostgreSQL database..."
railway add postgresql

# Set environment variables
echo "⚙️ Setting environment variables..."
railway variables set PORT=8000
railway variables set LOG_LEVEL=INFO
railway variables set RSS_URL="https://omny.fm/shows/daniel-and-kellys-extraordinary-universe/playlists/podcast.rss"
railway variables set USER_AGENT="Podcast Search Bot 1.0"
railway variables set MODEL_NAME="sentence-transformers/all-MiniLM-L6-v2"
railway variables set CHUNK_SIZE=1200
railway variables set CHUNK_OVERLAP=200
railway variables set TOP_K=10
railway variables set HYBRID_ALPHA=0.7

# Deploy the application
echo "🚀 Deploying to Railway..."
railway up

echo "✅ Deployment complete!"
echo ""
echo "📋 Next steps:"
echo "1. Wait for deployment to complete"
echo "2. Run: railway shell"
echo "3. Run: python -m app.cli update"
echo "4. Your app will be available at the Railway URL"
echo ""
echo "🔍 To view logs: railway logs"
echo "📊 To check status: railway status"
