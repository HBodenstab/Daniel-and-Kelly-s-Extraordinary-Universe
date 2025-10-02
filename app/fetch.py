"""RSS and HTML fetching functionality."""

import requests
import xml.etree.ElementTree as ET
import logging
import time
from typing import List, Dict, Optional
from urllib.parse import urljoin

from .models import Episode
from .config import RSS_URL, USER_AGENT, SCRAPE_DELAY

logger = logging.getLogger(__name__)


def fetch_rss() -> bytes:
    """Fetch RSS feed content."""
    try:
        response = requests.get(RSS_URL, headers={"User-Agent": USER_AGENT}, timeout=30)
        response.raise_for_status()
        logger.info(f"Fetched RSS feed: {len(response.content)} bytes")
        return response.content
    except requests.RequestException as e:
        logger.error(f"Failed to fetch RSS feed: {e}")
        raise


def parse_rss(rss_content: bytes) -> List[Dict[str, str]]:
    """Parse RSS content and extract episode information."""
    try:
        root = ET.fromstring(rss_content)
        
        # Handle namespaces
        namespaces = {
            'atom': 'http://www.w3.org/2005/Atom',
            'itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd'
        }
        
        episodes = []
        for item in root.findall('.//item'):
            episode_data = {}
            
            # Extract basic fields
            title_elem = item.find('title')
            episode_data['title'] = title_elem.text.strip() if title_elem is not None and title_elem.text else ""
            
            link_elem = item.find('link')
            episode_data['link'] = link_elem.text.strip() if link_elem is not None and link_elem.text else ""
            
            pub_date_elem = item.find('pubDate')
            episode_data['pub_date'] = pub_date_elem.text.strip() if pub_date_elem is not None and pub_date_elem.text else ""
            
            # Description (CDATA handling)
            desc_elem = item.find('description')
            if desc_elem is not None:
                episode_data['description'] = desc_elem.text.strip() if desc_elem.text else ""
            else:
                episode_data['description'] = ""
            
            # GUID
            guid_elem = item.find('guid')
            episode_data['guid'] = guid_elem.text.strip() if guid_elem is not None and guid_elem.text else None
            
            # iTunes description (often more detailed)
            itunes_desc_elem = item.find('itunes:summary', namespaces)
            if itunes_desc_elem is not None and itunes_desc_elem.text:
                episode_data['description'] = itunes_desc_elem.text.strip()
            
            episodes.append(episode_data)
            logger.debug(f"Parsed episode: {episode_data['title']}")
        
        logger.info(f"Parsed {len(episodes)} episodes from RSS")
        return episodes
    
    except ET.ParseError as e:
        logger.error(f"Failed to parse RSS XML: {e}")
        raise


def fetch_html(url: str, max_retries: int = 2) -> Optional[str]:
    """Fetch HTML content with retries and error handling."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    }
    
    for attempt in range(max_retries + 1):
        try:
            logger.debug(f"Fetching HTML from {url} (attempt {attempt + 1})")
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Small delay to be respectful
            if attempt < max_retries:
                time.sleep(SCRAPE_DELAY)
            
            logger.debug(f"Successfully fetched HTML: {len(response.text)} characters")
            return response.text
            
        except requests.RequestException as e:
            logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
            if attempt < max_retries:
                time.sleep(1 * (attempt + 1))  # Exponential backoff
            else:
                logger.error(f"All attempts failed for {url}")
                return None
    
    return None


def fetch_episode_data() -> List[Episode]:
    """Fetch all episode data from RSS and individual episode pages."""
    logger.info("Starting episode data fetch...")
    
    # Fetch RSS feed
    rss_content = fetch_rss()
    episode_data_list = parse_rss(rss_content)
    
    episodes = []
    for i, episode_data in enumerate(episode_data_list):
        logger.info(f"Processing episode {i+1}/{len(episode_data_list)}: {episode_data['title']}")
        
        # Create episode object
        episode = Episode(
            guid=episode_data.get('guid'),
            title=episode_data['title'],
            link=episode_data['link'],
            pub_date=episode_data.get('pub_date'),
            description=episode_data['description'],
            transcript=""  # Will be populated by parse.py
        )
        
        # Fetch individual episode page for transcript
        if episode.link:
            html_content = fetch_html(episode.link)
            if html_content:
                # Import here to avoid circular imports
                from .parse import extract_transcript
                episode.transcript = extract_transcript(html_content)
                logger.debug(f"Extracted transcript: {len(episode.transcript)} characters")
            else:
                logger.warning(f"Could not fetch HTML for {episode.link}")
        
        episodes.append(episode)
        
        # Respectful delay between requests
        if i < len(episode_data_list) - 1:
            time.sleep(SCRAPE_DELAY)
    
    logger.info(f"Fetched {len(episodes)} episodes")
    return episodes