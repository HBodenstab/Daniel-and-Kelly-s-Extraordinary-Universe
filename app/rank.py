"""Hybrid ranking combining semantic and lexical scoring."""

import logging
from typing import List, Tuple, Dict, Optional
from rapidfuzz import fuzz
import numpy as np

from .models import SearchResult, Chunk
from .config import HYBRID_ALPHA
from .storage import db

logger = logging.getLogger(__name__)


def lexical_score(query: str, text: str) -> float:
    """Calculate lexical similarity score using RapidFuzz."""
    if not query or not text:
        return 0.0
    
    # Use partial ratio for better substring matching
    score = fuzz.partial_ratio(query.lower(), text.lower())
    
    # Normalize to 0-1 range
    return score / 100.0


def hybrid_score(semantic_score: float, lexical_score: float, alpha: float = HYBRID_ALPHA) -> float:
    """Combine semantic and lexical scores."""
    return alpha * semantic_score + (1 - alpha) * lexical_score


def rank_results(
    query: str,
    semantic_results: List[Tuple[int, float]],
    top_k: int = 10
) -> List[SearchResult]:
    """Rank results using hybrid semantic + lexical scoring."""
    
    if not semantic_results:
        return []
    
    # Get chunk metadata for all results
    chunk_metadata = []
    for chunk_idx, semantic_score in semantic_results:
        metadata = _get_chunk_metadata(chunk_idx)
        if metadata:
            chunk_metadata.append((chunk_idx, semantic_score, metadata))
    
    # Calculate lexical scores and combine
    ranked_results = []
    
    for chunk_idx, semantic_score, (episode_id, start, end) in chunk_metadata:
        # Get chunk text
        chunk_text = _get_chunk_text(episode_id, start, end)
        if not chunk_text:
            continue
        
        # Calculate lexical score
        lexical = lexical_score(query, chunk_text)
        
        # Calculate hybrid score
        final_score = hybrid_score(semantic_score, lexical)
        
        # Get episode information
        episode = db.get_episode(episode_id)
        if not episode:
            continue
        
        # Generate snippet
        snippet = _generate_snippet(chunk_text, query)
        
        result = SearchResult(
            episode_id=episode_id,
            title=episode.title,
            pub_date=episode.pub_date,
            link=episode.link,
            score=final_score,
            snippet=snippet,
            semantic_score=semantic_score,
            lexical_score=lexical
        )
        
        ranked_results.append(result)
    
    # Sort by final score (descending)
    ranked_results.sort(key=lambda x: x.score, reverse=True)
    
    # Limit to top_k
    return ranked_results[:top_k]


def _get_chunk_metadata(chunk_idx: int) -> Optional[Tuple[int, int, int]]:
    """Get chunk metadata from database using database abstraction."""
    try:
        # Use the database abstraction to get chunk by index
        from .database import ChunkModel
        from .storage import db
        
        with db.SessionLocal() as session:
            # Get chunk by its index position (assuming chunks are ordered by id)
            chunk = session.query(ChunkModel).order_by(ChunkModel.id).offset(chunk_idx).first()
            if chunk:
                return (chunk.episode_id, chunk.start, chunk.end)
    except Exception as e:
        logger.error(f"Error getting chunk metadata: {e}")
    
    return None


def _get_chunk_text(episode_id: int, start: int, end: int) -> str:
    """Get chunk text from episode transcript."""
    try:
        episode = db.get_episode(episode_id)
        if not episode:
            return ""
        
        # Get the relevant portion of the transcript
        full_text = episode.transcript or episode.description or ""
        
        if start >= len(full_text) or end > len(full_text):
            return full_text
        
        return full_text[start:end]
        
    except Exception as e:
        logger.error(f"Error getting chunk text: {e}")
        return ""


def _generate_snippet(text: str, query: str, snippet_length: int = 200) -> str:
    """Generate a relevant snippet from text based on query."""
    if len(text) <= snippet_length:
        return text
    
    # Find the best position to center the snippet
    query_lower = query.lower()
    text_lower = text.lower()
    
    # Look for query terms
    best_pos = 0
    max_score = 0
    
    for i in range(0, len(text) - snippet_length, 50):
        snippet = text_lower[i:i + snippet_length]
        
        # Simple scoring: count query words found
        score = sum(1 for word in query_lower.split() if word in snippet)
        
        if score > max_score:
            max_score = score
            best_pos = i
    
    # Extract snippet
    start = max(0, best_pos - 20)
    end = min(len(text), start + snippet_length + 20)
    
    snippet = text[start:end]
    
    # Add ellipsis if needed
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."
    
    return snippet


def lexical_search_episodes(query: str, top_k: int = 10) -> List[SearchResult]:
    """Fallback lexical search over episode titles and descriptions."""
    episodes = db.search_episodes_title_desc(query)
    
    results = []
    for episode in episodes:
        # Calculate lexical score for title and description
        title_score = lexical_score(query, episode.title)
        desc_score = lexical_score(query, episode.description)
        
        # Use the higher score
        lexical = max(title_score, desc_score)
        
        # Create snippet from title and description
        snippet = f"{episode.title}. {episode.description[:150]}..."
        
        result = SearchResult(
            episode_id=episode.id or 0,
            title=episode.title,
            pub_date=episode.pub_date,
            link=episode.link,
            score=lexical,
            snippet=snippet,
            semantic_score=0.0,
            lexical_score=lexical
        )
        
        results.append(result)
    
    # Sort by score
    results.sort(key=lambda x: x.score, reverse=True)
    
    return results[:top_k]


def normalize_query(query: str) -> str:
    """Normalize search query for better matching."""
    if not query:
        return ""
    
    # Remove extra whitespace
    query = " ".join(query.split())
    
    # Convert to lowercase for consistency
    query = query.lower()
    
    # Remove common stop words (basic list)
    stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
    words = [word for word in query.split() if word not in stop_words]
    
    return " ".join(words)