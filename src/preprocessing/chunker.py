from typing import List
from langchain.text_splitter import RecursiveCharacterTextSplitter


def chunk_text(text: str, method: str = "recursive", chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    """
    Chunk text using different methods.
    
    Args:
        text: The input text to chunk
        method: "recursive" or "table_rows"
        chunk_size: Maximum size of each chunk (for recursive method)
        chunk_overlap: Overlap between chunks (for recursive method)
    
    Returns:
        List of text chunks
    """
    if method == "table_rows":
        # Split by table rows, extract content between pipes
        lines = text.split('\n')
        chunks = []
        for line in lines:
            line = line.strip()
            # Skip header and separator rows
            if line.startswith('|') and not line.startswith('| :') and 'text' not in line.lower():
                # Extract content between pipes
                content = line.strip('|').strip()
                if content:  # Only add non-empty content
                    chunks.append(content)
        return chunks
    
    elif method == "recursive":
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )
        chunks = text_splitter.split_text(text)
        return chunks
    
    else:
        raise ValueError(f"Unknown method: {method}")


def load_markdown_file(file_path: str) -> str:
    """Load markdown file content."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()