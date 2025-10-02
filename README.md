# Podcast Search

A local-first semantic search tool for "Daniel and Kelly's Extraordinary Universe" podcast. Search through episodes using natural language queries like "relativity" or "time dilation" and get instant results with titles, dates, links, and relevant transcript snippets.

## Features

- **Semantic Search**: Uses sentence-transformers for intelligent content matching
- **Hybrid Scoring**: Combines semantic and lexical scoring for better results
- **Local-First**: All processing happens locally - no external API calls
- **CLI Interface**: Command-line tools for updating and searching
- **Web Interface**: Clean, modern web UI for easy searching
- **Transcript Extraction**: Automatically extracts transcripts from episode pages
- **Robust Parsing**: Handles missing transcripts gracefully

## Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Ingest and Index Episodes

```bash
# Fetch all episodes and build search index
python -m app.cli update
```

This will:
- Fetch the RSS feed from Omny
- Download each episode page
- Extract transcripts when available
- Create text chunks with overlap
- Generate embeddings using sentence-transformers
- Build a FAISS vector index

### 3. Search Episodes

#### Command Line
```bash
# Semantic search
python -m app.cli search "relativity theory"

# Lexical-only search
python -m app.cli search "time dilation" --lexical-only

# Limit results
python -m app.cli search "quantum mechanics" --top-k 5
```

#### Web Interface
```bash
# Start the web server
uvicorn app.api:app --reload --port 8000

# Open http://localhost:8000 in your browser
```

## Configuration

Environment variables (all optional):

```bash
# RSS feed URL
export RSS_URL="https://omny.fm/shows/daniel-and-kellys-extraordinary-universe/playlists/podcast.rss"

# Embedding model
export MODEL_NAME="sentence-transformers/all-MiniLM-L6-v2"

# Chunking parameters
export CHUNK_SIZE=1200
export CHUNK_OVERLAP=200

# Search parameters
export TOP_K=10
export HYBRID_ALPHA=0.7  # Weight for semantic vs lexical scoring

# Logging
export LOG_LEVEL=INFO
```

## API Endpoints

### Search
```bash
POST /api/search
{
  "query": "relativity",
  "top_k": 10
}
```

### Statistics
```bash
GET /api/stats
```

### Refresh Data
```bash
POST /api/refresh
```

## Project Structure

```
app/
├── __init__.py          # Package initialization
├── config.py            # Configuration management
├── models.py            # Data models (Episode, Chunk, SearchResult)
├── storage.py           # SQLite database operations
├── fetch.py             # RSS and HTML fetching
├── parse.py             # HTML parsing and transcript extraction
├── chunk.py             # Text chunking with overlap
├── embed.py             # Sentence-transformers embeddings
├── index.py             # FAISS vector search
├── rank.py              # Hybrid semantic + lexical scoring
├── cli.py               # Command-line interface
├── api.py               # FastAPI web application
└── ui/
    └── index.html       # Web interface

data/
├── episodes.sqlite      # Episode metadata and transcripts
├── index.faiss          # FAISS vector index
└── embeddings.npz       # Cached embeddings

tests/
├── test_parse.py        # HTML parsing tests
├── test_chunk.py        # Text chunking tests
├── test_embed_index.py  # Embedding and indexing tests
└── test_rank.py         # Ranking tests
```

## Development

### Running Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_parse.py

# Run with coverage
pytest --cov=app
```

### Code Formatting
```bash
# Format code
black app/ tests/
isort app/ tests/

# Type checking
mypy app/
```

## Troubleshooting

### Common Issues

1. **No episodes found during update**
   - Check RSS_URL is correct
   - Verify network connection
   - Check logs for specific errors

2. **Transcript extraction fails**
   - Some episodes may not have transcripts
   - The system falls back to title + description
   - Check individual episode URLs manually

3. **Search returns no results**
   - Ensure index was built successfully (`python -m app.cli stats`)
   - Try lexical-only search: `--lexical-only`
   - Check if embeddings were generated properly

4. **Memory issues with large datasets**
   - Reduce CHUNK_SIZE in config
   - Process episodes in batches
   - Monitor system resources during update

### Database Reset
```bash
# Clear all data and start fresh
python -m app.cli clear
python -m app.cli update
```

### Manual Database Inspection
```bash
# Check database contents
sqlite3 data/episodes.sqlite "SELECT COUNT(*) FROM episodes;"
sqlite3 data/episodes.sqlite "SELECT title FROM episodes LIMIT 5;"
```

## Performance Notes

- **Initial Setup**: First run may take 10-30 minutes depending on number of episodes
- **Memory Usage**: ~2-4GB RAM during embedding generation
- **Disk Space**: ~100-500MB for database and index files
- **Search Speed**: Sub-second response times for semantic search

## Tech Stack

- **Python 3.11+**
- **FastAPI** - Web framework
- **SQLite** - Local database
- **FAISS** - Vector similarity search
- **sentence-transformers** - Embedding generation
- **BeautifulSoup** - HTML parsing
- **RapidFuzz** - Lexical similarity
- **Click** - CLI framework

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

---

*Built with ❤️ for exploring extraordinary topics in science and beyond.*