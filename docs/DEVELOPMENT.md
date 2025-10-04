# Development Guide

Complete guide for developers contributing to the Extraordinary Universe Search project.

---

## Table of Contents

- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [Code Organization](#code-organization)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Git Workflow](#git-workflow)
- [Pull Request Process](#pull-request-process)
- [Release Process](#release-process)
- [Common Tasks](#common-tasks)
- [Debugging](#debugging)

---

## Getting Started

### Prerequisites

**Required**:
- Python 3.11 or higher
- pip 23.0+
- git 2.30+

**Recommended**:
- virtualenv or venv
- VS Code or PyCharm
- Docker (for deployment testing)

### Initial Setup

```bash
# Clone repository
git clone <repository-url>
cd Daniel-and-Kelly-s-Extraordinary-Universe

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# macOS/Linux:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-cov black isort mypy flake8

# Verify installation
python -m pytest
```

### First Run

```bash
# Build search index (takes 15-30 minutes)
python -m app.cli update

# Verify data
python -m app.cli stats

# Start development server
uvicorn app.api:app --reload --port 8000

# Run tests
pytest
```

---

## Development Environment

### Recommended Tools

**IDE**: VS Code or PyCharm
- Python extension (VS Code)
- Pylance for type checking
- Python Test Explorer

**Terminal**: iTerm2 (macOS), Windows Terminal, or Zsh

**Database**: SQLite Browser for inspecting local database

### VS Code Configuration

`.vscode/settings.json`:
```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.sortImports.args": ["--profile", "black"],
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false
}
```

`.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["app.api:app", "--reload"],
      "jinja": true
    },
    {
      "name": "Python: Current File",
      "type": "python",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal"
    }
  ]
}
```

### Environment Variables

Create `.env` file (copy from `env.example`):

```bash
# Database
DATABASE_URL=sqlite:///data/episodes.sqlite

# RSS Feed
RSS_URL=https://omny.fm/shows/daniel-and-kellys-extraordinary-universe/playlists/podcast.rss

# Model
MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2

# Chunking
CHUNK_SIZE=1200
CHUNK_OVERLAP=200

# Search
TOP_K=10
HYBRID_ALPHA=0.7

# Logging
LOG_LEVEL=DEBUG  # Use DEBUG for development
```

---

## Code Organization

### Module Structure

```
app/
├── __init__.py          # Package init
├── api.py              # FastAPI application
├── chunk.py            # Text chunking
├── cli.py              # Command-line interface
├── config.py           # Configuration
├── database.py         # Database abstraction
├── embed.py            # Embeddings
├── fetch.py            # Data fetching
├── index.py            # FAISS indexing
├── models.py           # Data models
├── parse.py            # HTML parsing
├── rank.py             # Result ranking
├── storage.py          # Storage interface
└── ui/
    └── index.html      # Web UI
```

### Dependency Graph

```
api.py → rank.py → index.py → embed.py
       → storage.py → database.py
       
cli.py → fetch.py → parse.py
       → chunk.py
       → embed.py → index.py
       → storage.py
```

**Key Principles**:
- **No circular dependencies**: Each module has clear upstream dependencies
- **Single responsibility**: Each module handles one aspect of the system
- **Testability**: Modules can be tested independently

---

## Coding Standards

### Python Style Guide

Follow **PEP 8** with these conventions:

**Imports**:
```python
# Standard library
import os
import sys
from typing import List, Optional

# Third-party
import numpy as np
from fastapi import FastAPI

# Local
from .models import Episode, Chunk
from .storage import db
```

**Naming Conventions**:
```python
# Modules: lowercase with underscores
# app/fetch.py, app/embed.py

# Classes: PascalCase
class EpisodeParser:
    pass

# Functions/variables: snake_case
def fetch_episode_data():
    episode_count = 0

# Constants: UPPER_SNAKE_CASE
MAX_RETRIES = 3
DEFAULT_CHUNK_SIZE = 1200

# Private: Leading underscore
def _internal_helper():
    pass
```

**Type Hints**:
```python
# Always use type hints
def chunk_text(text: str, size: int) -> List[str]:
    """Split text into chunks."""
    return [text[i:i+size] for i in range(0, len(text), size)]

# Use Optional for nullable values
def get_episode(episode_id: int) -> Optional[Episode]:
    """Get episode by ID, or None if not found."""
    return db.get_episode(episode_id)

# Use typing module for complex types
from typing import Dict, Tuple, Union

def process_results(data: Dict[str, List[float]]) -> Tuple[int, float]:
    """Process search results."""
    return len(data), sum(data.values())
```

**Docstrings**:
```python
def semantic_search(query_embedding: np.ndarray, top_k: int = 10) -> List[SearchResult]:
    """
    Perform semantic search using vector similarity.
    
    Args:
        query_embedding: Query vector (normalized, shape [384])
        top_k: Number of results to return
        
    Returns:
        List of SearchResult objects, sorted by relevance
        
    Raises:
        ValueError: If index is not loaded
        RuntimeError: If search fails
        
    Example:
        >>> embedding = embed_query("quantum mechanics")
        >>> results = semantic_search(embedding, top_k=5)
        >>> print(results[0].title)
        "Introduction to Quantum Physics"
    """
    if not is_index_loaded():
        raise ValueError("Index not loaded. Call load_faiss_index() first.")
    
    # Implementation...
```

### Code Quality Tools

**Black** (code formatting):
```bash
# Format all Python files
black app/ tests/

# Check without modifying
black --check app/ tests/

# Configuration in pyproject.toml
[tool.black]
line-length = 100
target-version = ['py311']
```

**isort** (import sorting):
```bash
# Sort imports
isort app/ tests/

# Configuration in pyproject.toml
[tool.isort]
profile = "black"
line_length = 100
```

**mypy** (type checking):
```bash
# Type check
mypy app/

# Configuration in pyproject.toml
[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false
```

**flake8** (linting):
```bash
# Lint code
flake8 app/ tests/

# Configuration in .flake8
[flake8]
max-line-length = 100
exclude = .git,__pycache__,.venv
ignore = E203,W503
```

### Pre-commit Checks

Create `.git/hooks/pre-commit`:
```bash
#!/bin/bash

echo "Running pre-commit checks..."

# Format code
black app/ tests/
isort app/ tests/

# Type check
mypy app/
if [ $? -ne 0 ]; then
    echo "Type checking failed"
    exit 1
fi

# Lint
flake8 app/ tests/
if [ $? -ne 0 ]; then
    echo "Linting failed"
    exit 1
fi

# Run tests
pytest
if [ $? -ne 0 ]; then
    echo "Tests failed"
    exit 1
fi

echo "All checks passed!"
```

Make executable:
```bash
chmod +x .git/hooks/pre-commit
```

---

## Testing

### Test Organization

```
tests/
├── test_chunk.py         # Chunking tests
├── test_embed_index.py   # Embedding/indexing tests
├── test_parse.py         # HTML parsing tests
├── test_rank.py          # Ranking tests
├── test_api.py           # (Add) API endpoint tests
└── test_integration.py   # (Add) End-to-end tests
```

### Writing Tests

**Unit Test Example**:
```python
# tests/test_chunk.py
import pytest
from app.chunk import chunk_episode_content

def test_chunk_basic():
    """Test basic chunking functionality."""
    episode_id = 1
    title = "Test Episode"
    description = "A test description."
    transcript = "A" * 2000  # Long text
    
    chunks = chunk_episode_content(
        episode_id, title, description, transcript
    )
    
    assert len(chunks) > 0
    assert all(chunk.episode_id == episode_id for chunk in chunks)
    assert all(len(chunk.text) <= 1200 for chunk in chunks)

def test_chunk_overlap():
    """Test that chunks have proper overlap."""
    chunks = chunk_episode_content(1, "", "", "A" * 3000)
    
    # Check overlap between consecutive chunks
    if len(chunks) > 1:
        chunk1_end = chunks[0].text[-100:]
        chunk2_start = chunks[1].text[:100]
        # Should have some overlap
        assert len(set(chunk1_end) & set(chunk2_start)) > 0
```

**Integration Test Example**:
```python
# tests/test_integration.py
import pytest
from app.fetch import fetch_episode_data
from app.chunk import chunk_episode_content
from app.embed import embed_chunks
from app.index import build_faiss_index, semantic_search

def test_full_pipeline():
    """Test complete ingestion and search pipeline."""
    # Fetch (use sample data for testing)
    episodes = fetch_episode_data()
    assert len(episodes) > 0
    
    # Chunk
    episode = episodes[0]
    chunks = chunk_episode_content(
        1, episode.title, episode.description, episode.transcript
    )
    assert len(chunks) > 0
    
    # Embed
    embeddings = embed_chunks(chunks)
    assert embeddings.shape[0] == len(chunks)
    
    # Index
    chunk_ids = list(range(len(chunks)))
    build_faiss_index(embeddings, chunk_ids)
    
    # Search
    from app.embed import embed_query
    query_emb = embed_query("test query")
    results = semantic_search(query_emb, top_k=5)
    assert len(results) > 0
```

**API Test Example**:
```python
# tests/test_api.py
from fastapi.testclient import TestClient
from app.api import app

client = TestClient(app)

def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_search_endpoint():
    """Test search endpoint."""
    response = client.post(
        "/api/search",
        json={"query": "quantum mechanics", "top_k": 5}
    )
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "total_found" in data
    assert len(data["results"]) <= 5

def test_search_invalid_query():
    """Test search with empty query."""
    response = client.post(
        "/api/search",
        json={"query": "", "top_k": 5}
    )
    assert response.status_code == 400
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific file
pytest tests/test_chunk.py

# Run specific test
pytest tests/test_chunk.py::test_chunk_basic

# Run with coverage
pytest --cov=app --cov-report=html

# Run with verbose output
pytest -v

# Run in parallel (requires pytest-xdist)
pytest -n auto

# Stop on first failure
pytest -x
```

### Coverage Goals

**Minimum Coverage**: 80% overall
- **Critical modules** (embed, index, rank): 90%+
- **Integration modules** (fetch, parse): 70%+
- **UI/CLI**: 60%+

View coverage report:
```bash
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

---

## Git Workflow

### Branch Strategy

**Main Branches**:
- `main`: Production-ready code
- `develop`: Integration branch (optional, for larger teams)

**Feature Branches**:
- `feature/semantic-caching`: New features
- `fix/embedding-dimension-bug`: Bug fixes
- `docs/api-reference`: Documentation
- `refactor/storage-abstraction`: Code improvements

### Commit Messages

Follow **Conventional Commits**:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting (no code change)
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

**Examples**:
```
feat(search): add query caching with Redis

Implement Redis-based caching for search results.
Cache key includes query + top_k.
TTL set to 5 minutes.

Closes #123

---

fix(embed): handle empty chunks gracefully

Previously crashed with IndexError when chunk text was empty.
Now skips empty chunks with a warning.

Fixes #456

---

docs: add architecture diagrams

Added Mermaid diagrams for:
- High-level architecture
- Data flow
- Deployment architecture
```

### Commit Best Practices

1. **Atomic commits**: One logical change per commit
2. **Descriptive messages**: Explain *why*, not just *what*
3. **Reference issues**: Use `Closes #123` or `Fixes #456`
4. **Keep commits small**: Easier to review and revert

---

## Pull Request Process

### Before Creating PR

1. **Update from main**:
   ```bash
   git checkout main
   git pull origin main
   git checkout feature/your-feature
   git rebase main
   ```

2. **Run all checks**:
   ```bash
   black app/ tests/
   isort app/ tests/
   mypy app/
   flake8 app/ tests/
   pytest
   ```

3. **Update documentation**:
   - Update README if user-facing changes
   - Update docstrings
   - Add to CHANGELOG.md

4. **Test manually**:
   ```bash
   # Start clean
   python -m app.cli clear
   python -m app.cli update
   python -m app.cli search "test query"
   ```

### Creating PR

**Title**: Follow commit message format
```
feat(search): add query caching
```

**Description Template**:
```markdown
## Summary
Brief description of changes.

## Motivation
Why is this change needed?

## Changes
- Added X
- Modified Y
- Removed Z

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed

## Documentation
- [ ] README updated (if needed)
- [ ] Docstrings added/updated
- [ ] CHANGELOG.md updated

## Screenshots
(If UI changes)

## Related Issues
Closes #123
Related to #456
```

### Review Process

**Reviewer Checklist**:
- [ ] Code follows style guide
- [ ] Tests are comprehensive
- [ ] Documentation is clear
- [ ] No breaking changes (or documented)
- [ ] Performance impact considered
- [ ] Security implications reviewed

**Response to Feedback**:
- Address all comments
- Mark resolved when fixed
- Ask for clarification if needed
- Request re-review when ready

### Merging

**Merge Strategy**: Squash and merge
- Keep main branch history clean
- Combine related commits
- Preserve PR description in commit message

**Post-Merge**:
```bash
# Delete feature branch
git branch -d feature/your-feature
git push origin --delete feature/your-feature

# Update local main
git checkout main
git pull origin main
```

---

## Release Process

### Versioning

Follow **Semantic Versioning** (SemVer):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

**Examples**:
- `1.0.0` → `1.0.1`: Bug fix
- `1.0.1` → `1.1.0`: New feature
- `1.1.0` → `2.0.0`: Breaking change

### Release Checklist

1. **Update version**:
   ```python
   # app/__init__.py
   __version__ = "1.1.0"
   ```

2. **Update CHANGELOG.md**:
   ```markdown
   ## [1.1.0] - 2024-06-15
   
   ### Added
   - Query caching with Redis
   - Date range filters
   
   ### Fixed
   - Empty chunk handling
   - Memory leak in embedding cache
   ```

3. **Run full test suite**:
   ```bash
   pytest --cov=app
   ```

4. **Tag release**:
   ```bash
   git tag -a v1.1.0 -m "Release version 1.1.0"
   git push origin v1.1.0
   ```

5. **Deploy to production** (see Railway deployment docs)

6. **Create GitHub release**:
   - Use tag `v1.1.0`
   - Copy CHANGELOG section
   - Attach build artifacts (if applicable)

---

## Common Tasks

### Adding a New Endpoint

1. **Define Pydantic models** (`app/models.py`):
   ```python
   @dataclass
   class FilterRequest:
       query: str
       start_date: Optional[str] = None
       end_date: Optional[str] = None
       top_k: int = 10
   ```

2. **Implement endpoint** (`app/api.py`):
   ```python
   @app.post("/api/search/filtered")
   async def search_filtered(request: FilterRequest):
       # Implementation
       return {"results": [...]}
   ```

3. **Add tests** (`tests/test_api.py`):
   ```python
   def test_filtered_search():
       response = client.post("/api/search/filtered", json={...})
       assert response.status_code == 200
   ```

4. **Update documentation** (`docs/API_REFERENCE.md`)

### Adding a New Embedding Model

1. **Update config** (`app/config.py`):
   ```python
   MODEL_NAME = os.getenv("MODEL_NAME", "sentence-transformers/all-mpnet-base-v2")
   ```

2. **Update embedding dimension** (`app/embed.py`):
   ```python
   def get_embedding_dimension() -> int:
       # Auto-detect from model
       return model.get_sentence_embedding_dimension()
   ```

3. **Test with new model**:
   ```bash
   export MODEL_NAME=sentence-transformers/all-mpnet-base-v2
   python -m app.cli clear
   python -m app.cli update
   ```

4. **Benchmark performance** (speed vs quality)

### Optimizing Search Performance

1. **Profile search**:
   ```python
   import cProfile
   cProfile.run('semantic_search(query_emb, 10)')
   ```

2. **Identify bottlenecks**:
   - Embedding generation?
   - FAISS search?
   - Database queries?
   - Ranking computation?

3. **Apply optimizations**:
   - Cache embeddings
   - Use approximate FAISS index
   - Batch database queries
   - Pre-compute lexical features

4. **Benchmark improvements**:
   ```bash
   python -m pytest tests/benchmark_search.py
   ```

---

## Debugging

### Logging

**Enable debug logging**:
```bash
export LOG_LEVEL=DEBUG
python -m app.cli search "query"
```

**Add debug logs**:
```python
import logging
logger = logging.getLogger(__name__)

def semantic_search(query_embedding, top_k):
    logger.debug(f"Searching for {top_k} results")
    logger.debug(f"Query embedding shape: {query_embedding.shape}")
    
    # ...
    
    logger.debug(f"Found {len(results)} results")
    return results
```

### Debugging Search Issues

**No results returned**:
```bash
# Check index status
python -m app.cli stats

# Verify embeddings
python -c "from app.embed import load_embeddings; emb, ids = load_embeddings(); print(emb.shape)"

# Try lexical-only search
python -m app.cli search "query" --lexical-only
```

**Poor result quality**:
```python
# Inspect scores
results = semantic_search(query_emb, 20)
for r in results:
    print(f"{r.score:.3f} | {r.semantic_score:.3f} | {r.lexical_score:.3f} | {r.title}")
```

**Slow search**:
```python
import time

start = time.time()
query_emb = embed_query(query)
print(f"Embedding: {time.time() - start:.3f}s")

start = time.time()
results = semantic_search(query_emb, 10)
print(f"Search: {time.time() - start:.3f}s")
```

### Database Debugging

**Inspect SQLite**:
```bash
sqlite3 data/episodes.sqlite

# Check tables
.tables

# Check episode count
SELECT COUNT(*) FROM episodes;

# Check sample episode
SELECT id, title, LENGTH(transcript) FROM episodes LIMIT 1;

# Check chunks
SELECT COUNT(*) FROM chunks;
SELECT episode_id, COUNT(*) FROM chunks GROUP BY episode_id LIMIT 5;
```

**Inspect PostgreSQL** (production):
```bash
# Connect via Railway CLI
railway run psql

# Or use connection string
psql $DATABASE_URL
```

---

## Best Practices

### Performance

- **Use batch operations**: Process chunks in batches, not one-by-one
- **Cache aggressively**: Embeddings, query results, stats
- **Profile before optimizing**: Measure, don't guess
- **Use async where possible**: FastAPI async endpoints

### Security

- **Validate all inputs**: Use Pydantic models
- **Sanitize SQL queries**: Use parameterized queries (SQLAlchemy ORM handles this)
- **Rate limit**: Implement rate limiting in production
- **Environment variables**: Never commit secrets

### Maintainability

- **Write tests first**: TDD when possible
- **Keep functions small**: <50 lines ideal
- **Avoid global state**: Pass dependencies explicitly
- **Document why, not what**: Code shows what, comments explain why

---

## Resources

- **Python Style Guide**: [PEP 8](https://pep8.org/)
- **FastAPI Docs**: [fastapi.tiangolo.com](https://fastapi.tiangolo.com/)
- **FAISS Guide**: [github.com/facebookresearch/faiss/wiki](https://github.com/facebookresearch/faiss/wiki)
- **Sentence-Transformers**: [sbert.net](https://www.sbert.net/)

---

*Development practices refined with expertise from [BeagleMind.com](https://BeagleMind.com) — building maintainable AI systems.*


