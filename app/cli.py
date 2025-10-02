"""Command-line interface for the podcast search system."""

import click
import logging
from typing import List

from .models import SearchResult
from .storage import db
from .fetch import fetch_episode_data
from .chunk import chunk_episode_content
from .embed import embed_chunks, save_embeddings
from .index import build_faiss_index
from .rank import rank_results, lexical_search_episodes
from .embed import embed_query, clear_embeddings
from .index import load_faiss_index, semantic_search, is_index_loaded

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
        
        # Get chunk IDs for saving
        chunk_ids = [chunk.id for chunk in all_chunks if chunk.id is not None]
        
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
        
        if lexical_only:
            logger.info("Using lexical search only")
            results = lexical_search_episodes(query, top_k)
        else:
            # Check if index is loaded
            if not is_index_loaded():
                logger.info("Loading search index...")
                if not load_faiss_index():
                    logger.warning("Could not load semantic index, falling back to lexical search")
                    results = lexical_search_episodes(query, top_k)
                else:
                    logger.info("Index loaded successfully")
            
            if is_index_loaded():
                # Perform semantic search
                logger.info("Performing semantic search...")
                query_embedding = embed_query(query)
                semantic_results = semantic_search(query_embedding, top_k * 2)  # Get more for ranking
                
                # Rank results
                results = rank_results(query, semantic_results, top_k)
            else:
                results = lexical_search_episodes(query, top_k)
        
        # Display results
        if not results:
            logger.info("No results found")
            return
        
        logger.info(f"Found {len(results)} results:")
        print("\n" + "="*80)
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result.title}")
            print(f"   Score: {result.score:.3f} (semantic: {result.semantic_score:.3f}, lexical: {result.lexical_score:.3f})")
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


if __name__ == '__main__':
    cli()