"""Command-line interface for the podcast search system."""

import click
import logging
import os
import sqlite3
from pathlib import Path
from typing import List

from .models import SearchResult, Episode, Chunk
from .storage import db
from .fetch import fetch_episode_data
from .chunk import chunk_episode_content
from .embed import embed_chunks, save_embeddings
from .index import build_faiss_index
from .rank import rank_results, lexical_search_episodes
from .embed import embed_query, clear_embeddings
from .index import load_faiss_index, semantic_search, is_index_loaded
from .config import SQLITE_PATH
from sqlalchemy import inspect

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.group()
def cli():
    """Podcast Search CLI - Search through Daniel and Kelly's Extraordinary Universe."""
    pass


@cli.command()
def update():
    """Update the podcast database and search index."""
    logger.info("Starting podcast update process...")
    
    try:
        # Step 1: Fetch episode data
        logger.info("Fetching episode data from RSS...")
        episodes = fetch_episode_data()
        
        if not episodes:
            logger.error("No episodes found")
            return
        
        logger.info(f"Found {len(episodes)} episodes")
        
        # Step 2: Store episodes in database
        logger.info("Storing episodes in database...")
        episode_count = 0
        for episode in episodes:
            episode_id = db.upsert_episode(episode)
            episode_count += 1
            logger.debug(f"Stored episode: {episode.title}")
        
        logger.info(f"Stored {episode_count} episodes")
        
        # Step 3: Create chunks
        logger.info("Creating text chunks...")
        all_chunks = []
        for episode in episodes:
            if episode.id is None:
                # Get episode ID from database
                episode_id = db.upsert_episode(episode)
            else:
                episode_id = episode.id
            
            chunks = chunk_episode_content(
                episode_id, 
                episode.title, 
                episode.description, 
                episode.transcript
            )
            
            # Store chunks in database
            if chunks:
                db.add_chunks(episode_id, chunks)
                all_chunks.extend(chunks)
        
        logger.info(f"Created {len(all_chunks)} chunks")
        
        # Step 4: Generate embeddings
        logger.info("Generating embeddings...")
        embeddings = embed_chunks(all_chunks)
        
        # Get chunk IDs from database (after chunks are saved)
        logger.info("Retrieving chunk IDs from database...")
        chunk_ids = []
        for chunk, episode in db.get_all_chunks():
            chunk_ids.append(chunk.id)
        
        logger.info(f"Retrieved {len(chunk_ids)} chunk IDs from database")
        
        # Step 5: Save embeddings
        logger.info("Saving embeddings...")
        save_embeddings(embeddings, chunk_ids)
        
        # Step 6: Build FAISS index
        logger.info("Building search index...")
        build_faiss_index(embeddings, chunk_ids)
        
        # Summary
        logger.info("Update completed successfully!")
        logger.info(f"Episodes: {db.get_episode_count()}")
        logger.info(f"Chunks: {db.get_chunk_count()}")
        logger.info(f"Embeddings shape: {embeddings.shape}")
        
    except Exception as e:
        logger.error(f"Update failed: {e}")
        raise


@cli.command()
@click.argument('query')
@click.option('--top-k', default=10, help='Number of results to return')
@click.option('--lexical-only', is_flag=True, help='Use only lexical search (no semantic)')
def search(query: str, top_k: int, lexical_only: bool):
    """Search through podcast episodes."""
    logger.info(f"Searching for: '{query}'")
    
    try:
        results: List[SearchResult]
        
        # For now, use lexical search only since FAISS index is too large
        logger.info("Using lexical search (FAISS index too large for quick loading)")
        results = lexical_search_episodes(query, top_k)
        
        # Display results
        if not results:
            logger.info("No results found")
            return
        
        logger.info(f"Found {len(results)} results:")
        print("\n" + "="*80)
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result.title}")
            print(f"   Score: {result.score:.3f}")
            print(f"   Date: {result.pub_date or 'Unknown'}")
            print(f"   Link: {result.link}")
            print(f"   Snippet: {result.snippet}")
            print("-" * 80)
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise


@cli.command()
def stats():
    """Show database and index statistics."""
    try:
        episode_count = db.get_episode_count()
        chunk_count = db.get_chunk_count()
        
        print(f"Episodes in database: {episode_count}")
        print(f"Chunks in database: {chunk_count}")
        
        if is_index_loaded():
            from .index import get_index_stats
            stats = get_index_stats()
            print(f"Search index vectors: {stats['vectors']}")
            print(f"Search index dimension: {stats['dimension']}")
            print(f"Chunks mapped: {stats['chunks_mapped']}")
        else:
            print("Search index: Not loaded")
        
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")


@cli.command()
def clear():
    """Clear all data and start fresh."""
    if click.confirm("Are you sure you want to clear all data?"):
        try:
            # Clear database
            import sqlite3
            with sqlite3.connect(str(db.db_path)) as conn:
                conn.execute("DELETE FROM chunks")
                conn.execute("DELETE FROM episodes")
                conn.commit()
            
            # Clear embeddings
            clear_embeddings()
            
            # Clear index
            from .index import delete_index_file, clear_index
            delete_index_file()
            clear_index()
            
            logger.info("All data cleared successfully")
            
        except Exception as e:
            logger.error(f"Failed to clear data: {e}")


