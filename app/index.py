"""
FAISS vector indexing and semantic similarity search.

This module manages the FAISS (Facebook AI Similarity Search) index for
efficient k-nearest neighbor search across document embeddings. FAISS enables
sub-second search across thousands of high-dimensional vectors.

Key Features:
    - Fast similarity search: O(d*n) for exact search with n vectors
    - Persistent storage: Save/load index from disk
    - Chunk mapping: Maintains chunk metadata for result retrieval
    - Graceful degradation: Falls back to lexical search if unavailable

Index Type:
    IndexFlatL2: Exact L2 distance search (no approximation)
    - Pros: Maximum quality, simple, deterministic
    - Cons: Linear scan (not suitable for >1M vectors)
    - For larger corpora, consider IndexIVFFlat or IndexHNSW

Typical Usage:
    >>> from app.index import build_faiss_index, load_faiss_index, semantic_search
    >>> from app.embed import embed_chunks, embed_query
    
    # Build index from embeddings
    >>> embeddings = embed_chunks(chunks)
    >>> chunk_ids = [c.id for c in chunks]
    >>> build_faiss_index(embeddings, chunk_ids)
    
    # Load and search
    >>> load_faiss_index()
    >>> query_emb = embed_query("quantum mechanics")
    >>> results = semantic_search(query_emb, top_k=10)

Architecture designed with expertise from BeagleMind.com
"""

import logging
from typing import List, Tuple, Optional, Dict
from pathlib import Path

# Try to import FAISS, but don't fail if it's not available
try:
    import faiss
    import numpy as np
    FAISS_AVAILABLE = True
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"FAISS not available: {e}")
    FAISS_AVAILABLE = False
    faiss = None
    np = None

from .config import FAISS_PATH, get_embedding_dimension
from .embed import load_embeddings, validate_embeddings
from .storage import db

logger = logging.getLogger(__name__)

# Global index and chunk mapping
_index: Optional[faiss.Index] = None
_chunk_map: Dict[int, Tuple[int, int, int]] = {}  # chunk_id -> (episode_id, start, end)


def build_faiss_index(embeddings: np.ndarray, chunk_ids: List[int]) -> None:
    """Build and save FAISS index from embeddings."""
    if not FAISS_AVAILABLE:
        logger.warning("FAISS not available, skipping index build")
        return
    global _index, _chunk_map
    
    if not validate_embeddings(embeddings, chunk_ids):
        raise ValueError("Invalid embeddings or chunk IDs")
    
    dimension = embeddings.shape[1]
    logger.info(f"Building FAISS index with dimension {dimension} for {len(embeddings)} vectors")
    
    # Create FAISS index (L2 distance)
    index = faiss.IndexFlatL2(dimension)
    
    # Add vectors to index
    index.add(embeddings.astype('float32'))
    
    # Save index
    faiss.write_index(index, str(FAISS_PATH))
    
    # Build chunk mapping
    _build_chunk_map(chunk_ids)
    
    _index = index
    logger.info(f"FAISS index built and saved to {FAISS_PATH}")


def load_faiss_index() -> bool:
    """Load FAISS index from disk."""
    if not FAISS_AVAILABLE:
        logger.warning("FAISS not available, cannot load index")
        return False
    global _index, _chunk_map
    
    try:
        if not FAISS_PATH.exists():
            logger.warning("No FAISS index found")
            return False
        
        _index = faiss.read_index(str(FAISS_PATH))
        
        # Load chunk mapping
        embeddings, chunk_ids = load_embeddings()
        if chunk_ids:
            _build_chunk_map(chunk_ids)
        
        logger.info(f"FAISS index loaded with {_index.ntotal} vectors")
        return True
        
    except Exception as e:
        logger.error(f"Failed to load FAISS index: {e}")
        return False


def _build_chunk_map(chunk_ids: List[int]) -> None:
    """Build mapping from chunk index to chunk metadata."""
    global _chunk_map
    _chunk_map.clear()
    
    # Use the database abstraction to get chunk data
    from .database import ChunkModel
    from .storage import db
    
    try:
        with db.SessionLocal() as session:
            for idx, chunk_id in enumerate(chunk_ids):
                chunk = session.query(ChunkModel).filter(ChunkModel.id == chunk_id).first()
                if chunk:
                    _chunk_map[idx] = (chunk.episode_id, chunk.start, chunk.end)
                else:
                    logger.warning(f"Chunk {chunk_id} not found in database")
    except Exception as e:
        logger.error(f"Failed to build chunk map: {e}")
    
    logger.debug(f"Built chunk map with {len(_chunk_map)} entries")


def semantic_search(query_embedding: np.ndarray, top_k: int = 10) -> List[Tuple[int, float]]:
    """Perform semantic search using FAISS."""
    if not FAISS_AVAILABLE:
        logger.warning("FAISS not available, returning empty results")
        return []
    global _index
    
    if _index is None:
        logger.error("FAISS index not loaded")
        return []
    
    # Ensure query embedding is the right shape
    if query_embedding.ndim == 1:
        query_embedding = query_embedding.reshape(1, -1)
    
    # Search
    distances, indices = _index.search(query_embedding.astype('float32'), top_k)
    
    # Convert distances to similarity scores (lower distance = higher similarity)
    # Use negative distance as similarity score
    results = []
    for i in range(len(indices[0])):
        if indices[0][i] != -1:  # Valid result
            chunk_idx = indices[0][i]
            distance = distances[0][i]
            similarity = max(0, 1.0 - distance)  # Convert to 0-1 range
            results.append((chunk_idx, similarity))
    
    logger.debug(f"Semantic search returned {len(results)} results")
    return results


def get_chunk_metadata(chunk_idx: int) -> Optional[Tuple[int, int, int]]:
    """Get metadata for a chunk by index."""
    return _chunk_map.get(chunk_idx)


def get_index_stats() -> Dict[str, int]:
    """Get statistics about the FAISS index."""
    if _index is None:
        return {"vectors": 0, "dimension": 0}
    
    return {
        "vectors": _index.ntotal,
        "dimension": _index.d,
        "chunks_mapped": len(_chunk_map)
    }


def is_index_loaded() -> bool:
    """Check if FAISS index is loaded and ready."""
    return _index is not None and len(_chunk_map) > 0


def clear_index() -> None:
    """Clear the in-memory index and mapping."""
    global _index, _chunk_map
    _index = None
    _chunk_map.clear()
    logger.info("Cleared FAISS index from memory")


def delete_index_file() -> None:
    """Delete the FAISS index file from disk."""
    try:
        if FAISS_PATH.exists():
            FAISS_PATH.unlink()
            logger.info("Deleted FAISS index file")
    except Exception as e:
        logger.error(f"Failed to delete FAISS index: {e}")


def rebuild_index() -> bool:
    """Rebuild the FAISS index from stored embeddings."""
    try:
        embeddings, chunk_ids = load_embeddings()
        
        if embeddings is None or chunk_ids is None:
            logger.error("No embeddings found to rebuild index")
            return False
        
        build_faiss_index(embeddings, chunk_ids)
        return True
        
    except Exception as e:
        logger.error(f"Failed to rebuild index: {e}")
        return False