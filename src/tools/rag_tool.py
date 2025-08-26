import sys
sys.path.append('./preprocessing')
from chroma_loader import ChromaDBLoader
from loguru import logger
import os


# TODO
os.environ["ANONYMIZED_TELEMETRY"] = "False"

def rag_search(query: str, num_results: int = 5, similarity_threshold: float = 0.2) -> list:
    """
    Search the knowledge base for relevant information.
    
    Args:
        query: Search query string
        num_results: Number of results to return
        similarity_threshold: Minimum similarity score (0.0 to 1.0)
        
    Returns:
        List of chunk objects with text and metadata
    """
    try:
        loader = ChromaDBLoader("jedi_ai")
        logger.info(f"Collection count: {loader.get_count()}")
        
        results = loader.query(query, n_results=num_results)
        
        if not results or not results.get('documents') or not results['documents'][0]:
            return []
        
        documents = results['documents'][0]
        distances = results['distances'][0]
        ids = results.get('ids', [0])[0]
        
        chunks = []
        for i, (doc, distance, chunk_id) in enumerate(zip(documents, distances, ids)):
            similarity = 1 - distance  #distance to similarity
            if similarity >= similarity_threshold:
                chunks.append({
                    "text": doc,
                    "score": similarity,
                    "id": chunk_id,
                    "source": "Knowledge Base",
                    "title": f"Document Chunk {i+1}"
                })
        
        return chunks
        
    except Exception as e:
        logger.error(f"RAG search error: {str(e)}")
        return []
    

# # Test
# if __name__ == "__main__":
#     result = rag_search("Tell me the percentage of remote workers in Denver", 3)
#     print(result)

