"""Tests for text chunking functionality."""

import pytest
from app.chunk import to_chunks, chunk_episode_content, get_chunk_snippet


def test_to_chunks_short_text():
    """Test chunking of text shorter than chunk size."""
    text = "This is a short text."
    chunks = to_chunks(text, chunk_size=100, overlap=20)
    
    assert len(chunks) == 1
    assert chunks[0].text == text
    assert chunks[0].start == 0
    assert chunks[0].end == len(text)


def test_to_chunks_long_text():
    """Test chunking of long text with overlap."""
    text = "This is a much longer text that should be split into multiple chunks. " * 10
    chunks = to_chunks(text, chunk_size=100, overlap=20)
    
    assert len(chunks) > 1
    
    # Check overlap
    for i in range(1, len(chunks)):
        prev_chunk = chunks[i-1]
        curr_chunk = chunks[i]
        
        # Current chunk should start before previous chunk ends (due to overlap)
        assert curr_chunk.start < prev_chunk.end


def test_to_chunks_empty_text():
    """Test chunking of empty text."""
    chunks = to_chunks("")
    assert len(chunks) == 0
    
    chunks = to_chunks("   ")
    assert len(chunks) == 0


def test_chunk_episode_content():
    """Test chunking episode content."""
    episode_id = 1
    title = "Test Episode"
    description = "This is a test episode description."
    transcript = "This is the transcript content. It contains the full conversation."
    
    chunks = chunk_episode_content(episode_id, title, description, transcript)
    
    assert len(chunks) > 0
    
    # All chunks should have the same episode_id
    for chunk in chunks:
        assert chunk.episode_id == episode_id
    
    # Check that content is included
    combined_text = " ".join(chunk.text for chunk in chunks)
    assert title in combined_text
    assert description in combined_text
    assert transcript in combined_text


def test_get_chunk_snippet():
    """Test snippet generation from chunk."""
    text = "This is a longer piece of text that contains the word relativity and other scientific concepts."
    chunk = type('Chunk', (), {'text': text})()
    
    snippet = get_chunk_snippet(chunk, "relativity", snippet_length=50)
    
    assert "relativity" in snippet.lower()
    assert len(snippet) <= 80  # Should be close to snippet_length + some padding


def test_get_chunk_snippet_short_chunk():
    """Test snippet generation for short chunk."""
    text = "Short text."
    chunk = type('Chunk', (), {'text': text})()
    
    snippet = get_chunk_snippet(chunk, "text", snippet_length=100)
    
    assert snippet == text  # Should return full text if shorter than snippet_length


if __name__ == "__main__":
    pytest.main([__file__])
