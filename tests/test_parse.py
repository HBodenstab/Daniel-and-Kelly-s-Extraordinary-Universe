"""Tests for HTML parsing and transcript extraction."""

import pytest
from app.parse import extract_transcript, sanitize_text


def test_extract_transcript_with_transcript_section():
    """Test transcript extraction when explicit transcript section exists."""
    html = """
    <html>
    <body>
        <h2>Transcript</h2>
        <p>This is the transcript content. It contains the full conversation between the hosts.</p>
        <p>They discuss various topics including science and technology.</p>
    </body>
    </html>
    """
    
    result = extract_transcript(html)
    
    assert result
    assert "transcript content" in result
    assert "science and technology" in result


def test_extract_transcript_with_speaker_patterns():
    """Test transcript extraction using speaker patterns."""
    html = """
    <html>
    <body>
        <p>Daniel: Welcome to our podcast!</p>
        <p>Kelly: Thanks for having me.</p>
        <p>Daniel: Today we'll discuss quantum mechanics.</p>
        <p>Kelly: That sounds fascinating.</p>
    </body>
    </html>
    """
    
    result = extract_transcript(html)
    
    assert result
    assert "Daniel:" in result
    assert "Kelly:" in result
    assert "quantum mechanics" in result


def test_extract_transcript_no_transcript():
    """Test transcript extraction when no transcript is found."""
    html = """
    <html>
    <body>
        <h1>Episode Title</h1>
        <p>This is just a description, not a transcript.</p>
    </body>
    </html>
    """
    
    result = extract_transcript(html)
    
    # Should return empty string when no transcript found
    assert result == ""


def test_sanitize_text():
    """Test text sanitization."""
    text = "  This   has   multiple    spaces  "
    result = sanitize_text(text)
    
    assert result == "This has multiple spaces"
    
    # Test with HTML entities
    text_with_entities = "This &amp; that &quot;quoted&quot;"
    result = sanitize_text(text_with_entities)
    
    assert "&amp;" not in result
    assert "&quot;" not in result
    assert "This & that" in result
    assert "quoted" in result


def test_sanitize_text_empty():
    """Test sanitize_text with empty input."""
    assert sanitize_text("") == ""
    assert sanitize_text(None) == ""
    assert sanitize_text("   ") == ""


if __name__ == "__main__":
    pytest.main([__file__])
