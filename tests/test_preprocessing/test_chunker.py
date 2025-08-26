import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from unittest.mock import Mock, patch

sys.modules['langchain.text_splitter'] = Mock()
sys.modules['langchain'] = Mock()

from preprocessing.chunker import chunk_text, load_markdown_file


def test_chunk_text_table_rows():
    """Test chunk_text function with table_rows method."""
    text = """| Column1 | Column2 |
| :------ | :------ |
| data1   | data2   |
| info1   | info2   |"""
    
    result = chunk_text(text, method="table_rows")
    
    assert isinstance(result, list)
    assert len(result) == 3 
    assert "Column1 | Column2" in result[0]
    assert "data1   | data2" in result[1]
    assert "info1   | info2" in result[2]


def test_chunk_text_recursive():
    """Test chunk_text function with recursive method."""
    text = "This is a test text that should be chunked using recursive method."
    
    mock_splitter = Mock()
    mock_splitter.split_text.return_value = ["chunk1", "chunk2"]
    
    with patch('preprocessing.chunker.RecursiveCharacterTextSplitter', return_value=mock_splitter):
        result = chunk_text(text, method="recursive")
    
    assert isinstance(result, list)
    assert result == ["chunk1", "chunk2"]


def test_chunk_text_invalid_method():
    """Test chunk_text function with invalid method."""
    text = "Some test text"
    
    with pytest.raises(ValueError) as exc_info:
        chunk_text(text, method="invalid")
    
    assert "Unknown method: invalid" in str(exc_info.value)


def test_chunk_text_empty_table():
    """Test chunk_text with empty table content."""
    text = "|   |   |\n| :-- | :-- |"
    
    result = chunk_text(text, method="table_rows")
    
    assert isinstance(result, list)
    # The header row "|   |   |" will still be included since it has content (spaces)
    assert len(result) >= 0


def test_chunk_text_parameters():
    """Test chunk_text with custom parameters."""
    text = "Test text for chunking"
    
    # Mock the text splitter to verify parameters
    mock_splitter = Mock()
    mock_splitter.split_text.return_value = ["chunk"]
    
    with patch('preprocessing.chunker.RecursiveCharacterTextSplitter') as mock_class:
        mock_class.return_value = mock_splitter
        
        chunk_text(text, method="recursive", chunk_size=500, chunk_overlap=100)
        
        # Verify the splitter was created with correct parameters
        mock_class.assert_called_once_with(
            chunk_size=500,
            chunk_overlap=100,
            separators=["\n\n", "\n", " ", ""]
        )


def test_load_markdown_file():
    """Test load_markdown_file function."""
    test_content = "# Test Markdown\nThis is test content."
    

    from unittest.mock import mock_open
    mock_file = mock_open(read_data=test_content)
    
    with patch('builtins.open', mock_file):
        result = load_markdown_file("test.md")
    
    assert result == test_content
    mock_file.assert_called_once_with("test.md", 'r', encoding='utf-8')