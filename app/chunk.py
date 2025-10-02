"""Text chunking functionality."""

import re
import logging
from typing import List

from .models import Chunk
from .config import CHUNK_SIZE, CHUNK_OVERLAP

logger = logging.getLogger(__name__)


def to_chunks(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[Chunk]:
    """Split text into overlapping chunks."""
    if not text or not text.strip():
        return []
    
    text = text.strip()
    
    # If text is shorter than chunk size, return as single chunk
    if len(text) <= chunk_size:
        return [Chunk(
            text=text,
            start=0,
            end=len(text)
        )]
    
    chunks = []
    start = 0
    chunk_idx = 0
    
    while start < len(text):
        # Calculate end position
        end = min(start + chunk_size, len(text))
        
        # Try to break at word boundaries
        if end < len(text):
            # Look for the last space within the chunk
            last_space = text.rfind(' ', start, end)
            if last_space > start + chunk_size * 0.7:  # Don't make chunks too small
                end = last_space
        
        chunk_text = text[start:end].strip()
        
        # Skip empty chunks
        if chunk_text:
            chunks.append(Chunk(
                idx=chunk_idx,
                text=chunk_text,
                start=start,
                end=end
            ))
            chunk_idx += 1
        
        # Move start position with overlap
        start = max(start + 1, end - overlap)
        
        # Prevent infinite loop
        if start >= len(text):
            break
    
    logger.debug(f"Created {len(chunks)} chunks from text of length {len(text)}")
    return chunks


def chunk_episode_content(episode_id: int, title: str, description: str, transcript: str) -> List[Chunk]:
    """Create chunks from episode content, prioritizing transcript."""
    chunks = []
    
    # Combine all content for chunking
    content_parts = []
    
    if title:
        content_parts.append(f"Title: {title}")
    
    if description:
        content_parts.append(f"Description: {description}")
    
    if transcript:
        content_parts.append(f"Transcript: {transcript}")
    
    if not content_parts:
        logger.warning(f"No content to chunk for episode {episode_id}")
        return []
    
    full_content = "\n\n".join(content_parts)
    
    # Create chunks
    raw_chunks = to_chunks(full_content)
    
    # Assign episode_id to chunks
    for chunk in raw_chunks:
        chunk.episode_id = episode_id
        chunks.append(chunk)
    
    logger.debug(f"Created {len(chunks)} chunks for episode {episode_id}")
    return chunks


def normalize_text_for_chunking(text: str) -> str:
    """Normalize text before chunking."""
    if not text:
        return ""
    
    # Replace multiple whitespace with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Remove excessive punctuation
    text = re.sub(r'[.]{3,}', '...', text)
    text = re.sub(r'[!]{2,}', '!', text)
    text = re.sub(r'[?]{2,}', '?', text)
    
    # Normalize quotes
    text = text.replace('"', '"').replace('"', '"')
    text = text.replace(''', "'").replace(''', "'")
    
    return text.strip()


def get_chunk_snippet(chunk: Chunk, query: str, snippet_length: int = 200) -> str:
    """Extract a relevant snippet from a chunk based on query."""
    text = chunk.text
    
    # If chunk is short enough, return as is
    if len(text) <= snippet_length:
        return text
    
    # Find query terms in the text (case-insensitive)
    query_words = query.lower().split()
    text_lower = text.lower()
    
    best_start = 0
    max_matches = 0
    
    # Slide through the text looking for the best match
    for start in range(0, len(text) - snippet_length + 1, 50):
        snippet = text[start:start + snippet_length]
        snippet_lower = snippet.lower()
        
        matches = sum(1 for word in query_words if word in snippet_lower)
        if matches > max_matches:
            max_matches = matches
            best_start = start
    
    # Extract snippet with some context
    snippet_start = max(0, best_start - 20)
    snippet_end = min(len(text), snippet_start + snippet_length + 20)
    
    snippet = text[snippet_start:snippet_end]
    
    # Add ellipsis if needed
    if snippet_start > 0:
        snippet = "..." + snippet
    if snippet_end < len(text):
        snippet = snippet + "..."
    
    return snippet