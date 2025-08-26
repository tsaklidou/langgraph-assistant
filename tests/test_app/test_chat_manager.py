import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from unittest.mock import Mock


sys.modules['app.database'] = Mock()
sys.modules['agent.agent'] = Mock()
sys.modules['loguru'] = Mock()

from app.chat_manager import ChatManager


def test_capture_thought():
    """Test thought capture works."""
    manager = object.__new__(ChatManager)
    manager.current_thoughts = []
    manager.streaming_callback = None
    
    # Test thought capture
    manager._capture_thought("test thought")
    assert len(manager.current_thoughts) == 1
    assert manager.current_thoughts[0] == "test thought"


def test_generate_simple_title():
    """Test simple title generation."""
    manager = object.__new__(ChatManager)
    
    # Test title generation
    title = manager._generate_title("What is machine learning and how does it work")
    assert title == "What Is Machine Learning And..."
    
    title = manager._generate_title("Short question")
    assert title == "Short Question"


def test_title_logic():
    """Test title generation logic without dependencies."""
    message = "What is machine learning and how does it work"
    
    # Test the core logic
    words = message.split()[:5]
    title = " ".join(words)
    if len(message.split()) > 5:
        title += "..."
    result = title.title()
    
    assert result == "What Is Machine Learning And..."