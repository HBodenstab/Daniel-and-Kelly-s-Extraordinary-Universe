#!/usr/bin/env python3
"""
Railway ML Data Setup Script
Uploads embeddings and FAISS index to Railway persistent storage
"""

import os
import shutil
from pathlib import Path

def setup_railway_ml_data():
    """Set up ML data files for Railway deployment."""
    
    # Check if we're on Railway
    if os.getenv("RAILWAY_ENVIRONMENT"):
        print("🚀 Running on Railway - setting up ML data...")
        
        # Railway volume mount point
        volume_path = Path("/data")
        volume_path.mkdir(exist_ok=True)
        
        # Check if ML files already exist
        embeddings_file = volume_path / "embeddings.npz"
        faiss_file = volume_path / "index.faiss"
        
        if embeddings_file.exists() and faiss_file.exists():
            print("✅ ML data files already exist on Railway")
            return True
        
        print("⚠️  ML data files missing on Railway")
        print("📋 To fix this:")
        print("1. Go to Railway dashboard")
        print("2. Add a Volume to your service")
        print("3. Mount it at /data")
        print("4. Upload the files manually or use Railway CLI")
        
        return False
    else:
        print("🏠 Running locally - ML data should be in data/ directory")
        data_dir = Path("data")
        
        if (data_dir / "embeddings.npz").exists() and (data_dir / "index.faiss").exists():
            print("✅ Local ML data files found")
            return True
        else:
            print("❌ Local ML data files missing")
            return False

if __name__ == "__main__":
    setup_railway_ml_data()
