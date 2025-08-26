from typing import TypedDict, List, Dict, Any

class AgentState(TypedDict, total=False):
    """State of the agent during processing."""
    query: str                     
    original_query: str
    history: List[Dict[str, Any]]
    rag_content: str
    rag_score: float
    rag_chunks: List[Dict]
    web_content: str
    web_score: float
    web_results: List[Dict]
    final_answer: str
    method_used: str