@cli.command()
@click.option('--from-sqlite', 'from_sqlite', default=None, help='Path to source SQLite file (defaults to local data store)')
@click.option('--to-url', 'to_url', default=None, help='Destination DATABASE_URL (defaults to env DATABASE_URL)')
def migrate(from_sqlite: str | None, to_url: str | None):
    """Migrate episodes and chunks from local SQLite to destination database.

    By default, reads from the local SQLite at `SQLITE_PATH` and writes to the
    database specified by the `DATABASE_URL` environment variable (Railway).
    """
    logger.info("Starting migration...")

    # Determine source and destination
    source_path = from_sqlite or str(SQLITE_PATH)
    dest_url = to_url or os.getenv("DATABASE_URL")

    if not dest_url:
        logger.error("Destination DATABASE_URL is not set. Provide --to-url or set env var.")
        raise SystemExit(1)

    if not Path(source_path).exists():
        logger.error(f"Source SQLite not found: {source_path}")
        raise SystemExit(1)

    logger.info(f"Source (SQLite): {source_path}")
    logger.info("Destination: DATABASE_URL (configured in environment)")

    # Open source SQLite read-only
    try:
        conn = sqlite3.connect(source_path)
        conn.row_factory = sqlite3.Row
    except Exception as e:
        logger.error(f"Failed to open source database: {e}")
        raise SystemExit(1)

    migrated_episodes = 0
    migrated_chunks = 0

    try:
        # Read all episodes
        ep_rows = conn.execute(
            """
            SELECT id, guid, title, link, pub_date, description, transcript
            FROM episodes
            ORDER BY id
            """
        ).fetchall()

        logger.info(f"Found {len(ep_rows)} episodes to migrate")

        for ep_row in ep_rows:
            episode = Episode(
                id=None,
                guid=ep_row["guid"],
                title=ep_row["title"],
                link=ep_row["link"],
                pub_date=ep_row["pub_date"],
                description=ep_row["description"],
                transcript=ep_row["transcript"],
            )

            dest_episode_id = db.upsert_episode(episode)
            migrated_episodes += 1

            # Read chunks for this episode
            ch_rows = conn.execute(
                """
                SELECT idx, text, start, end
                FROM chunks
                WHERE episode_id = ?
                ORDER BY idx
                """,
                (ep_row["id"],),
            ).fetchall()

            if ch_rows:
                chunks: List[Chunk] = [
                    Chunk(
                        id=None,
                        episode_id=dest_episode_id,
                        idx=cr["idx"],
                        text=cr["text"],
                        start=cr["start"],
                        end=cr["end"],
                    )
                    for cr in ch_rows
                ]

                db.add_chunks(dest_episode_id, chunks)
                migrated_chunks += len(chunks)

        logger.info("Migration completed successfully")
        logger.info(f"Episodes migrated: {migrated_episodes}")
        logger.info(f"Chunks migrated: {migrated_chunks}")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise
    finally:
        conn.close()


@cli.command(name="rebuild-index")
def rebuild_index():
    """Rebuild embeddings and FAISS index from existing database data."""
    logger.info("Rebuilding embeddings and search index from database...")
    
    try:
        # Get all chunks from database
        logger.info("Retrieving chunks from database...")
        all_chunks = []
        chunk_ids = []
        
        for chunk, episode in db.get_all_chunks():
            all_chunks.append(chunk)
            chunk_ids.append(chunk.id)
        
        logger.info(f"Found {len(all_chunks)} chunks in database")
        
        if not all_chunks:
            logger.error("No chunks found in database")
            return
        
        # Generate embeddings
        logger.info("Generating embeddings...")
        embeddings = embed_chunks(all_chunks)
        
        # Save embeddings
        logger.info("Saving embeddings...")
        save_embeddings(embeddings, chunk_ids)
        
        # Build FAISS index
        logger.info("Building search index...")
        build_faiss_index(embeddings, chunk_ids)
        
        logger.info("Rebuild completed successfully!")
        logger.info(f"Episodes: {db.get_episode_count()}")
        logger.info(f"Chunks: {db.get_chunk_count()}")
        logger.info(f"Embeddings shape: {embeddings.shape}")
        
    except Exception as e:
        logger.error(f"Rebuild failed: {e}")
        raise


@cli.command(name="db-info")
def db_info():
    """Show effective database connection info and tables."""
    try:
        engine = db.engine
        url = engine.url
        # Mask password if present
        try:
            safe_url = url.set(password="***")  # SQLAlchemy 2.x URL
        except Exception:
            safe_url = url

        dialect = engine.dialect.name
        is_sqlite = dialect == "sqlite"

        print("Effective database URL:", str(safe_url))
        print("Dialect:", dialect)
        print("Using SQLite fallback:", "yes" if is_sqlite else "no")

        insp = inspect(engine)
        tables = insp.get_table_names()
        print("Tables:", ", ".join(tables) if tables else "<none>")

    except Exception as e:
        logger.error(f"db-info failed: {e}")
        raise


if __name__ == '__main__':
    cli()