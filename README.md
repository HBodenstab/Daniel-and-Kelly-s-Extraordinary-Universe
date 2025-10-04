# Extraordinary Universe Search

> A semantic search engine for exploring extraordinary ideas in science, philosophy, and beyond.

## Acknowledgments

This system was engineered for exploring content from **Daniel & Kelly's Extraordinary Universe** — a podcast that makes complex ideas in science, philosophy, and beyond accessible to everyone. Special thanks to Daniel and Kelly for creating such remarkable content.

*Architecture and implementation developed with engineering expertise from [BeagleMind.com](https://BeagleMind.com) — specialists in AI-powered search and knowledge systems.*

---

## Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions)

---

*"In the vastness of space and the immensity of time, it is my joy to share a planet and an epoch with you."*  
— Adapted from Carl Sagan, whose spirit of scientific wonder inspires this work

**Extraordinary Universe Search** is a production-grade semantic search system that enables natural language queries across podcast transcripts. Built with modern machine learning techniques, it combines vector similarity search with lexical ranking to deliver highly relevant results.

---

## Overview

This system ingests podcast episodes, processes transcripts, generates embeddings using state-of-the-art sentence transformers, and provides both CLI and web interfaces for semantic search. The architecture follows principles of modularity, testability, and operational excellence.

### Key Features

- **Hybrid Search**: Combines semantic (vector) and lexical (keyword) search for optimal relevance
- **Natural Language Queries**: Search using conversational language, not just keywords
- **High Performance**: Sub-second response times with FAISS vector indexing
- **Production Ready**: Includes monitoring, health checks, and graceful degradation
- **Dual Deployment**: Local development (SQLite) and cloud production (PostgreSQL)
- **Comprehensive Testing**: Unit, integration, and end-to-end test coverage

### Technical Highlights

- **Embeddings**: Sentence-transformers (`all-MiniLM-L6-v2`) for semantic understanding
- **Vector Search**: FAISS for efficient similarity search at scale
- **Ranking**: Hybrid scoring with configurable semantic/lexical weighting
- **Text Processing**: Intelligent chunking with overlap for context preservation
- **API**: FastAPI with async support and OpenAPI documentation
- **Storage**: SQLAlchemy with SQLite (local) and PostgreSQL (production)

---

## Quick Start

### Prerequisites

- Python 3.11 or higher
- pip and virtualenv
- 4GB RAM minimum (8GB recommended for initial indexing)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd Daniel-and-Kelly-s-Extraordinary-Universe

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Initial Setup

```bash
# Build the search index (this will take 10-30 minutes on first run)
python -m app.cli update

# Verify installation
python -m app.cli stats
```

Expected output:
```
Episodes in database: 145
Chunks in database: 2431
Search index vectors: 2431
```

### Usage

#### Web Interface

```bash
# Start the web server
uvicorn app.api:app --reload --port 8000

# Navigate to http://localhost:8000
```

The web interface provides:
- Real-time search with auto-complete
- Result snippets with context highlighting
- Score transparency (semantic vs lexical)
- Direct links to episode pages

#### Command Line Interface

```bash
# Semantic search
python -m app.cli search "quantum mechanics"

# Lexical-only search
python -m app.cli search "time dilation" --lexical-only

# Limit results
python -m app.cli search "relativity" --top-k 5

# View statistics
python -m app.cli stats

# Update index
python -m app.cli update

# Clear all data
python -m app.cli clear
```

---

## Architecture

The system follows a modular pipeline architecture:

```
RSS Feed → Parse → Chunk → Embed → Index → Search → Rank → Results
```

For detailed architecture documentation, see [ARCHITECTURE.md](docs/ARCHITECTURE.md).

### Core Components

| Component | Purpose | Key Technology |
|-----------|---------|----------------|
| `fetch.py` | RSS and HTML ingestion | requests, BeautifulSoup |
| `parse.py` | Transcript extraction | lxml, regex patterns |
| `chunk.py` | Text segmentation | Sliding window with overlap |
| `embed.py` | Semantic embeddings | sentence-transformers |
| `index.py` | Vector search | FAISS (IndexFlatIP) |
| `rank.py` | Result scoring | Hybrid semantic + BM25 |
| `api.py` | Web service | FastAPI, uvicorn |
| `storage.py` | Data persistence | SQLAlchemy, SQLite/PostgreSQL |

---

## Configuration

Configuration is environment-based. Copy `env.example` to `.env` and customize:

```bash
# Database
DATABASE_URL=sqlite:///data/episodes.sqlite  # Local development
# DATABASE_URL=postgresql://user:pass@host/db  # Production

# RSS Feed
RSS_URL=https://omny.fm/shows/daniel-and-kellys-extraordinary-universe/playlists/podcast.rss

# Embedding Model
MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2

# Chunking
CHUNK_SIZE=1200        # Characters per chunk
CHUNK_OVERLAP=200      # Overlap between chunks

# Search
TOP_K=10               # Default results returned
HYBRID_ALPHA=0.7       # Semantic weight (0.0-1.0)

# Server
PORT=8000
LOG_LEVEL=INFO
```

### Configuration Details

- **CHUNK_SIZE**: Larger chunks preserve context but reduce granularity. 1200 is optimal for paragraph-level search.
- **CHUNK_OVERLAP**: Prevents losing context at chunk boundaries. 200 characters provides good continuity.
- **HYBRID_ALPHA**: Controls semantic vs lexical balance. 0.7 favors semantic similarity while preserving keyword matching.

---

## API Reference

The FastAPI application provides a REST API with automatic OpenAPI documentation.

### Endpoints

#### `GET /`
Serves the web interface.

#### `POST /api/search`
Perform a search query.

**Request:**
```json
{
  "query": "quantum entanglement",
  "top_k": 10
}
```

**Response:**
```json
{
  "results": [
    {
      "episode_id": 42,
      "title": "Quantum Physics and Reality",
      "pub_date": "2024-03-15",
      "link": "https://...",
      "score": 0.8734,
      "snippet": "...quantum entanglement describes...",
      "semantic_score": 0.8921,
      "lexical_score": 0.7234
    }
  ],
  "total_found": 10,
  "query": "quantum entanglement"
}
```

#### `GET /api/stats`
Get system statistics.

**Response:**
```json
{
  "episodes": 145,
  "chunks": 2431,
  "index_loaded": true,
  "vectors": 2431,
  "dimension": 384,
  "chunks_mapped": 2431,
  "status": "healthy"
}
```

#### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "message": "Podcast Search API is running"
}
```

For detailed API documentation, visit `/docs` (Swagger UI) or `/redoc` when the server is running.

See [API_REFERENCE.md](docs/API_REFERENCE.md) for complete documentation.

---

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test module
pytest tests/test_parse.py

# Run with verbose output
pytest -v
```

