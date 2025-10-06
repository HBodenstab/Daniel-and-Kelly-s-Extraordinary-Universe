#!/usr/bin/env python3
"""
Railway Volume Setup Script
Checks and sets up ML data files in Railway volume storage
"""

import os
import shutil
from pathlib import Path

def setup_railway_volume():
    """Set up ML data files in Railway volume storage."""
    
    # Check if we're on Railway
    if not os.getenv("RAILWAY_ENVIRONMENT"):
        print("🏠 Running locally - using local data directory")
        return True
    
    print("🚀 Running on Railway - checking volume storage...")
    
    # Railway volume mount point
    volume_path = Path("/data")
    volume_path.mkdir(exist_ok=True)
    
    # Check if ML files exist in volume
    embeddings_file = volume_path / "embeddings.npz"
    faiss_file = volume_path / "index.faiss"
    sqlite_file = volume_path / "episodes.sqlite"
    
    files_exist = all([
        embeddings_file.exists(),
        faiss_file.exists(),
        sqlite_file.exists()
    ])
    
    if files_exist:
        print("✅ ML data files found in Railway volume")
        print(f"   - Embeddings: {embeddings_file} ({embeddings_file.stat().st_size / 1024 / 1024:.1f}MB)")
        print(f"   - FAISS Index: {faiss_file} ({faiss_file.stat().st_size / 1024 / 1024:.1f}MB)")
        print(f"   - Database: {sqlite_file} ({sqlite_file.stat().st_size / 1024 / 1024:.1f}MB)")
        return True
    else:
        print("❌ ML data files missing in Railway volume")
        print("📋 To fix this:")
        print("1. Go to Railway dashboard")
        print("2. Add volume to your service:")
        print("   - Name: ml-data")
        print("   - Mount Path: /data")
        print("   - Size: 1GB")
        print("3. Upload files using Railway CLI:")
        print("   railway volume upload /data/embeddings.npz data/embeddings.npz")
        print("   railway volume upload /data/index.faiss data/index.faiss")
        print("   railway volume upload /data/episodes.sqlite data/episodes.sqlite")
        print("4. Redeploy your service")
        return False

if __name__ == "__main__":
    setup_railway_volume()
