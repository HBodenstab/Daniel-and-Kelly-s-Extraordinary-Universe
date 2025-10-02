"""Database abstraction layer supporting SQLite and PostgreSQL."""

import os
import logging
from typing import List, Optional, Iterator, Tuple, Union
from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy import create_engine, text, Index
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from .models import Episode, Chunk
from .config import SQLITE_PATH, DB_TIMEOUT, DATABASE_URL

logger = logging.getLogger(__name__)

# SQLAlchemy base
Base = declarative_base()


class EpisodeModel(Base):
    """SQLAlchemy model for episodes."""
    __tablename__ = "episodes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    guid = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    link = Column(String, nullable=False)
    pub_date = Column(String)
    description = Column(Text)
    transcript = Column(Text)
    
    # Relationship
    chunks = relationship("ChunkModel", back_populates="episode", cascade="all, delete-orphan")


class ChunkModel(Base):
    """SQLAlchemy model for chunks."""
    __tablename__ = "chunks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    episode_id = Column(Integer, ForeignKey("episodes.id"), nullable=False)
    idx = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    start = Column(Integer, nullable=False)
    end = Column(Integer, nullable=False)
    
    # Relationship
    episode = relationship("EpisodeModel", back_populates="chunks")


class Database:
    """Database abstraction layer supporting SQLite and PostgreSQL."""
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or self._get_database_url()
        self.engine = self._create_engine()
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.init_db()
    
    def _get_database_url(self) -> str:
        """Get database URL from environment or default to SQLite."""
        return DATABASE_URL
    
    def _create_engine(self):
        """Create SQLAlchemy engine."""
        if self.database_url.startswith("sqlite"):
            return create_engine(
                self.database_url, connect_args={"timeout": DB_TIMEOUT}
            )
        else:
            # PostgreSQL configuration
            return create_engine(
                self.database_url,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True
            )
    
    def init_db(self) -> None:
        """Initialize database schema."""
        try:
            Base.metadata.create_all(bind=self.engine)
            
            # Create indexes for performance
            with self.engine.connect() as conn:
                # Check if indexes exist before creating
                if self.database_url.startswith("sqlite"):
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_episodes_guid ON episodes(guid)"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_chunks_episode_id ON chunks(episode_id)"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_episodes_title ON episodes(title)"))
                else:
                    # PostgreSQL indexes
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_episodes_guid ON episodes(guid)"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_chunks_episode_id ON chunks(episode_id)"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_episodes_title ON episodes(title)"))
                conn.commit()
            
            logger.info("Database initialized")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    def upsert_episode(self, episode: Episode) -> int:
        """Insert or update an episode, return episode ID."""
        with self.SessionLocal() as session:
            try:
                # Check if episode exists
                existing = session.query(EpisodeModel).filter(
                    EpisodeModel.guid == episode.guid
                ).first()
                
                if existing:
                    # Update existing episode
                    existing.title = episode.title
                    existing.link = episode.link
                    existing.pub_date = episode.pub_date
                    existing.description = episode.description
                    existing.transcript = episode.transcript
                    episode_id = existing.id
                else:
                    # Create new episode
                    episode_model = EpisodeModel(
                        guid=episode.guid,
                        title=episode.title,
                        link=episode.link,
                        pub_date=episode.pub_date,
                        description=episode.description,
                        transcript=episode.transcript
                    )
                    session.add(episode_model)
                    session.flush()  # Get the ID
                    episode_id = episode_model.id
                
                session.commit()
                logger.debug(f"Upserted episode: {episode.title} (ID: {episode_id})")
                return episode_id
                
            except Exception as e:
                session.rollback()
                logger.error(f"Failed to upsert episode: {e}")
                raise
    
    def add_chunks(self, episode_id: int, chunks: List[Chunk]) -> None:
        """Add chunks for an episode."""
        with self.SessionLocal() as session:
            try:
                # Clear existing chunks for this episode
                session.query(ChunkModel).filter(
                    ChunkModel.episode_id == episode_id
                ).delete()
                
                # Insert new chunks
                chunk_models = [
                    ChunkModel(
                        episode_id=episode_id,
                        idx=chunk.idx,
                        text=chunk.text,
                        start=chunk.start,
                        end=chunk.end
                    )
                    for chunk in chunks
                ]
                session.add_all(chunk_models)
                session.commit()
                
                logger.debug(f"Added {len(chunks)} chunks for episode {episode_id}")
                
            except Exception as e:
                session.rollback()
                logger.error(f"Failed to add chunks: {e}")
                raise
    
    def get_episode(self, episode_id: int) -> Optional[Episode]:
        """Get episode by ID."""
        with self.SessionLocal() as session:
            episode_model = session.query(EpisodeModel).filter(
                EpisodeModel.id == episode_id
            ).first()
            
            if episode_model:
                return Episode(
                    id=episode_model.id,
                    guid=episode_model.guid,
                    title=episode_model.title,
                    link=episode_model.link,
                    pub_date=episode_model.pub_date,
                    description=episode_model.description,
                    transcript=episode_model.transcript
                )
            return None
    
    def get_all_chunks(self) -> Iterator[Tuple[Chunk, Episode]]:
        """Get all chunks with their episode information."""
        with self.SessionLocal() as session:
            results = session.query(ChunkModel, EpisodeModel).join(
                EpisodeModel, ChunkModel.episode_id == EpisodeModel.id
            ).order_by(ChunkModel.episode_id, ChunkModel.idx).all()
            
            for chunk_model, episode_model in results:
                chunk = Chunk(
                    id=chunk_model.id,
                    episode_id=chunk_model.episode_id,
                    idx=chunk_model.idx,
                    text=chunk_model.text,
                    start=chunk_model.start,
                    end=chunk_model.end
                )
                episode = Episode(
                    id=episode_model.id,
                    guid=episode_model.guid,
                    title=episode_model.title,
                    link=episode_model.link,
                    pub_date=episode_model.pub_date,
                    description=episode_model.description,
                    transcript=episode_model.transcript
                )
                yield chunk, episode
    
    def search_episodes_title_desc(self, query: str) -> List[Episode]:
        """Lexical search over episode titles and descriptions."""
        search_term = f"%{query}%"
        with self.SessionLocal() as session:
            episodes = session.query(EpisodeModel).filter(
                (EpisodeModel.title.like(search_term)) |
                (EpisodeModel.description.like(search_term))
            ).order_by(EpisodeModel.title).all()
            
            return [
                Episode(
                    id=ep.id, guid=ep.guid, title=ep.title, link=ep.link,
                    pub_date=ep.pub_date, description=ep.description, transcript=ep.transcript
                )
                for ep in episodes
            ]
    
    def get_episode_count(self) -> int:
        """Get total number of episodes."""
        with self.SessionLocal() as session:
            return session.query(EpisodeModel).count()
    
    def get_chunk_count(self) -> int:
        """Get total number of chunks."""
        with self.SessionLocal() as session:
            return session.query(ChunkModel).count()
    
    def close(self):
        """Close database connections."""
        self.engine.dispose()


# Global database instance
db = Database()
