import sys
from typing import Dict, Any, Literal, Callable, Optional
from langgraph.graph import StateGraph, END
from loguru import logger

from agent.agent_state import AgentState
from agent.llm_generator import LLMGenerator

sys.path.append('./tools')
from tools.rag_tool import rag_search
from tools.web_search import web_search_tool
from tools.classifier import Classifier

class LangGraphAgent:
    """Agent using LangGraph."""
    
    def __init__(self, threshold: float = 0.5, on_thought: Optional[Callable[[str], None]] = None):
        self.threshold = threshold
        self.on_thought = on_thought or (lambda x: None)
        self.llm = LLMGenerator()
        self.graph = self._build_graph()
        logger.info(f"LangGraphAgent initialized with threshold: {threshold}")
    
    def _build_graph(self):
        """Build LangGraph workflow."""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("rag_search", self._rag_node)
        workflow.add_node("web_search", self._web_node)
        workflow.add_node("generate_answer", self._generate_node)
        workflow.add_node("fallback", self._fallback_node)
        
        # Define flow
        workflow.set_entry_point("rag_search")
        
        workflow.add_conditional_edges(
            "rag_search",
            self._route_rag,
            {
                "good": "generate_answer",
                "bad": "web_search"
            }
        )
        
        workflow.add_conditional_edges(
            "web_search",
            self._route_web,
            {
                "good": "generate_answer",
                "bad": "fallback"
            }
        )
        
        workflow.add_edge("generate_answer", END)
        workflow.add_edge("fallback", END)
        
        logger.debug("LangGraph workflow built successfully")
        return workflow.compile()
    
    def _rag_node(self, state: AgentState) -> AgentState:
        """RAG search node with classification."""
        self.on_thought("Searching knowledge base...")
        logger.info(f"Starting RAG search for query: {state['original_query']}")
        
        rag_chunks = rag_search(state["original_query"], similarity_threshold=0.0)
        
        if rag_chunks:
            rag_content = "\n\n".join([chunk["text"] for chunk in rag_chunks])
            logger.info(f"RAG found {len(rag_chunks)} chunks")
        else:
            rag_content = f"No relevant information found for: '{state['original_query']}'"
            logger.warning("No RAG chunks found")
        
        if self._has_content(rag_content):
            classifier = Classifier()
            score = classifier.score(state["original_query"], rag_content)
        else:
            score = 0.0
        
        logger.info(f"RAG quality score: {score:.3f}")
        self.on_thought(f"RAG quality score: {score:.2f}")
        
        return {**state, 
                "rag_content": rag_content, 
                "rag_score": score,
                "rag_chunks": rag_chunks}
    
    def _web_node(self, state: AgentState) -> AgentState:
        """Web search node with classification."""
        self.on_thought("RAG insufficient, searching web...")
        logger.info(f"Starting web search for query: {state['original_query']}")
        
        web_results = web_search_tool(state["original_query"], num_results=2)
        
        web_content = ""
        if web_results:
            web_content = "\n\n".join([result["content"] for result in web_results if result.get("content")])
            logger.info(f"Web search found {len(web_results)} results")
        
        if not web_content:
            web_content = f"No useful web results found for: '{state['original_query']}'"
            logger.warning("No useful web content found")
   
        if self._has_content(web_content):
            classifier = Classifier()
            score = classifier.score(state["original_query"], web_content)
        else:
            score = 0.0
        
        logger.info(f"Web search quality score: {score:.3f}")
        self.on_thought(f"Web search quality score: {score:.2f}")
        
        return {**state, 
                "web_content": web_content, 
                "web_score": score,
                "web_results": web_results}
    
    def _generate_node(self, state: AgentState) -> AgentState:
        """Generate final answer using LLM."""
    
        if state["rag_score"] >= self.threshold:
            content = state["rag_content"]
            method = "rag"
            self.on_thought("Using knowledge base content")
            logger.info("Using RAG content for answer generation")
        else:
            content = state["web_content"]
            method = "web"
            self.on_thought("Using web search content")
            logger.info("Using web content for answer generation")
        
        self.on_thought("Generating final answer...")
        
        answer = self.llm.generate_answer(
            state["original_query"],
            content,
            state.get("history", [])
        )
        
        logger.info(f"Answer generated using {method} method")
        
        return {
            **state,
            "final_answer": answer,
            "method_used": method
        }
    
    def _fallback_node(self, state: AgentState) -> AgentState:
        """Fallback when both fail."""
        self.on_thought("Both searches failed, using fallback")
        logger.warning("Both RAG and web search failed, using fallback")
        return {
            **state,
            "final_answer": "I am sorry, I cannot answer your question at this time.",
            "method_used": "fallback"
        }
    
    def _route_rag(self, state: AgentState) -> Literal["good", "bad"]:
        """Route after RAG classification."""
        if state["rag_score"] >= self.threshold:
            self.on_thought("RAG quality is sufficient")
            logger.debug(f"RAG score {state['rag_score']:.3f} >= threshold {self.threshold}, routing to answer generation")
            return "good"
        else:
            self.on_thought("RAG quality too low, trying web search")
            logger.debug(f"RAG score {state['rag_score']:.3f} < threshold {self.threshold}, routing to web search")
            return "bad"
    
    def _route_web(self, state: AgentState) -> Literal["good", "bad"]:
        """Route after web classification."""
        web_threshold = self.threshold - 0.2
        if state["web_score"] >= web_threshold:
            self.on_thought("Web search quality acceptable")
            logger.debug(f"Web score {state['web_score']:.3f} >= threshold {web_threshold}, routing to answer generation")
            return "good"
        else:
            self.on_thought("Web search quality insufficient")
            logger.debug(f"Web score {state['web_score']:.3f} < threshold {web_threshold}, routing to fallback")
            return "bad"
    
    def _has_content(self, content: str) -> bool:
        """Check if content is useful."""
        if not content:
            return False
        bad_signals = ["no relevant information", "search error", "could not find"]
        has_bad_signal = any(signal in content.lower() for signal in bad_signals)
        if has_bad_signal:
            logger.debug("Content contains bad signals, marking as unusable")
        return not has_bad_signal
    
    def answer(self, question: str, history=None) -> Dict[str, Any]:
        """Answer a question using the agent with optional conversation history."""
        
        logger.info(f"Processing question: {question}")
        
        #initial state setup
        initial_state = {
            "original_query": question,
            "history": history or [],
            "rag_content": "",
            "rag_score": 0.0,
            "rag_chunks": [],
            "web_content": "",
            "web_score": 0.0,
            "web_results": [],
            "final_answer": "",
            "method_used": ""
        }
        
        result = self.graph.invoke(initial_state)
        
        logger.info(f"Question answered using {result['method_used']} method")
        
        return {
            "answer": result["final_answer"],
            "method": result["method_used"],
            "rag_score": result["rag_score"],
            "web_score": result["web_score"],
            "rag_chunks": result.get("rag_chunks", []),
            "web_results": result.get("web_results", [])
        }