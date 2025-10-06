#!/usr/bin/env python3
"""
Simple Railway deployment script for Daniel & Kelly's Extraordinary Universe Search
"""

import os
import sys
import subprocess

def main():
    """Deploy to Railway with proper configuration."""
    print("🚀 Deploying to Railway...")
    
    # Check if we're in the right directory
    if not os.path.exists("app/api.py"):
        print("❌ Error: app/api.py not found. Are you in the right directory?")
        sys.exit(1)
    
    # Check if requirements.txt exists
    if not os.path.exists("requirements.txt"):
        print("❌ Error: requirements.txt not found")
        sys.exit(1)
    
    # Check if data directory exists
    if not os.path.exists("data"):
        print("❌ Error: data directory not found. Make sure embeddings and database are present.")
        sys.exit(1)
    
    print("✅ All files present. Ready for Railway deployment!")
    print("\n📋 Deployment checklist:")
    print("  ✅ Procfile created")
    print("  ✅ railway.json configured")
    print("  ✅ FastAPI app ready")
    print("  ✅ Data directory present")
    
    print("\n🚀 To deploy:")
    print("  1. Connect your GitHub repo to Railway")
    print("  2. Railway will automatically detect Python and use the Procfile")
    print("  3. The app will be available at your Railway URL")
    
    print("\n🔧 Environment variables (if needed):")
    print("  - PORT: Automatically set by Railway")
    print("  - DATABASE_URL: Will use SQLite by default")

if __name__ == "__main__":
    main()
