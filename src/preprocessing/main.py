from chunker import chunk_text, load_markdown_file
from chroma_loader import ChromaDBLoader
from loguru import logger


# #TODO
# import os
# if os.getenv("DISABLE_SSL", "false").lower() == "true":
#     os.environ["HF_HUB_DISABLE_SSL_VERIFICATION"] = "1"
 
 

def main():
    """Preprocessing pipeline."""
    
    try:
        # 1. Load markdown file
        logger.info("Loading markdown file...")
        text = load_markdown_file("../data/data.md")
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
        results = loader.query("Remote workers in Seattle", n_results=3)
        
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