#!/usr/bin/env python3
"""
Download ML data from cloud storage for Railway deployment
"""

import os
import urllib.request
import zipfile
from pathlib import Path

def download_ml_data():
    """Download ML data files from cloud storage."""
    
    # Check if we're on Railway
    if os.getenv("RAILWAY_ENVIRONMENT"):
        print("🚀 Running on Railway - downloading ML data...")
        
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        # Option 1: Download from a cloud storage service
        # Replace with your actual cloud storage URLs
        ml_data_url = os.getenv("ML_DATA_URL", "")
        
        if ml_data_url:
            try:
                print(f"📥 Downloading ML data from {ml_data_url}")
                urllib.request.urlretrieve(ml_data_url, "ml_data.zip")
                
                with zipfile.ZipFile("ml_data.zip", 'r') as zip_ref:
                    zip_ref.extractall(data_dir)
                
                print("✅ ML data downloaded successfully")
                return True
            except Exception as e:
                print(f"❌ Failed to download ML data: {e}")
                return False
        else:
            print("⚠️  ML_DATA_URL environment variable not set")
            print("📋 To fix this:")
            print("1. Upload your data files to a cloud storage service")
            print("2. Set ML_DATA_URL environment variable in Railway")
            print("3. Redeploy the application")
            return False
    else:
        print("🏠 Running locally - using local ML data")
        return True

if __name__ == "__main__":
    download_ml_data()
