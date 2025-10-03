#!/usr/bin/env python3
"""
Railway deployment helper script.
This script helps prepare the application for Railway deployment.
"""

import os
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_environment():
    """Check if required environment variables are set."""
    required_vars = []
    optional_vars = [
        "DATABASE_URL",
        "RSS_URL", 
        "MODEL_NAME",
        "CHUNK_SIZE",
        "CHUNK_OVERLAP",
        "TOP_K",
        "HYBRID_ALPHA",
        "LOG_LEVEL"
    ]
    
    logger.info("Checking environment variables...")
    
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            logger.info(f"✓ {var} is set")
        else:
            logger.info(f"⚠ {var} is not set (will use default)")
    
    logger.info("Environment check complete.")

def check_dependencies():
    """Check if all required dependencies are available."""
    logger.info("Checking dependencies...")
    
    try:
        import fastapi
        logger.info(f"✓ FastAPI {fastapi.__version__}")
    except ImportError:
        logger.error("✗ FastAPI not found")
        return False
    
    try:
        import uvicorn
        logger.info(f"✓ Uvicorn {uvicorn.__version__}")
    except ImportError:
        logger.error("✗ Uvicorn not found")
        return False
    
    try:
        import sqlalchemy
        logger.info(f"✓ SQLAlchemy {sqlalchemy.__version__}")
    except ImportError:
        logger.error("✗ SQLAlchemy not found")
        return False
    
    try:
        import sentence_transformers
        logger.info(f"✓ Sentence Transformers {sentence_transformers.__version__}")
    except ImportError:
        logger.error("✗ Sentence Transformers not found")
        return False
    
    logger.info("Dependency check complete.")
    return True

def main():
    """Main deployment preparation function."""
    logger.info("🚀 Preparing for Railway deployment...")
    
    # Check environment
    check_environment()
    
    # Check dependencies
    if not check_dependencies():
        logger.error("❌ Dependency check failed!")
        sys.exit(1)
    
    # Check if we're in the right directory
    if not Path("app/api.py").exists():
        logger.error("❌ app/api.py not found. Are you in the right directory?")
        sys.exit(1)
    
    logger.info("✅ Railway deployment preparation complete!")
    logger.info("")
    logger.info("Next steps:")
    logger.info("1. Make sure your Railway PostgreSQL service is connected")
    logger.info("2. Deploy to Railway")
    logger.info("3. After deployment, use /api/refresh to load podcast data")
    logger.info("")

if __name__ == "__main__":
    main()
