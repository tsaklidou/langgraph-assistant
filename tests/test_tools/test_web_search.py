import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from unittest.mock import patch, Mock
from tools.web_search import (
    url_is_accepted, 
    content_is_relevant, 
    get_urls_from_google_search,
    extract_content_from_url,
    web_search_tool
)


def test_url_is_accepted_default():
    """Test URL acceptance with no lists."""
    result = url_is_accepted("https://example.com")
    assert result == True


def test_url_is_accepted_with_accepted_list():
    """Test URL acceptance with accepted list."""
    result = url_is_accepted("https://example.com", accepted_list=["example.com"])
    assert result == True
    
    result = url_is_accepted("https://bad.com", accepted_list=["example.com"])
    assert result == False


def test_url_is_accepted_with_rejected_list():
    """Test URL acceptance with rejected list."""
    result = url_is_accepted("https://bad.com", rejected_list=["bad.com"])
    assert result == False
    
    result = url_is_accepted("https://good.com", rejected_list=["bad.com"])
    assert result == True


def test_content_is_relevant():
    """Test content relevance check."""
    #short content
    assert content_is_relevant("short") == False
    
    #needs 100+ chars AND 10+ words
    long_content = "This is a long piece of content that has more than ten words and definitely has more than one hundred characters to pass the test"
    assert content_is_relevant(long_content) == True
    
    #None content
    assert content_is_relevant(None) == False


def test_get_urls_from_google_search_success():
    """Test successful Google search."""
    with patch('tools.web_search.serpapi') as mock_serpapi:
        mock_search = Mock()
        mock_search.as_dict.return_value = {
            "search_metadata": {"status": "Success"},
            "organic_results": [
                {
                    "title": "Test Title",
                    "link": "https://example.com",
                    "snippet": "Test snippet"
                }
            ]
        }
        mock_serpapi.search.return_value = mock_search
        
        result = get_urls_from_google_search("test query")
        
        assert result["status"] == "Success"
        assert len(result["articles"]) == 1
        assert result["articles"][0]["title"] == "Test Title"


def test_get_urls_from_google_search_exception():
    """Test Google search with exception."""
    with patch('tools.web_search.serpapi.search', side_effect=Exception("API error")):
        with pytest.raises(Exception):
            get_urls_from_google_search("test query")


def test_extract_content_from_url_success():
    """Test successful content extraction."""
    with patch('tools.web_search.fetch_url', return_value="<html>content</html>"), \
         patch('tools.web_search.extract', return_value="This is a very long extracted content with more than ten words and definitely more than one hundred characters"), \
         patch('tools.web_search.use_config'), \
         patch('tools.web_search.content_is_relevant', return_value=True):
        
        result = extract_content_from_url("https://example.com")
        assert result is not None


def test_extract_content_from_url_failure():
    """Test content extraction failure."""
    with patch('tools.web_search.fetch_url', return_value=None):
        result = extract_content_from_url("https://example.com")
        assert result is None


def test_web_search_tool_success():
    """Test web search tool with successful results."""
    with patch('tools.web_search.get_urls_from_google_search') as mock_search, \
         patch('tools.web_search.extract_content_from_url') as mock_extract:
        
        mock_search.return_value = {
            "status": "Success",
            "articles": [
                {
                    "title": "Test Article",
                    "url": "https://example.com",
                    "source": "Example",
                    "date": "2024-01-01",
                    "snippet": "Test snippet"
                }
            ]
        }
        mock_extract.return_value = "Extracted content"
        
        result = web_search_tool("test query")
        
        assert len(result) == 1
        assert result[0]["title"] == "Test Article"
        assert result[0]["content"] == "Extracted content"


def test_web_search_tool_empty_results():
    """Test web search tool with empty results."""
    with patch('tools.web_search.get_urls_from_google_search') as mock_search:
        mock_search.return_value = {
            "status": "Success",
            "articles": []
        }
        
        result = web_search_tool("test query")
        assert result == []