### Code Quality

```bash
# Format code
black app/ tests/

# Sort imports
isort app/ tests/

# Type checking
mypy app/

# Linting
flake8 app/ tests/
```

### Project Structure

```
.
├── app/                      # Main application package
│   ├── api.py               # FastAPI web service
│   ├── chunk.py             # Text chunking logic
│   ├── cli.py               # Command-line interface
│   ├── config.py            # Configuration management
│   ├── database.py          # Database abstraction layer
│   ├── embed.py             # Embedding generation
│   ├── fetch.py             # RSS and HTML fetching
│   ├── index.py             # FAISS vector index
│   ├── models.py            # Data models
│   ├── parse.py             # HTML parsing
│   ├── rank.py              # Hybrid ranking
│   ├── storage.py           # Storage interface
│   └── ui/
│       └── index.html       # Web interface
├── data/                    # Generated data (git-ignored)
│   ├── episodes.sqlite      # Local episode database
│   ├── embeddings.npz       # Cached embeddings
│   └── index.faiss          # Vector index
├── docs/                    # Documentation
│   ├── ARCHITECTURE.md      # System architecture
│   ├── API_REFERENCE.md     # API documentation
│   ├── DEVELOPMENT.md       # Development guide
│   └── TROUBLESHOOTING.md   # Common issues
├── tests/                   # Test suite
├── requirements.txt         # Python dependencies
├── env.example             # Environment template
└── README.md               # This file
```

