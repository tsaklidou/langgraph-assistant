#!/bin/bash

echo "Starting Chatbot..."

# Change to src directory
cd /app/src

# Check if ChromaDB already exists
if [ ! -d "./chromadb" ] || [ -z "$(ls -A ./chromadb 2>/dev/null)" ]; then
    echo "ChromaDB not found. Running preprocessing..."
    
    # Create a temporary preprocessing script with correct path
    cd preprocessing
    cat > temp_main.py << 'EOF'
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from chunker import chunk_text, load_markdown_file
from chroma_loader import ChromaDBLoader
from loguru import logger

def main():
    """Preprocessing pipeline."""
    try:
        # Use correct path for Docker container (../../data/data.md)
        logger.info("Loading markdown file...")
        text = load_markdown_file("../../data/data.md")
        logger.info(f"Loaded {len(text):,} characters")
        
        # 2. Chunk the text
        logger.info("Chunking text...")
        chunks = chunk_text(text, method="table_rows")
        logger.info(f"Created {len(chunks)} chunks")
        
        # 3. Load into ChromaDB
        logger.info("Loading into ChromaDB...")
        loader = ChromaDBLoader("jedi_ai")
        loader.add_chunks(chunks)
        logger.info("Successfully loaded chunks into ChromaDB")
        
        # 4. Test with a sample query
        logger.info("Testing with sample query...")
        results = loader.query("People working remote", n_results=3)
        logger.info(f"Found {len(results['documents'][0])} results:")
        for i, doc in enumerate(results['documents'][0]):
            logger.info(f"Result {i+1}: {doc[:60]}...")
        
        total_count = loader.get_count()
        logger.info(f"Total documents in database: {total_count}")
        logger.success("Pipeline completed successfully")
        
    except FileNotFoundError as e:
        logger.error(f"Markdown file not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
EOF
    
    # Run the preprocessing with correct path
    python temp_main.py
    
    if [ $? -eq 0 ]; then
        echo "Preprocessing completed successfully!"
        rm temp_main.py  # Clean up
    else
        echo "Preprocessing failed!"
        rm temp_main.py  # Clean up
        exit 1
    fi
    
    cd ..
else
    echo "ChromaDB already exists, skipping preprocessing"
fi

# Start the Streamlit app
echo "Starting Streamlit app..."
streamlit run app/ui_app.py --server.port=8501 --server.address=0.0.0.0