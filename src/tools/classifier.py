from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from loguru import logger

class Classifier:
    def __init__(self):
        try:
            self.model = SentenceTransformer("all-mpnet-base-v2")
            logger.info("Successfully loaded SentenceTransformer model")
        except Exception as e:
            self.model = None
            logger.error(f"Failed to load SentenceTransformer model: {str(e)}")
    
    def score(self, query: str, content: str) -> float:
        if not content or len(content.strip()) < 10:
            logger.debug(f"Content too short: {len(content)} chars")
            return 0.0
            
        embedding_score = self._embedding_similarity(query, content)
        
        keyword_score = self._keyword_overlap(query, content)
        
        final_score = 0.7 * embedding_score + 0.3 * keyword_score
        logger.debug(f"Scores - embedding: {embedding_score:.3f}, keyword: {keyword_score:.3f}, final: {final_score:.3f}")
        
        return min(1.0, max(0.0, final_score))
        
    def _embedding_similarity(self, query: str, content: str) -> float:
        """Calculate embedding similarity."""
        if self.model is None:
            logger.warning("Model not available for embedding similarity")
            return 0.0
        
        try:
            query_embedding = self.model.encode([query])
            content_embedding = self.model.encode([content])
            similarity = cosine_similarity(query_embedding, content_embedding)[0][0]
            return max(0.0, float(similarity))
        except Exception as e:
            logger.error(f"Error calculating embedding similarity: {str(e)}")
            return 0.0
    
    def _keyword_overlap(self, query: str, content: str) -> float:
        """Simple keyword overlap score."""
        #common question words
        stopwords = {'what', 'how', 'when', 'where', 'why', 'who', 'is', 'are', 'the', 'a', 'an'}
        
        query_words = [word.lower() for word in query.split() 
                      if word.lower() not in stopwords and len(word) > 2]
        
        if not query_words:
            logger.debug("No valid query words found after filtering")
            return 0.0
        
        content_lower = content.lower()
        matches = sum(1 for word in query_words if word in content_lower)
        
        return matches / len(query_words)