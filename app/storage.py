"""SQLite storage operations for episodes and chunks."""

import sqlite3
import logging
from typing import List, Optional, Iterator, Tuple
from pathlib import Path

from .models import Episode, Chunk
from .config import SQLITE_PATH, DB_TIMEOUT

logger = logging.getLogger(__name__)


class Database:
    """SQLite database manager."""
    
    def __init__(self, db_path: Path = SQLITE_PATH):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self) -> None:
        """Initialize database schema."""
        with sqlite3.connect(str(self.db_path), timeout=DB_TIMEOUT) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS episodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guid TEXT UNIQUE,
                    title TEXT NOT NULL,
                    link TEXT NOT NULL,
                    pub_date TEXT,
                    description TEXT,
                    transcript TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    episode_id INTEGER NOT NULL,
                    idx INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    start INTEGER NOT NULL,
                    end INTEGER NOT NULL,
                    FOREIGN KEY(episode_id) REFERENCES episodes(id)
                )
            """)
            
            # Indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_episodes_guid ON episodes(guid)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_episode_id ON chunks(episode_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_episodes_title ON episodes(title)")
            
            conn.commit()
            logger.info("Database initialized")
    
    def upsert_episode(self, episode: Episode) -> int:
        """Insert or update an episode, return episode ID."""
        with sqlite3.connect(str(self.db_path), timeout=DB_TIMEOUT) as conn:
            cursor = conn.execute("""
                INSERT OR REPLACE INTO episodes (guid, title, link, pub_date, description, transcript)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (episode.guid, episode.title, episode.link, episode.pub_date, 
                  episode.description, episode.transcript))
            
            # Get the episode ID
            if cursor.lastrowid:
                episode_id = cursor.lastrowid
            else:
                # If no row was inserted, find existing episode
                cursor = conn.execute(
                    "SELECT id FROM episodes WHERE guid = ? OR link = ?",
                    (episode.guid, episode.link)
                )
                result = cursor.fetchone()
                episode_id = result[0] if result else None
            
            conn.commit()
            logger.debug(f"Upserted episode: {episode.title} (ID: {episode_id})")
            return episode_id
    
    def add_chunks(self, episode_id: int, chunks: List[Chunk]) -> None:
        """Add chunks for an episode."""
        # Clear existing chunks for this episode
        with sqlite3.connect(str(self.db_path), timeout=DB_TIMEOUT) as conn:
            conn.execute("DELETE FROM chunks WHERE episode_id = ?", (episode_id,))
            
            # Insert new chunks
            chunk_data = [
                (episode_id, chunk.idx, chunk.text, chunk.start, chunk.end)
                for chunk in chunks
            ]
            conn.executemany("""
                INSERT INTO chunks (episode_id, idx, text, start, end)
                VALUES (?, ?, ?, ?, ?)
            """, chunk_data)
            
            conn.commit()
            logger.debug(f"Added {len(chunks)} chunks for episode {episode_id}")
    
    def get_episode(self, episode_id: int) -> Optional[Episode]:
        """Get episode by ID."""
        with sqlite3.connect(str(self.db_path), timeout=DB_TIMEOUT) as conn:
            cursor = conn.execute("""
                SELECT id, guid, title, link, pub_date, description, transcript
                FROM episodes WHERE id = ?
            """, (episode_id,))
            
            result = cursor.fetchone()
            if result:
                return Episode(
                    id=result[0], guid=result[1], title=result[2], link=result[3],
                    pub_date=result[4], description=result[5], transcript=result[6]
                )
            return None
    
    def get_all_chunks(self) -> Iterator[Tuple[Chunk, Episode]]:
        """Get all chunks with their episode information."""
        with sqlite3.connect(str(self.db_path), timeout=DB_TIMEOUT) as conn:
            cursor = conn.execute("""
                SELECT c.id, c.episode_id, c.idx, c.text, c.start, c.end,
                       e.id, e.guid, e.title, e.link, e.pub_date, e.description, e.transcript
                FROM chunks c
                JOIN episodes e ON c.episode_id = e.id
                ORDER BY c.episode_id, c.idx
            """)
            
            for row in cursor:
                chunk = Chunk(
                    id=row[0], episode_id=row[1], idx=row[2], text=row[3],
                    start=row[4], end=row[5]
                )
                episode = Episode(
                    id=row[6], guid=row[7], title=row[8], link=row[9],
                    pub_date=row[10], description=row[11], transcript=row[12]
                )
                yield chunk, episode
    
    def search_episodes_title_desc(self, query: str) -> List[Episode]:
        """Lexical search over episode titles and descriptions."""
        search_term = f"%{query}%"
        with sqlite3.connect(str(self.db_path), timeout=DB_TIMEOUT) as conn:
            cursor = conn.execute("""
                SELECT id, guid, title, link, pub_date, description, transcript
                FROM episodes
                WHERE title LIKE ? OR description LIKE ?
                ORDER BY title
            """, (search_term, search_term))
            
            episodes = []
            for row in cursor:
                episodes.append(Episode(
                    id=row[0], guid=row[1], title=row[2], link=row[3],
                    pub_date=row[4], description=row[5], transcript=row[6]
                ))
            
            return episodes
    
    def get_episode_count(self) -> int:
        """Get total number of episodes."""
        with sqlite3.connect(str(self.db_path), timeout=DB_TIMEOUT) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM episodes")
            return cursor.fetchone()[0]
    
    def get_chunk_count(self) -> int:
        """Get total number of chunks."""
        with sqlite3.connect(str(self.db_path), timeout=DB_TIMEOUT) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM chunks")
            return cursor.fetchone()[0]


# Global database instance
db = Database()