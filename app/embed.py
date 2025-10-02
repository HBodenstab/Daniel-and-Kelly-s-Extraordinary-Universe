"""Embedding functionality using sentence-transformers."""

import numpy as np
import logging
from typing import List, Optional, Tuple
from pathlib import Path
import pickle

from sentence_transformers import SentenceTransformer

from .config import MODEL_NAME, EMBEDDINGS_PATH
from .models import Chunk

logger = logging.getLogger(__name__)

# Global model instance
_model: Optional[SentenceTransformer] = None


def load_model() -> SentenceTransformer:
    """Load the sentence transformer model."""
    global _model
    if _model is None:
        logger.info(f"Loading embedding model: {MODEL_NAME}")
        _model = SentenceTransformer(MODEL_NAME)
        logger.info("Model loaded successfully")
    return _model


def embed_texts(texts: List[str]) -> np.ndarray:
    """Generate embeddings for a list of texts."""
    if not texts:
        return np.array([])
    
    model = load_model()
    
    logger.info(f"Generating embeddings for {len(texts)} texts")
    embeddings = model.encode(texts, show_progress_bar=True)
    
    logger.info(f"Generated embeddings with shape: {embeddings.shape}")
    return embeddings


def embed_chunks(chunks: List[Chunk]) -> np.ndarray:
    """Generate embeddings for chunks."""
    texts = [chunk.text for chunk in chunks]
    return embed_texts(texts)


def save_embeddings(embeddings: np.ndarray, chunk_ids: List[int]) -> None:
    """Save embeddings and chunk IDs to disk."""
    try:
        data = {
            'embeddings': embeddings,
            'chunk_ids': chunk_ids
        }
        
        with open(EMBEDDINGS_PATH, 'wb') as f:
            pickle.dump(data, f)
        
        logger.info(f"Saved embeddings to {EMBEDDINGS_PATH}")
        logger.info(f"Embeddings shape: {embeddings.shape}, Chunk IDs: {len(chunk_ids)}")
        
    except Exception as e:
        logger.error(f"Failed to save embeddings: {e}")
        raise


def load_embeddings() -> Tuple[Optional[np.ndarray], Optional[List[int]]]:
    """Load embeddings and chunk IDs from disk."""
    try:
        if not EMBEDDINGS_PATH.exists():
            logger.info("No embeddings file found")
            return None, None
        
        with open(EMBEDDINGS_PATH, 'rb') as f:
            data = pickle.load(f)
        
        embeddings = data['embeddings']
        chunk_ids = data['chunk_ids']
        
        logger.info(f"Loaded embeddings from {EMBEDDINGS_PATH}")
        logger.info(f"Embeddings shape: {embeddings.shape}, Chunk IDs: {len(chunk_ids)}")
        
        return embeddings, chunk_ids
        
    except Exception as e:
        logger.error(f"Failed to load embeddings: {e}")
        return None, None


def get_embedding_dimension() -> int:
    """Get the dimension of embeddings from the model."""
    model = load_model()
    # Create a dummy embedding to get the dimension
    dummy_embedding = model.encode(["dummy"])
    return dummy_embedding.shape[1]


def embed_query(query: str) -> np.ndarray:
    """Generate embedding for a search query."""
    model = load_model()
    embedding = model.encode([query])
    return embedding[0]  # Return single embedding, not array of one


def validate_embeddings(embeddings: np.ndarray, chunk_ids: List[int]) -> bool:
    """Validate that embeddings and chunk IDs are consistent."""
    if embeddings is None or chunk_ids is None:
        return False
    
    if len(embeddings) != len(chunk_ids):
        logger.error(f"Mismatch: {len(embeddings)} embeddings vs {len(chunk_ids)} chunk IDs")
        return False
    
    if len(embeddings) == 0:
        logger.warning("Empty embeddings")
        return False
    
    # Check for NaN or infinite values
    if np.any(np.isnan(embeddings)) or np.any(np.isinf(embeddings)):
        logger.error("Embeddings contain NaN or infinite values")
        return False
    
    logger.info("Embeddings validation passed")
    return True


def clear_embeddings() -> None:
    """Remove cached embeddings file."""
    try:
        if EMBEDDINGS_PATH.exists():
            EMBEDDINGS_PATH.unlink()
            logger.info("Cleared cached embeddings")
    except Exception as e:
        logger.error(f"Failed to clear embeddings: {e}")