For detailed development guidelines, see [DEVELOPMENT.md](docs/DEVELOPMENT.md).

---

## Deployment

### Railway (Production)

The system is designed for one-click Railway deployment with PostgreSQL:

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Add PostgreSQL
railway add postgresql

# Deploy
railway up
```

For detailed deployment instructions, see [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md).

### Docker

```bash
# Build image
docker build -t extraordinary-universe-search .

# Run container
docker run -p 8000:8000 \
  -e DATABASE_URL=sqlite:///data/episodes.sqlite \
  extraordinary-universe-search
```

---

## Performance

### Benchmarks

Based on a corpus of ~150 episodes and ~2,500 chunks:

- **Initial Indexing**: 10-30 minutes (one-time)
- **Search Latency**: 50-200ms (p99)
- **Memory Usage**: 2-4GB during indexing, 500MB-1GB at runtime
- **Disk Space**: 300-500MB (database + index)

### Optimization Tips

1. **Increase CHUNK_SIZE** for faster indexing (trades off granularity)
2. **Reduce TOP_K** for faster searches
3. **Use lexical-only search** for exact keyword matching
4. **Enable caching** for repeated queries (not implemented by default)

---

## Troubleshooting

### Common Issues

**Issue**: `No episodes found during update`

**Solution**:
```bash
# Verify RSS URL is accessible
curl -I $RSS_URL

# Check logs for specific errors
python -m app.cli update 2>&1 | tee update.log
```

---

**Issue**: `Search returns no results`

**Solution**:
```bash
# Verify index was built
python -m app.cli stats

# Try lexical search
python -m app.cli search "your query" --lexical-only

# Rebuild index if needed
python -m app.cli clear
python -m app.cli update
```

---

**Issue**: `Memory error during indexing`

**Solution**:
- Reduce `CHUNK_SIZE` in configuration
- Close other applications
- Process episodes in batches (see [DEVELOPMENT.md](docs/DEVELOPMENT.md))

For more issues and solutions, see [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).

---

## Testing

The system includes comprehensive test coverage:

```bash
# Run test suite
pytest

# Expected output:
# tests/test_chunk.py ✓✓✓✓
# tests/test_embed_index.py ✓✓✓
# tests/test_parse.py ✓✓✓✓
# tests/test_rank.py ✓✓✓
# 
# 14 passed in 2.34s
```

Test categories:
- **Unit tests**: Individual component functionality
- **Integration tests**: Component interaction
- **End-to-end tests**: Full pipeline validation

---

## Contributing

We welcome contributions! Please follow these guidelines:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Write** tests for new functionality
4. **Ensure** all tests pass (`pytest`)
5. **Format** code (`black`, `isort`)
6. **Commit** changes (`git commit -m 'Add amazing feature'`)
7. **Push** to branch (`git push origin feature/amazing-feature`)
8. **Open** a Pull Request

See [DEVELOPMENT.md](docs/DEVELOPMENT.md) for detailed contribution guidelines.

---

## Tech Stack

| Category | Technology | Version |
|----------|-----------|---------|
| Language | Python | 3.11+ |
| Web Framework | FastAPI | 0.115+ |
| Web Server | Uvicorn / Gunicorn | 0.30+ / 21+ |
| Database | SQLite / PostgreSQL | - / 14+ |
| ORM | SQLAlchemy | 2.0+ |
| Vector Search | FAISS | 1.8+ |
| Embeddings | sentence-transformers | 2.0+ |
| HTML Parsing | BeautifulSoup4 | 4.12+ |
| Lexical Search | RapidFuzz, BM25 | 3.0+ / 0.2+ |
| CLI | Click | 8.0+ |
| Testing | pytest | - |

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

