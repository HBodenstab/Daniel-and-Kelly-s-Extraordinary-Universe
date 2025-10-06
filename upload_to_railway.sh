#!/bin/bash
# Railway Volume Upload Script
# Run this after setting up the volume in Railway dashboard

echo "🚀 Railway Volume Upload Script"
echo "================================"

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    npm install -g @railway/cli
fi

echo "📋 Manual steps required:"
echo "1. Go to Railway dashboard"
echo "2. Add volume to your service:"
echo "   - Name: ml-data"
echo "   - Mount Path: /data"
echo "   - Size: 1GB"
echo "3. Login to Railway CLI:"
echo "   railway login"
echo "4. Connect to your project:"
echo "   railway link"
echo "5. Upload files:"
echo "   railway volume upload /data/embeddings.npz data/embeddings.npz"
echo "   railway volume upload /data/index.faiss data/index.faiss"
echo "   railway volume upload /data/episodes.sqlite data/episodes.sqlite"
echo ""
echo "📁 Files to upload:"
echo "   - data/embeddings.npz (217MB)"
echo "   - data/index.faiss (216MB)"
echo "   - data/episodes.sqlite (22MB)"
echo ""
echo "✅ After upload, redeploy your service to use the volume!"
