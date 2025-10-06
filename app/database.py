"""Database abstraction layer supporting SQLite and PostgreSQL.

This module is resilient to missing/misconfigured PostgreSQL environment variables
in hosted environments (e.g., Railway). It attempts to construct a proper
PostgreSQL SQLAlchemy URL from available env vars, ensures SSL is enabled,
and falls back to SQLite if connection/initialization fails so the API can
still boot and pass health checks.
"""

import os
import logging
from typing import List, Optional, Iterator, Tuple, Union
from pathlib import Path
from urllib.parse import urlparse, urlencode, parse_qsl, urlunparse

from sqlalchemy import create_engine, text, Index
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
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


class UsageModel(Base):
    """SQLAlchemy model for tracking usage statistics."""
    __tablename__ = "usage"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=func.now())
    ip_address = Column(String)       # optional, for unique user tracking
    endpoint = Column(String)         # e.g. "/api/search"


class Database:
    """Database abstraction layer supporting SQLite and PostgreSQL."""
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or self._get_database_url()
        self.engine = self._create_engine()
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.init_db()
    
    def _get_database_url(self) -> str:
        """Get database URL from environment or default to SQLite.

        Priority:
        1) DATABASE_URL (normalize scheme, ensure sslmode)
        2) Construct from Railway-style env vars (PG*/POSTGRES*)
        3) Fallback to SQLite
        """
        env_url = os.getenv("DATABASE_URL")
        if env_url:
            return self._normalize_database_url(env_url)

        # Railway provides PG* variables. Also support POSTGRES_* variants.
        host = os.getenv("PGHOST") or os.getenv("POSTGRES_HOST")
        port = os.getenv("PGPORT") or os.getenv("POSTGRES_PORT") or "5432"
        user = os.getenv("PGUSER") or os.getenv("POSTGRES_USER")
        password = os.getenv("PGPASSWORD") or os.getenv("POSTGRES_PASSWORD")
        dbname = os.getenv("PGDATABASE") or os.getenv("POSTGRES_DB")

        if host and user and password and dbname:
            url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}"
            return self._ensure_sslmode(url)

        # Fallback to configured default (likely SQLite)
        return str(DATABASE_URL)
    
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
                pool_pre_ping=True,
            )
    
    def init_db(self) -> None:
        """Initialize database schema. Falls back to SQLite on failure."""
        try:
            Base.metadata.create_all(bind=self.engine)
            # Create indexes for performance
            with self.engine.connect() as conn:
                if self.database_url.startswith("sqlite"):
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_episodes_guid ON episodes(guid)"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_chunks_episode_id ON chunks(episode_id)"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_episodes_title ON episodes(title)"))
                else:
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_episodes_guid ON episodes(guid)"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_chunks_episode_id ON chunks(episode_id)"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_episodes_title ON episodes(title)"))
                conn.commit()
            logger.info("Database initialized")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            allow_fallback = os.getenv("ALLOW_SQLITE_FALLBACK", "1") != "0"
            if allow_fallback and not self.database_url.startswith("sqlite"):
                # Fallback to SQLite to allow app to boot
                logger.warning("Falling back to SQLite database due to initialization failure")
                self.database_url = f"sqlite:///{SQLITE_PATH}"
                self.engine = self._create_engine()
                self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
                Base.metadata.create_all(bind=self.engine)
                with self.engine.connect() as conn:
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_episodes_guid ON episodes(guid)"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_chunks_episode_id ON chunks(episode_id)"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_episodes_title ON episodes(title)"))
                    conn.commit()
                logger.info("SQLite fallback database initialized")
            else:
                # Re-raise if fallback not allowed
                raise

    def _normalize_database_url(self, url: str) -> str:
        """Normalize DATABASE_URL, enforce driver and SSL for Postgres."""
        try:
            parsed = urlparse(url)
            scheme = parsed.scheme
            # Convert postgres:// to postgresql+psycopg2:// if needed
            if scheme == "postgres":
                scheme = "postgresql+psycopg2"
            elif scheme == "postgresql":
                scheme = "postgresql+psycopg2"

            if scheme.startswith("postgresql"):
                # Rebuild URL with possibly updated scheme and sslmode
                query = dict(parse_qsl(parsed.query))
                # Ensure sslmode
                if "sslmode" not in query:
                    query["sslmode"] = "require"
                new_query = urlencode(query)
                rebuilt = parsed._replace(scheme=scheme, query=new_query)
                return urlunparse(rebuilt)

            return url
        except Exception:
            # If anything goes wrong, return original
            return url

    def _ensure_sslmode(self, url: str) -> str:
        """Ensure sslmode=require is present for Postgres URLs."""
        try:
            parsed = urlparse(url)
            if not parsed.scheme.startswith("postgres"):
                return url
            query = dict(parse_qsl(parsed.query))
            if "sslmode" not in query:
                query["sslmode"] = "require"
            new_query = urlencode(query)
            rebuilt = parsed._replace(query=new_query)
            return urlunparse(rebuilt)
        except Exception:
            return url
    
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
    
    def record_usage(self, ip_address: str, endpoint: str) -> None:
        """Record a usage event."""
        with self.SessionLocal() as session:
            try:
                usage = UsageModel(ip_address=ip_address, endpoint=endpoint)
                session.add(usage)
                session.commit()
                logger.debug(f"Recorded usage: {endpoint} from {ip_address}")
            except Exception as e:
                session.rollback()
                logger.error(f"Failed to record usage: {e}")
    
    def get_usage_stats(self) -> dict:
        """Get usage statistics."""
        with self.SessionLocal() as session:
            try:
                total_searches = session.query(func.count(UsageModel.id)).scalar() or 0
                unique_users = session.query(func.count(func.distinct(UsageModel.ip_address))).scalar() or 0
                return {
                    "total_searches": total_searches,
                    "unique_users": unique_users
                }
            except Exception as e:
                logger.error(f"Failed to get usage stats: {e}")
                return {"total_searches": 0, "unique_users": 0}
    
    def get_detailed_analytics(self) -> dict:
        """Get detailed analytics data."""
        with self.SessionLocal() as session:
            try:
                # Basic stats
                total_searches = session.query(func.count(UsageModel.id)).scalar() or 0
                unique_users = session.query(func.count(func.distinct(UsageModel.ip_address))).scalar() or 0
                
                # Database content stats
                total_episodes = session.query(func.count(EpisodeModel.id)).scalar() or 0
                total_chunks = session.query(func.count(ChunkModel.id)).scalar() or 0
                
                # Recent activity (last 24 hours)
                from datetime import datetime, timedelta
                yesterday = datetime.utcnow() - timedelta(days=1)
                recent_searches = session.query(func.count(UsageModel.id)).filter(
                    UsageModel.timestamp >= yesterday
                ).scalar() or 0
                
                # Top search times (hourly distribution)
                hourly_stats = session.query(
                    func.extract('hour', UsageModel.timestamp).label('hour'),
                    func.count(UsageModel.id).label('count')
                ).group_by(
                    func.extract('hour', UsageModel.timestamp)
                ).order_by('count').all()
                
                # Search frequency over time (last 7 days)
                week_ago = datetime.utcnow() - timedelta(days=7)
                daily_stats = session.query(
                    func.date(UsageModel.timestamp).label('date'),
                    func.count(UsageModel.id).label('count')
                ).filter(
                    UsageModel.timestamp >= week_ago
                ).group_by(
                    func.date(UsageModel.timestamp)
                ).order_by('date').all()
                
                return {
                    "total_searches": total_searches,
                    "unique_users": unique_users,
                    "total_episodes": total_episodes,
                    "total_chunks": total_chunks,
                    "recent_searches": recent_searches,
                    "hourly_distribution": [{"hour": int(h), "count": int(c)} for h, c in hourly_stats],
                    "daily_stats": [{"date": str(d), "count": int(c)} for d, c in daily_stats],
                    "last_updated": datetime.utcnow().isoformat()
                }
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
                    "last_updated": datetime.utcnow().isoformat()
                }
    
    def close(self):
        """Close database connections."""
        self.engine.dispose()


# Global database instance (resilient to failures)
try:
    db = Database()
except Exception as e:
    logger.warning(f"Primary database init failed, using SQLite fallback: {e}")
    db = Database(database_url=f"sqlite:///{SQLITE_PATH}")
