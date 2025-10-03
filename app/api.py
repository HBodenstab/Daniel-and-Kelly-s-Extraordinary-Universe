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
from .database import EpisodeModel
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
    
    try:
        # Try to load the search index
        if not is_index_loaded():
            logger.info("Loading search index...")
            load_faiss_index()
            logger.info("Search index loaded successfully.")
        else:
            logger.info("Search index already loaded.")
    except Exception as e:
        logger.warning(f"Could not load search index: {e}")
        logger.info("Application will start without search index. Use /api/refresh to load data.")
    
    logger.info("Application startup complete.")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main search interface."""
    # Serve the static HTML file
    html_file = Path(__file__).parent / "ui" / "index.html"
    with open(html_file, 'r') as f:
        content = f.read()
    return HTMLResponse(content=content)


@app.get("/search", response_class=HTMLResponse)
async def search_page(q: str = ""):
    """Serve the search page with optional query parameter."""
    # Serve the static HTML file
    html_file = Path(__file__).parent / "ui" / "search.html"
    try:
        with open(html_file, 'r') as f:
            content = f.read()
        # Replace placeholder with actual query if provided
        if q:
            content = content.replace('{{query}}', q)
        else:
            content = content.replace('{{query}}', '')
        return HTMLResponse(content=content)
    except FileNotFoundError:
        # Fallback to index.html if search.html doesn't exist
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
        
        # Use lexical search for fast results (FAISS index too large for quick loading)
        logger.info("Using lexical search for fast results")
        logger.info(f"Searching for: '{query}' with top_k: {request.top_k}")
        
        try:
            results = lexical_search_episodes(query, request.top_k)
            logger.info(f"Lexical search returned {len(results)} results")
        except Exception as e:
            logger.error(f"Lexical search failed: {e}")
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


@app.get("/episodes")
async def episodes_page(page: int = 1, limit: int = 20):
    """Browse episodes page."""
    try:
        # Calculate offset for pagination
        offset = (page - 1) * limit
        
        # Get episodes from database
        episodes = []
        total_count = db.get_episode_count()
        
        with db.SessionLocal() as session:
            episode_models = session.query(EpisodeModel).order_by(
                EpisodeModel.pub_date.desc()
            ).offset(offset).limit(limit).all()
            
            for ep in episode_models:
                episodes.append({
                    "id": ep.id,
                    "title": ep.title,
                    "link": ep.link,
                    "pub_date": ep.pub_date.isoformat() if ep.pub_date else None,
                    "description": ep.description[:200] + "..." if ep.description and len(ep.description) > 200 else ep.description
                })
        
        # Calculate pagination info
        total_pages = (total_count + limit - 1) // limit
        has_prev = page > 1
        has_next = page < total_pages
        
        # Read and serve the episodes HTML page
        html_file = Path(__file__).parent / "ui" / "episodes.html"
        if not html_file.exists():
            raise HTTPException(status_code=404, detail="Episodes page not found")
        
        with open(html_file, 'r') as f:
            content = f.read()
        
        # Replace placeholder data with actual episodes
        episodes_json = json.dumps(episodes)
        pagination_info = json.dumps({
            "page": page,
            "total_pages": total_pages,
            "total_count": total_count,
            "has_prev": has_prev,
            "has_next": has_next,
            "prev_page": page - 1 if has_prev else None,
            "next_page": page + 1 if has_next else None
        })
        
        content = content.replace('{{EPISODES}}', episodes_json)
        content = content.replace('{{PAGINATION}}', pagination_info)
        
        return HTMLResponse(content=content)
        
    except Exception as e:
        logger.error(f"Error serving episodes page: {e}")
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