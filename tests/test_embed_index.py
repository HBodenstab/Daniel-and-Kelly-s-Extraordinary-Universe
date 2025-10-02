"""Tests for embedding and indexing functionality."""

import pytest
import numpy as np
from app.embed import embed_texts, get_embedding_dimension
from app.index import build_faiss_index, semantic_search, load_faiss_index


def test_embed_texts():
    """Test embedding generation for texts."""
    texts = [
        "This is a test sentence about science.",
        "Another sentence about quantum mechanics.",
        "A third sentence about relativity."
    ]
    
    embeddings = embed_texts(texts)
    
    assert embeddings.shape[0] == len(texts)
    assert embeddings.shape[1] > 0  # Should have some dimension
    
    # Check that embeddings are normalized (roughly)
    for i in range(len(texts)):
        norm = np.linalg.norm(embeddings[i])
        assert norm > 0  # Should not be zero vector


def test_embed_texts_empty():
    """Test embedding generation for empty list."""
    embeddings = embed_texts([])
    assert embeddings.shape == (0,)


def test_get_embedding_dimension():
    """Test getting embedding dimension."""
    dimension = get_embedding_dimension()
    assert dimension > 0


def test_faiss_index_roundtrip():
    """Test FAISS index building and searching."""
    # Create test embeddings
    texts = [
        "quantum mechanics and physics",
        "relativity and spacetime",
        "biology and evolution",
        "chemistry and molecules"
    ]
    
    embeddings = embed_texts(texts)
    chunk_ids = list(range(len(texts)))
    
    # Build index
    build_faiss_index(embeddings, chunk_ids)
    
    # Test search
    query_embedding = embed_texts(["physics and quantum"])[0]
    results = semantic_search(query_embedding, top_k=2)
    
    assert len(results) <= 2
    
    # Results should be tuples of (chunk_idx, score)
    for chunk_idx, score in results:
        assert isinstance(chunk_idx, int)
        assert isinstance(score, float)
        assert 0 <= score <= 1


def test_semantic_search_quality():
    """Test that semantic search returns relevant results."""
    texts = [
        "quantum mechanics and physics",
        "relativity and spacetime", 
        "biology and evolution",
        "chemistry and molecules"
    ]
    
    embeddings = embed_texts(texts)
    chunk_ids = list(range(len(texts)))
    
    build_faiss_index(embeddings, chunk_ids)
    
    # Search for quantum-related content
    query_embedding = embed_texts(["quantum physics"])[0]
    results = semantic_search(query_embedding, top_k=1)
    
    assert len(results) > 0
    
    # The quantum mechanics text should be the top result
    top_result = results[0]
    chunk_idx, score = top_result
    
    # The first text (index 0) is about quantum mechanics
    assert chunk_idx == 0
    assert score > 0.5  # Should have reasonable similarity


if __name__ == "__main__":
    pytest.main([__file__])
