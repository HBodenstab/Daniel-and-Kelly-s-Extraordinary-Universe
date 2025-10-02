"""Configuration management for the podcast search system."""

import os
from pathlib import Path
from typing import Optional

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# RSS and scraping
RSS_URL = os.getenv("RSS_URL", "https://omny.fm/shows/daniel-and-kellys-extraordinary-universe/playlists/podcast.rss")
USER_AGENT = "Podcast Search Bot 1.0"
SCRAPE_DELAY = 0.3  # seconds between episode fetches

# Embedding model
MODEL_NAME = os.getenv("MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")

# Chunking parameters
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1200"))  # characters
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))  # characters

# Search parameters
TOP_K = int(os.getenv("TOP_K", "10"))
HYBRID_ALPHA = float(os.getenv("HYBRID_ALPHA", "0.7"))  # semantic weight

# File paths
SQLITE_PATH = DATA_DIR / "episodes.sqlite"
FAISS_PATH = DATA_DIR / "index.faiss"
EMBEDDINGS_PATH = DATA_DIR / "embeddings.npz"

# Database settings
DB_TIMEOUT = 30  # seconds

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")