import chromadb
import chromadb.utils.embedding_functions as embedding_functions
from typing import List, Dict, Any
# import uuid

#TODO
import os
os.environ["ANONYMIZED_TELEMETRY"] = "False"

class ChromaDBLoader:
    """Simple ChromaDB loader for text chunks."""
    
    def __init__(self, collection_name: str = "markdown_chunks"):
        """Initialize ChromaDB client and collection."""
        self.client = chromadb.PersistentClient(path="./chroma_db")
        
        # Use better embedding model
        sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-mpnet-base-v2"
        )
        
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=sentence_transformer_ef
        )
    
    def add_chunks(self, chunks: List[str]) -> None:
        """Add text chunks to ChromaDB."""
        # Generate simple IDs and metadata
        ids = [f"chunk_{i}" for i in range(len(chunks))]
        metadatas = [{"chunk_index": i} for i in range(len(chunks))]
        
        self.collection.add(
            documents=chunks,
            metadatas=metadatas,
            ids=ids
        )
        print(f"Added {len(chunks)} chunks to database")
    
    def query(self, query_text: str, n_results: int = 5) -> Dict[str, Any]:
        """Query similar chunks from the database."""
        return self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
    
    def get_count(self) -> int:
        """Get number of documents in collection."""
        return self.collection.count()