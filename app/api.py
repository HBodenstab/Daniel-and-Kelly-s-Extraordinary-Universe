"""FastAPI web application for podcast search."""

import logging
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn

from .models import SearchResult
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

# Jinja2 templates
from pathlib import Path
templates = Jinja2Templates(directory=str((Path(__file__).parent / "ui").resolve()))

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
    
    try:
        # Try to load the search index with optimized chunk mapping
        if not is_index_loaded():
            logger.info("Loading search index...")
            load_faiss_index()
            logger.info("Search index loaded successfully.")
        else:
            logger.info("Search index already loaded.")
    except Exception as e:
        logger.warning(f"Could not load search index: {e}")
        logger.info("Application will start without search index. Use lexical search only.")
    
    logger.info("Application startup complete.")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve the main search interface via Jinja2 (auto-escaped)."""
    return templates.TemplateResponse("index.html", {"request": request})




@app.post("/api/search", response_model=SearchResponseModel)
async def search(request: SearchRequestModel, http_request: Request):
    """Search through podcast episodes."""
    try:
        query = normalize_query(request.query)
        if not query:
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        logger.info(f"API search request: '{query}'")
        
        # Record usage
        user_ip = http_request.client.host
        db.record_usage(ip_address=user_ip, endpoint="/api/search")
        
        results: List[SearchResult]
        
        # Smart search strategy: lexical first, semantic only when needed
        logger.info(f"Smart search for: '{query}' with top_k: {request.top_k}")
        
        try:
            # Start with fast lexical search
            lexical_results = lexical_search_episodes(query, request.top_k)
            logger.info(f"Lexical search returned {len(lexical_results)} results")
            
            # Check if we need semantic search for better results
            should_use_semantic = (
                is_index_loaded() and 
                len(lexical_results) < request.top_k and  # Not enough lexical results
                len(query.split()) >= 2  # Multi-word queries benefit more from semantic
            )
            
            if should_use_semantic:
                logger.info("Using semantic search to improve results")
                try:
                    query_embedding = embed_query(query)
                    semantic_raw = semantic_search(query_embedding, request.top_k)
                    semantic_results = rank_results(query, semantic_raw, request.top_k)
                    
                    # Combine lexical and semantic results, removing duplicates
                    all_results = lexical_results + semantic_results
                    seen_episodes = set()
                    combined_results = []
                    
                    for result in all_results:
                        if result.episode_id not in seen_episodes:
                            combined_results.append(result)
                            seen_episodes.add(result.episode_id)
                    
                    # Take top_k results
                    results = combined_results[:request.top_k]
                    logger.info(f"Combined search returned {len(results)} results")
                except Exception as e:
                    logger.warning(f"Semantic search failed, using lexical only: {e}")
                    results = lexical_results
            else:
                logger.info("Using lexical search only (fast path)")
                results = lexical_results
                
        except Exception as e:
            logger.error(f"Search failed: {e}")
            results = []
        
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




@app.get("/health")
async def health():
    """Simple health check endpoint."""
    return {"status": "healthy", "message": "Podcast Search API is running"}




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