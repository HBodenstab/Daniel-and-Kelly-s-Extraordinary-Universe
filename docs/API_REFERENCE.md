# API Reference

Complete REST API documentation for the Extraordinary Universe Search system.

---

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Base URL](#base-url)
- [Endpoints](#endpoints)
  - [GET /](#get-)
  - [POST /api/search](#post-apisearch)
  - [GET /api/stats](#get-apistats)
  - [GET /health](#get-health)
- [Data Models](#data-models)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Examples](#examples)
- [OpenAPI/Swagger](#openapiswagger)

---

## Overview

The API is built with **FastAPI** and follows REST principles. All endpoints return JSON responses unless otherwise specified.

**Key Features**:
- Automatic OpenAPI (Swagger) documentation
- Request/response validation with Pydantic
- Async support for high concurrency
- Detailed error messages

---

## Authentication

Currently, the API is **open and does not require authentication**. 

For production deployments, consider adding:
- API key authentication
- Rate limiting per client
- OAuth2 integration

---

## Base URL

### Local Development
```
http://localhost:8000
```

### Production (Railway)
```
https://your-app-name.railway.app
```

---

## Endpoints

### GET `/`

Serves the web interface HTML page.

#### Response

**Type**: `text/html`

**Status Codes**:
- `200 OK`: HTML page returned

#### Example

```bash
curl http://localhost:8000/
```

---

### POST `/api/search`

Perform a semantic search across podcast episodes.

#### Request Body

**Content-Type**: `application/json`

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `query` | string | Yes | - | Search query in natural language |
| `top_k` | integer | No | 10 | Number of results to return (1-100) |

**Example**:
```json
{
  "query": "quantum mechanics and consciousness",
  "top_k": 5
}
```

#### Response

**Content-Type**: `application/json`

**Status Code**: `200 OK`

| Field | Type | Description |
|-------|------|-------------|
| `results` | array | List of search results (see SearchResult model) |
| `total_found` | integer | Number of results returned |
| `query` | string | Normalized query string used for search |

**SearchResult Object**:
| Field | Type | Description |
|-------|------|-------------|
| `episode_id` | integer | Database ID of the episode |
| `title` | string | Episode title |
| `pub_date` | string \| null | Publication date (ISO 8601 or custom format) |
| `link` | string | URL to episode page |
| `score` | float | Hybrid relevance score (0.0-1.0) |
| `snippet` | string | Relevant text snippet from transcript |
| `semantic_score` | float | Semantic similarity score (0.0-1.0) |
| `lexical_score` | float | Lexical similarity score (0.0-1.0) |

**Example Response**:
```json
{
  "results": [
    {
      "episode_id": 42,
      "title": "Quantum Mechanics and the Nature of Reality",
      "pub_date": "2024-03-15",
      "link": "https://omny.fm/shows/daniel-and-kellys-extraordinary-universe/quantum-mechanics",
      "score": 0.8734,
      "snippet": "...quantum mechanics describes the behavior of particles at the subatomic level...",
      "semantic_score": 0.8921,
      "lexical_score": 0.8123
    },
    {
      "episode_id": 67,
      "title": "Consciousness: The Hard Problem",
      "pub_date": "2024-05-22",
      "link": "https://omny.fm/shows/daniel-and-kellys-extraordinary-universe/consciousness",
      "score": 0.8456,
      "snippet": "...the relationship between quantum mechanics and consciousness remains controversial...",
      "semantic_score": 0.8234,
      "lexical_score": 0.8912
    }
  ],
  "total_found": 2,
  "query": "quantum mechanics and consciousness"
}
```

#### Status Codes

| Code | Description |
|------|-------------|
| `200 OK` | Search completed successfully |
| `400 Bad Request` | Invalid query (e.g., empty string, invalid top_k) |
| `500 Internal Server Error` | Server error during search |

#### Example Requests

**cURL**:
```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "black holes and time dilation",
    "top_k": 5
  }'
```

**Python (requests)**:
```python
import requests

response = requests.post(
    "http://localhost:8000/api/search",
    json={
        "query": "black holes and time dilation",
        "top_k": 5
    }
)

data = response.json()
for result in data["results"]:
    print(f"{result['title']}: {result['score']:.3f}")
```

**JavaScript (fetch)**:
```javascript
fetch("http://localhost:8000/api/search", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    query: "black holes and time dilation",
    top_k: 5
  })
})
  .then(res => res.json())
  .then(data => {
    data.results.forEach(result => {
      console.log(`${result.title}: ${result.score}`);
    });
  });
```

---

### GET `/api/stats`

Get system statistics including database and index information.

#### Response

**Content-Type**: `application/json`

**Status Code**: `200 OK`

| Field | Type | Description |
|-------|------|-------------|
| `episodes` | integer | Total episodes in database |
| `chunks` | integer | Total text chunks indexed |
| `index_loaded` | boolean | Whether FAISS index is loaded in memory |
| `status` | string | System status (`healthy`, `starting`, `degraded`) |
| `vectors` | integer | (Optional) Number of vectors in FAISS index |
| `dimension` | integer | (Optional) Embedding dimension |
| `chunks_mapped` | integer | (Optional) Chunks mapped in index |
| `message` | string | (Optional) Status message |

**Example Response**:
```json
{
  "episodes": 145,
  "chunks": 2431,
  "index_loaded": true,
  "status": "healthy",
  "vectors": 2431,
  "dimension": 384,
  "chunks_mapped": 2431
}
```

**Example Response (Starting)**:
```json
{
  "episodes": 0,
  "chunks": 0,
  "index_loaded": false,
  "status": "starting",
  "message": "Database initializing"
}
```

#### Status Codes

| Code | Description |
|------|-------------|
| `200 OK` | Statistics returned |

#### Example Request

**cURL**:
```bash
curl http://localhost:8000/api/stats
```

**Python**:
```python
import requests

stats = requests.get("http://localhost:8000/api/stats").json()
print(f"Episodes: {stats['episodes']}")
print(f"Chunks: {stats['chunks']}")
print(f"Index loaded: {stats['index_loaded']}")
```

---

### GET `/health`

Simple health check endpoint for monitoring and load balancers.

#### Response

**Content-Type**: `application/json`

**Status Code**: `200 OK`

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Always `"healthy"` if responding |
| `message` | string | Descriptive message |

**Example Response**:
```json
{
  "status": "healthy",
  "message": "Podcast Search API is running"
}
```

#### Example Request

**cURL**:
```bash
curl http://localhost:8000/health
```

---

## Data Models

### SearchRequest

Request payload for search endpoint.

```python
class SearchRequest(BaseModel):
    query: str
    top_k: int = 10
```

**Validation Rules**:
- `query`: Non-empty string, max 500 characters
- `top_k`: Integer between 1 and 100

---

### SearchResponse

Response payload for search endpoint.

```python
class SearchResponse(BaseModel):
    results: List[SearchResult]
    total_found: int
    query: str
```

---

### SearchResult

Individual search result.

```python
class SearchResult(BaseModel):
    episode_id: int
    title: str
    pub_date: Optional[str]
    link: str
    score: float
    snippet: str
    semantic_score: float
    lexical_score: float
```

**Score Interpretation**:
- **score**: Final hybrid score (weighted combination)
- **semantic_score**: Cosine similarity from embeddings (0.0 = unrelated, 1.0 = identical)
- **lexical_score**: Token-based similarity (0.0 = no common words, 1.0 = exact match)

**Default Weighting**:
```
score = (0.7 × semantic_score) + (0.3 × lexical_score)
```

---

### StatsResponse

Response for stats endpoint.

```python
class StatsResponse(BaseModel):
    episodes: int
    chunks: int
    index_loaded: bool
    status: str
    vectors: Optional[int]
    dimension: Optional[int]
    chunks_mapped: Optional[int]
    message: Optional[str]
```

---

## Error Handling

All errors follow a consistent format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Error Codes

#### 400 Bad Request

**Cause**: Invalid input data

**Examples**:
```json
{"detail": "Query cannot be empty"}
{"detail": "top_k must be between 1 and 100"}
```

**Resolution**: Fix request parameters

---

#### 500 Internal Server Error

**Cause**: Server-side error during processing

**Examples**:
```json
{"detail": "Failed to load search index"}
{"detail": "Database connection error"}
```

**Resolution**: Check server logs, verify system health with `/health` and `/api/stats`

---

### Error Response Example

**Request**:
```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "", "top_k": 10}'
```

**Response** (400):
```json
{
  "detail": "Query cannot be empty"
}
```

---

## Rate Limiting

**Current Implementation**: No rate limiting

**Recommended for Production**:
- 100 requests per minute per IP
- 1000 requests per hour per API key
- Exponential backoff for rate-limited clients

**Implementation Example** (not included by default):
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/search")
@limiter.limit("100/minute")
async def search(request: Request, ...):
    ...
```

---

## Examples

### Complete Search Flow

```python
import requests
from typing import List, Dict

class PodcastSearchClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    def health_check(self) -> bool:
        """Check if API is healthy."""
        try:
            resp = requests.get(f"{self.base_url}/health", timeout=5)
            return resp.status_code == 200
        except:
            return False
    
    def get_stats(self) -> Dict:
        """Get system statistics."""
        resp = requests.get(f"{self.base_url}/api/stats")
        resp.raise_for_status()
        return resp.json()
    
    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        """Perform search and return results."""
        resp = requests.post(
            f"{self.base_url}/api/search",
            json={"query": query, "top_k": top_k}
        )
        resp.raise_for_status()
        data = resp.json()
        return data["results"]

# Usage
client = PodcastSearchClient()

# Check health
if not client.health_check():
    print("API is not healthy")
    exit(1)

# Get stats
stats = client.get_stats()
print(f"Database has {stats['episodes']} episodes")

# Perform search
results = client.search("time travel paradoxes", top_k=5)
for i, result in enumerate(results, 1):
    print(f"{i}. {result['title']}")
    print(f"   Score: {result['score']:.3f}")
    print(f"   Snippet: {result['snippet'][:100]}...")
    print()
```

---

### Batch Search

```python
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

def search_query(query: str) -> Dict:
    """Search a single query."""
    response = requests.post(
        "http://localhost:8000/api/search",
        json={"query": query, "top_k": 3}
    )
    return {
        "query": query,
        "results": response.json()["results"]
    }

# Batch search multiple queries
queries = [
    "quantum mechanics",
    "general relativity",
    "dark matter",
    "string theory",
    "consciousness"
]

with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(search_query, q) for q in queries]
    
    for future in as_completed(futures):
        data = future.result()
        print(f"\nQuery: {data['query']}")
        print(f"Top result: {data['results'][0]['title']}")
```

---

### Filtering Results by Date

```python
from datetime import datetime

def search_with_date_filter(query: str, after_date: str) -> List[Dict]:
    """Search and filter results by date."""
    response = requests.post(
        "http://localhost:8000/api/search",
        json={"query": query, "top_k": 50}  # Get more for filtering
    )
    
    results = response.json()["results"]
    
    # Filter by date (assuming pub_date is in YYYY-MM-DD format)
    filtered = [
        r for r in results 
        if r["pub_date"] and r["pub_date"] >= after_date
    ]
    
    return filtered[:10]  # Return top 10 after filtering

# Get results from 2024 onwards
recent_results = search_with_date_filter("artificial intelligence", "2024-01-01")
```

---

## OpenAPI/Swagger

### Interactive Documentation

FastAPI automatically generates interactive API documentation:

**Swagger UI**: `http://localhost:8000/docs`
- Interactive interface to test endpoints
- Request/response examples
- Schema definitions

**ReDoc**: `http://localhost:8000/redoc`
- Clean, readable documentation
- Better for sharing with non-technical users

### OpenAPI Spec

Download the raw OpenAPI specification:

```bash
curl http://localhost:8000/openapi.json > openapi.json
```

### Code Generation

Use the OpenAPI spec to generate client libraries:

```bash
# Generate Python client
openapi-generator-cli generate \
  -i http://localhost:8000/openapi.json \
  -g python \
  -o ./python-client

# Generate TypeScript client
openapi-generator-cli generate \
  -i http://localhost:8000/openapi.json \
  -g typescript-fetch \
  -o ./typescript-client
```

---

## Performance Tips

### Optimal Query Construction

**Good Queries** (natural language):
- "How does quantum entanglement work?"
- "Explain the twin paradox in special relativity"
- "What is dark energy?"

**Less Effective Queries**:
- Single words: "quantum" (too broad)
- Very long queries: >100 words (dilutes signal)
- Complex boolean: "quantum AND (entanglement OR superposition) NOT decoherence"

**Tip**: Use 5-15 word queries for best results.

---

### Pagination Strategy

The API doesn't support offset-based pagination. For large result sets:

1. Request `top_k=50` (reasonable maximum)
2. Implement client-side pagination
3. Cache results for 5-10 minutes

```python
# Fetch once, paginate client-side
all_results = client.search(query, top_k=50)

def paginate(results, page_size=10):
    for i in range(0, len(results), page_size):
        yield results[i:i+page_size]

for page_num, page in enumerate(paginate(all_results), 1):
    print(f"Page {page_num}")
    for result in page:
        print(f"  - {result['title']}")
```

---

### Caching Recommendations

Implement client-side caching for:
- Frequent queries (e.g., "quantum mechanics")
- Stats endpoint (cache for 5 minutes)
- Health checks (cache for 30 seconds)

```python
from functools import lru_cache
import time

@lru_cache(maxsize=100)
def cached_search(query: str, top_k: int, cache_key: int):
    """Cache search results for 5 minutes."""
    # cache_key changes every 5 minutes, invalidating cache
    return client.search(query, top_k)

# Usage
cache_key = int(time.time() / 300)  # Changes every 5 minutes
results = cached_search("quantum mechanics", 10, cache_key)
```

---

## Monitoring

### Health Checks

Configure your monitoring system to:

```bash
# Check every 30 seconds
curl -f http://localhost:8000/health || alert

# Check index status
curl http://localhost:8000/api/stats | jq '.index_loaded' | grep true || alert
```

### Metrics to Track

| Metric | Endpoint | Threshold |
|--------|----------|-----------|
| Uptime | `/health` | 99.9% |
| Search latency | `/api/search` | p99 < 500ms |
| Index loaded | `/api/stats` | `true` |
| Episode count | `/api/stats` | > 0 |

---

## Changelog

### v1.0.0 (Current)

- Initial API release
- POST `/api/search` endpoint
- GET `/api/stats` endpoint
- GET `/health` endpoint
- OpenAPI/Swagger documentation

### Planned for v1.1.0

- Authentication (API keys)
- Rate limiting
- Query history
- Advanced filters (date range, topics)

---

## Support

For API issues or questions:

- **GitHub Issues**: [Report bugs](https://github.com/your-repo/issues)
- **Discussions**: [Ask questions](https://github.com/your-repo/discussions)
- **Documentation**: [Read the docs](../README.md)

---

*API design follows industry best practices from [BeagleMind.com](https://BeagleMind.com) — specialists in production ML APIs.*


