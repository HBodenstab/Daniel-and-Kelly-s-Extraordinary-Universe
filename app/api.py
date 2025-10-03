"""FastAPI web application for podcast search."""

import logging
from typing import List, Dict, Any
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn

from .models import SearchRequest, SearchResponse, SearchResult
from .storage import db
from .embed import embed_query
from .index import load_faiss_index, semantic_search, is_index_loaded
from .rank import rank_results, lexical_search_episodes, normalize_query

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Podcast Search API",
    description="Search through Daniel and Kelly's Extraordinary Universe podcast",
    version="1.0.0"
)

# Global flag for refresh operation
_refresh_in_progress = False


class SearchRequestModel(BaseModel):
    query: str
    top_k: int = 10


class SearchResponseModel(BaseModel):
    results: List[Dict[str, Any]]
    total_found: int
    query: str


@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup."""
    logger.info("Starting Podcast Search API...")
    
    # Try to load the search index
    if not is_index_loaded():
        logger.info("Loading search index...")
        load_faiss_index()


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main search interface."""
    # Serve the static HTML file
    html_file = Path(__file__).parent / "ui" / "index.html"
    with open(html_file, 'r') as f:
        content = f.read()
    return HTMLResponse(content=content)


@app.post("/api/search", response_model=SearchResponseModel)
async def search(request: SearchRequestModel):
    """Search through podcast episodes."""
    try:
        query = normalize_query(request.query)
        if not query:
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        logger.info(f"API search request: '{query}'")
        
        results: List[SearchResult]
        
        # Check if semantic search is available
        if is_index_loaded():
            # Perform semantic search
            query_embedding = embed_query(query)
            semantic_results = semantic_search(query_embedding, request.top_k * 2)
            
            # Rank results
            results = rank_results(query, semantic_results, request.top_k)
        else:
            # Fallback to lexical search
            results = lexical_search_episodes(query, request.top_k)
        
        # Convert to API response format
        api_results = []
        for result in results:
            api_results.append({
                "episode_id": result.episode_id,
                "title": result.title,
                "pub_date": result.pub_date,
                "link": result.link,
                "score": round(result.score, 4),
                "snippet": result.snippet,
                "semantic_score": round(result.semantic_score, 4),
                "lexical_score": round(result.lexical_score, 4)
            })
        
        return SearchResponseModel(
            results=api_results,
            total_found=len(api_results),
            query=query
        )
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats")
async def stats():
    """Get database and index statistics."""
    try:
        episode_count = db.get_episode_count()
        chunk_count = db.get_chunk_count()
        
        stats = {
            "episodes": episode_count,
            "chunks": chunk_count,
            "index_loaded": is_index_loaded(),
            "status": "healthy"
        }
        
        if is_index_loaded():
            from .index import get_index_stats
            index_stats = get_index_stats()
            stats.update(index_stats)
        
        return stats
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        # Return basic health status even if database is empty
        return {
            "episodes": 0,
            "chunks": 0,
            "index_loaded": False,
            "status": "starting",
            "message": "Database initializing"
        }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)