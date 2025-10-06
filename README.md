# Daniel & Kelly's Extraordinary Universe Search

A fast, intelligent search engine for the Daniel & Kelly's Extraordinary Universe podcast.

## Features

- **Smart Hybrid Search**: Combines semantic understanding with keyword matching
- **Fast Performance**: Optimized for speed with smart fallbacks
- **Simple Interface**: Clean, focused search experience

## Quick Start

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Start the server:**
```bash
   python3 -m uvicorn app.api:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Open in browser:**
   ```
   http://localhost:8000
   ```

## How It Works

- **Single keywords** → Fast lexical search
- **Conceptual queries** → Smart hybrid search (semantic + lexical)
- **Automatic optimization** → Uses the best search method for each query

## API

- `GET /` - Main search interface
- `POST /api/search` - Search API
- `GET /api/stats` - System statistics
- `GET /health` - Health check

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, FAISS
- **Search**: Sentence-Transformers, RapidFuzz
- **Database**: SQLite
- **Frontend**: HTML/CSS/JavaScript

## Data

The system includes:
- 744 podcast episodes
- 147,678 searchable chunks
- Pre-built semantic embeddings
- FAISS vector index

Ready to search the universe! 🚀

## Latest Update
- Smart hybrid search (semantic + lexical)
- Analytics dashboard restored
- Railway deployment optimized
- Railway volume storage setup complete