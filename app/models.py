"""Data models for the podcast search system."""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class Episode:
    """Represents a podcast episode."""
    id: Optional[int] = None
    guid: Optional[str] = None
    title: str = ""
    link: str = ""
    pub_date: Optional[str] = None
    description: str = ""
    transcript: str = ""

    @property
    def searchable_content(self) -> str:
        """Combine title, description, and transcript for search."""
        parts = [self.title, self.description, self.transcript]
        return " ".join(part for part in parts if part.strip())


@dataclass
class Chunk:
    """Represents a text chunk from an episode."""
    id: Optional[int] = None
    episode_id: int = 0
    idx: int = 0
    text: str = ""
    start: int = 0
    end: int = 0

    @property
    def length(self) -> int:
        """Length of the chunk text."""
        return len(self.text)


@dataclass
class SearchResult:
    """Represents a search result with scoring."""
    episode_id: int
    title: str
    pub_date: Optional[str]
    link: str
    score: float
    snippet: str
    semantic_score: float
    lexical_score: float


@dataclass
class SearchRequest:
    """Request payload for search API."""
    query: str
    top_k: int = 10


@dataclass
class SearchResponse:
    """Response payload for search API."""
    results: List[SearchResult]
    total_found: int
    query: str