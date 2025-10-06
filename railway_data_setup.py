#!/usr/bin/env python3
"""
Railway Data Setup Script
Downloads and sets up data files for Railway deployment
"""

import os
import urllib.request
import zipfile
from pathlib import Path

def setup_railway_data():
    """Set up data files for Railway deployment."""
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Check if we're on Railway
    if os.getenv("RAILWAY_ENVIRONMENT"):
        print("🚀 Running on Railway - setting up data files...")
        
        # For now, create placeholder files
        # In production, you would download from a cloud storage service
        print("⚠️  Data files need to be uploaded to Railway")
        print("📦 Consider using Railway's persistent storage or external storage")
        
        # Create empty placeholder files to prevent errors
        (data_dir / "embeddings.npz").touch()
        (data_dir / "episodes.sqlite").touch() 
        (data_dir / "index.faiss").touch()
        
        print("✅ Placeholder data files created")
        print("🔧 Full data files need to be uploaded separately")
    else:
        print("🏠 Running locally - data files should be present")
        if (data_dir / "embeddings.npz").exists():
            print("✅ Local data files found")
        else:
            print("❌ Local data files missing")

if __name__ == "__main__":
    setup_railway_data()
