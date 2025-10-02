"""HTML parsing and transcript extraction."""

import re
import logging
from typing import Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def sanitize_text(text: str) -> str:
    """Normalize whitespace and clean up text."""
    if not text:
        return ""
    
    # Replace multiple whitespace with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    # Remove any remaining HTML entities
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = text.replace('&#39;', "'")
    
    return text


def extract_transcript(html: str) -> str:
    """Extract transcript from episode HTML page."""
    try:
        soup = BeautifulSoup(html, 'lxml')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Strategy 1: Look for explicit "Transcript" section
        transcript_text = _find_transcript_section(soup)
        if transcript_text:
            logger.debug("Found transcript using explicit section method")
            return sanitize_text(transcript_text)
        
        # Strategy 2: Look for common transcript patterns
        transcript_text = _find_transcript_patterns(soup)
        if transcript_text:
            logger.debug("Found transcript using pattern matching")
            return sanitize_text(transcript_text)
        
        # Strategy 3: Look for long text content (fallback)
        transcript_text = _find_long_text_content(soup)
        if transcript_text:
            logger.debug("Found transcript using long text fallback")
            return sanitize_text(transcript_text)
        
        logger.debug("No transcript found, returning empty string")
        return ""
        
    except Exception as e:
        logger.error(f"Error extracting transcript: {e}")
        return ""


def _find_transcript_section(soup: BeautifulSoup) -> Optional[str]:
    """Look for explicit transcript section."""
    # Look for headings containing "transcript"
    transcript_headers = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'], 
                                     string=lambda text: text and 'transcript' in text.lower())
    
    for header in transcript_headers:
        # Collect all text after the transcript header
        text_parts = []
        current = header.next_sibling
        while current:
            if hasattr(current, 'get_text'):
                text = current.get_text().strip()
                if text:
                    text_parts.append(text)
            elif isinstance(current, str) and current.strip():
                text_parts.append(current.strip())
            current = current.next_sibling
        
        if text_parts:
            return " ".join(text_parts)
    
    # Look for divs or sections with transcript-related classes/IDs
    transcript_containers = soup.find_all(['div', 'section'], 
                                        class_=re.compile(r'transcript', re.IGNORECASE))
    
    for container in transcript_containers:
        text = container.get_text()
        if len(text.strip()) > 50:
            return text
    
    return None


def _find_transcript_patterns(soup: BeautifulSoup) -> Optional[str]:
    """Look for common transcript patterns."""
    # Look for text that contains speaker patterns (e.g., "Speaker:", "Host:", "Guest:")
    speaker_patterns = [
        r'\w+:',  # "Speaker:" anywhere in text
        r'\[.*?\]\s*',   # [Speaker Name]
        r'\(.*?\)\s*',   # (Speaker Name)
    ]
    
    all_text = soup.get_text()
    
    for pattern in speaker_patterns:
        matches = re.findall(pattern, all_text)
        if len(matches) >= 2:  # At least 2 speaker turns
            return all_text
    
    # Look for text with timestamps
    timestamp_pattern = r'\d{1,2}:\d{2}'
    if re.search(timestamp_pattern, all_text):
        return all_text
    
    return None


def _find_long_text_content(soup: BeautifulSoup) -> Optional[str]:
    """Find the longest text content as a fallback."""
    # Get all paragraph elements
    paragraphs = soup.find_all('p')
    if not paragraphs:
        return None
    
    # Combine all paragraph text
    all_text = ' '.join(p.get_text() for p in paragraphs)
    
    # Only return if it's substantial content
    if len(all_text.strip()) > 500:
        return all_text
    
    # Try div elements with substantial content
    divs = soup.find_all('div')
    long_divs = [div for div in divs if len(div.get_text().strip()) > 500]
    
    if long_divs:
        # Return the longest one
        longest_div = max(long_divs, key=lambda d: len(d.get_text()))
        return longest_div.get_text()
    
    return None


def extract_metadata(html: str) -> dict:
    """Extract metadata from episode page."""
    try:
        soup = BeautifulSoup(html, 'lxml')
        
        metadata = {}
        
        # Extract title
        title_elem = soup.find('title')
        if title_elem:
            metadata['title'] = sanitize_text(title_elem.get_text())
        
        # Extract description from meta tags
        desc_elem = soup.find('meta', attrs={'name': 'description'})
        if desc_elem:
            metadata['description'] = sanitize_text(desc_elem.get('content', ''))
        
        # Extract publication date
        date_elem = soup.find('meta', attrs={'property': 'article:published_time'})
        if date_elem:
            metadata['pub_date'] = sanitize_text(date_elem.get('content', ''))
        
        return metadata
        
    except Exception as e:
        logger.error(f"Error extracting metadata: {e}")
        return {}