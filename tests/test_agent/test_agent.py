import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from unittest.mock import Mock, MagicMock

# Mock ALL the complex dependencies BEFORE importing
sys.modules['langgraph'] = Mock()
sys.modules['langgraph.graph'] = Mock()
sys.modules['agent.agent_state'] = Mock()
sys.modules['agent.llm_generator'] = Mock()
sys.modules['loguru'] = Mock()

# Mock tools
sys.modules['tools'] = Mock()
sys.modules['tools.rag_tool'] = Mock()
sys.modules['tools.web_search'] = Mock()
sys.modules['tools.classifier'] = Mock()

# Mock specific classes that agent imports
mock_state_graph = Mock()
mock_end = Mock()
mock_llm_generator = Mock()

# Set up the mocks properly
sys.modules['langgraph.graph'].StateGraph = mock_state_graph
sys.modules['langgraph.graph'].END = mock_end
sys.modules['agent.llm_generator'].LLMGenerator = mock_llm_generator

# Mock the functions from tools
sys.modules['tools.rag_tool'].rag_search = Mock(return_value=[])
sys.modules['tools.web_search'].web_search_tool = Mock(return_value=[])
sys.modules['tools.classifier'].Classifier = Mock()

# Now import the actual agent
from agent.agent import LangGraphAgent


def test_agent_can_be_created():
    """Test that agent can be created with mocked dependencies."""
    # Mock the graph compilation
    mock_workflow = Mock()
    mock_workflow.compile.return_value = Mock()
    mock_state_graph.return_value = mock_workflow
    
    agent = LangGraphAgent()
    
    assert agent is not None
    assert agent.threshold == 0.5


def test_has_content_method():
    """Test the _has_content method."""
    # Create agent with mocked dependencies
    mock_workflow = Mock()
    mock_workflow.compile.return_value = Mock()
    mock_state_graph.return_value = mock_workflow
    
    agent = LangGraphAgent()
    
    # Test _has_content method
    assert agent._has_content("This is good content") == True
    assert agent._has_content("") == False
    assert agent._has_content("no relevant information found") == False


def test_route_rag_method():
    """Test RAG routing method."""
    mock_workflow = Mock()
    mock_workflow.compile.return_value = Mock()
    mock_state_graph.return_value = mock_workflow
    
    agent = LangGraphAgent(threshold=0.5)
    
    # Test routing decisions
    good_state = {"rag_score": 0.7}
    bad_state = {"rag_score": 0.3}
    
    assert agent._route_rag(good_state) == "good"
    assert agent._route_rag(bad_state) == "bad"


def test_route_web_method():
    """Test web routing method."""
    mock_workflow = Mock()
    mock_workflow.compile.return_value = Mock()
    mock_state_graph.return_value = mock_workflow
    
    agent = LangGraphAgent(threshold=0.5)
    
    # Test web routing (threshold - 0.2 = 0.3)
    good_state = {"web_score": 0.4}
    bad_state = {"web_score": 0.1}
    
    assert agent._route_web(good_state) == "good"
    assert agent._route_web(bad_state) == "bad"


def test_agent_with_custom_threshold():
    """Test agent with custom threshold."""
    mock_workflow = Mock()
    mock_workflow.compile.return_value = Mock()
    mock_state_graph.return_value = mock_workflow
    
    agent = LangGraphAgent(threshold=0.8)
    
    assert agent.threshold == 0.8