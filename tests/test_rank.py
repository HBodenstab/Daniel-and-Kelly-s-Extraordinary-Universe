"""Tests for hybrid ranking functionality."""

import pytest
from app.rank import lexical_score, hybrid_score, normalize_query


def test_lexical_score_exact_match():
    """Test lexical scoring with exact matches."""
    score = lexical_score("quantum mechanics", "quantum mechanics")
    assert score == 1.0  # Should be perfect match


def test_lexical_score_partial_match():
    """Test lexical scoring with partial matches."""
    score = lexical_score("quantum", "quantum mechanics and physics")
    assert score > 0.5  # Should have good partial match


def test_lexical_score_no_match():
    """Test lexical scoring with no match."""
    score = lexical_score("biology", "quantum mechanics")
    assert score < 0.5  # Should have low score


def test_lexical_score_empty_inputs():
    """Test lexical scoring with empty inputs."""
    assert lexical_score("", "test") == 0.0
    assert lexical_score("test", "") == 0.0
    assert lexical_score("", "") == 0.0


def test_hybrid_score():
    """Test hybrid score combination."""
    # Test with default alpha
    score = hybrid_score(0.8, 0.6)
    expected = 0.7 * 0.8 + 0.3 * 0.6  # alpha=0.7
    assert abs(score - expected) < 0.001
    
    # Test with custom alpha
    score = hybrid_score(0.8, 0.6, alpha=0.5)
    expected = 0.5 * 0.8 + 0.5 * 0.6
    assert abs(score - expected) < 0.001


def test_hybrid_score_edge_cases():
    """Test hybrid scoring edge cases."""
    # All semantic
    score = hybrid_score(1.0, 0.0, alpha=1.0)
    assert score == 1.0
    
    # All lexical
    score = hybrid_score(0.0, 1.0, alpha=0.0)
    assert score == 1.0
    
    # Zero scores
    score = hybrid_score(0.0, 0.0)
    assert score == 0.0


def test_normalize_query():
    """Test query normalization."""
    # Basic normalization
    query = "  This   is   a   test  "
    result = normalize_query(query)
    assert result == "this is test"  # "a" is removed as stop word
    
    # Stop word removal
    query = "the quantum mechanics and physics"
    result = normalize_query(query)
    assert "the" not in result
    assert "and" not in result
    assert "quantum" in result
    assert "mechanics" in result
    assert "physics" in result


def test_normalize_query_empty():
    """Test query normalization with empty input."""
    assert normalize_query("") == ""
    assert normalize_query("   ") == ""
    assert normalize_query("the and or") == ""  # Only stop words


def test_normalize_query_case_insensitive():
    """Test that normalization is case insensitive."""
    query1 = "QUANTUM MECHANICS"
    query2 = "quantum mechanics"
    
    result1 = normalize_query(query1)
    result2 = normalize_query(query2)
    
    assert result1 == result2


if __name__ == "__main__":
    pytest.main([__file__])
