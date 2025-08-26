import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from unittest.mock import patch
from tools.classifier import Classifier

def test_classifier_init():
    """Test classifier can be created."""
    with patch('tools.classifier.SentenceTransformer'):
        classifier = Classifier()
        assert classifier is not None


def test_score_short_content():
    """Test score returns 0 for short content."""
    with patch('tools.classifier.SentenceTransformer'):
        classifier = Classifier()
        score = classifier.score("test", "short")
        assert score == 0.0


def test_score_long_content():
    """Test score works with long content."""
    with patch('tools.classifier.SentenceTransformer'):
        classifier = Classifier()
        score = classifier.score("test", "this is a long content that has more than ten characters")
        assert 0.0 <= score <= 1.0


def test_keyword_overlap():
    """Test keyword overlap calculation."""
    with patch('tools.classifier.SentenceTransformer'):
        classifier = Classifier()
        score = classifier._keyword_overlap("machine learning", "machine learning is great")
        assert score == 1.0


def test_embedding_without_model():
    """Test embedding similarity without model."""
    with patch('tools.classifier.SentenceTransformer'):
        classifier = Classifier()
        classifier.model = None
        score = classifier._embedding_similarity("test", "content")
        assert score == 0.0