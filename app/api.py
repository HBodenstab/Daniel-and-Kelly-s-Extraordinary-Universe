"""FastAPI web application for podcast search."""

import logging
import json
from typing import List, Dict, Any
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
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

# Jinja2 templates
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


@app.get("/search", response_class=HTMLResponse)
async def search_page(request: Request, q: str = "", top_k: int = 10):
    """Serve the search page with optional query parameter using server-side rendering."""
    results: List[Dict[str, Any]] = []
    query = normalize_query(q) if q else ""

    if query:
        try:
            # Use lexical search for fast SSR results
            search_results = lexical_search_episodes(query, top_k)
            for r in search_results:
                results.append({
                    "episode_id": r.episode_id,
                    "title": r.title,
                    "pub_date": r.pub_date,
                    "link": r.link,
                    "score": round(r.score, 4),
                    "snippet": r.snippet,
                    "semantic_score": round(r.semantic_score, 4),
                    "lexical_score": round(r.lexical_score, 4),
                })
        except Exception as e:
            logger.error(f"SSR search failed: {e}")
            results = []

    return templates.TemplateResponse(
        "search.html",
        {
            "request": request,
            "query": query,
            "results": results,
            "total_found": len(results),
        },
    )


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


@app.get("/analytics")
async def analytics():
    """Analytics page."""
    return templates.TemplateResponse("analytics.html", {"request": {}})

@app.get("/api/usage")
async def get_usage():
    """Get usage statistics."""
    try:
        stats = db.get_usage_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get usage stats: {e}")
        return {"total_searches": 0, "unique_users": 0}

@app.get("/api/analytics")
async def get_detailed_analytics():
    """Get detailed analytics data."""
    try:
        analytics = db.get_detailed_analytics()
        return analytics
    except Exception as e:
        logger.error(f"Failed to get detailed analytics: {e}")
        return {
            "total_searches": 0,
            "unique_users": 0,
            "total_episodes": 0,
            "total_chunks": 0,
            "recent_searches": 0,
            "hourly_distribution": [],
            "daily_stats": [],
            "last_updated": "error"
        }


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
                    "pub_date": str(ep.pub_date) if ep.pub_date else None,
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