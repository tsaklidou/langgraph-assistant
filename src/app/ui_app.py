import streamlit as st
import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.chat_manager import ChatManager
from loguru import logger

#custom page configuration
st.set_page_config(
    page_title="AI Insight", 
    page_icon="app/static/bot_logo.png",  
    layout="wide"
)

if "chat_manager" not in st.session_state:
    try:
        st.session_state.chat_manager = ChatManager()
        logger.info("ChatManager initialized for Streamlit session")
    except Exception as e:
        logger.error(f"Failed to initialize ChatManager: {str(e)}")
        st.error("Failed to initialize the application. Please try again.")

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "streaming_thoughts" not in st.session_state:
    st.session_state.streaming_thoughts = []

if "last_thought_count" not in st.session_state:
    st.session_state.last_thought_count = 0

if "first_message_sent" not in st.session_state:
    st.session_state.first_message_sent = False

if "message_feedback" not in st.session_state:
    st.session_state.message_feedback = {}

if "current_conversation" not in st.session_state:
    st.session_state.current_conversation = None

def add_custom_css():
    """Add custom CSS styling"""
    st.markdown("""
    <style>
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #F8F9FA;
    }
    
    /* Chat messages styling */
    [data-testid="stChatMessageContent"] div div div {
        background-color: transparent !important;
    }
    
    .user-message {
        background-color: #eff6ff !important;
        border-radius: 15px;
        padding: 10px 15px;
        margin-bottom: 10px;
    }
    
    .assistant-message {
        background-color: #FFFFFF !important;
        border: 1px solid #E6E6E6;
        border-radius: 15px;
        padding: 10px 15px;
        margin-bottom: 10px;
    }
    
    /* Header styling */
    h1 {
        font-family: sans-serif;
        font-weight: 600;
    }
    
    /* Main heading */
    .main-heading {
        font-family: sans-serif;
        font-size: 2.5rem;
        font-weight: 600;
        margin-bottom: 2rem;
    }
    
    .main-heading span {
        color: #d4a600;
    }
    
    /* Animation for thoughts */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .thought-item {
        animation: fadeIn 0.3s ease-out forwards;
    }
    
    /* Agent thought process styling */
    .agent-thought-header {
        margin-top: 15px;
        margin-bottom: 10px;
        font-weight: bold;
        color: #666;
    }
    
    /* Center logo in sidebar */
    .sidebar-logo-container {
        display: flex;
        justify-content: center;
        margin: 20px 0;
    }
    
    /* Chat input styling */
    .stTextInput>div>div>input {
        border-radius: 20px;
    }
    
    /* Button styling */
    .stButton>button {
        border-radius: 20px;
    }
    
    /* Feedback buttons */
    .feedback-button {
        padding: 2px 8px;
        margin-right: 10px;
        border-radius: 12px;
        font-size: 14px;
    }
    
    /* Trash icon fix */
    button:has(span:contains("🗑️")) {
        padding: 0.25rem 0.75rem;
        font-size: 1rem;
        min-height: 0;
    }
    
    /* Processing state styling */
    .processing-feedback {
        color: #666;
        font-style: italic;
        font-size: 0.9em;
    }
    </style>
    """, unsafe_allow_html=True)

def login_page():
    """Display login page"""
    st.markdown('<div class="main-heading">Welcome to <span>AI Insight</span></div>', unsafe_allow_html=True)
    
    with st.form("login"):
        email = st.text_input("Email", placeholder="your.email@example.com")
        password = st.text_input("Password", type="password", placeholder="any password")
        submit = st.form_submit_button("Login")
        
        if submit and email and "@" in email and password:
            try:
                user_id = st.session_state.chat_manager.login_user(email)
                st.session_state.user_id = user_id
                st.session_state.user_email = email
                logger.info(f"User logged in via Streamlit: {email} (ID: {user_id})")
                st.rerun()
            except Exception as e:
                logger.error(f"Login failed for {email}: {str(e)}")
                st.error("Login failed. Please try again.")

def sidebar():
    """Display sidebar with conversations"""
    with st.sidebar:
        st.title("Chats")
        
        # Logout/ New Chat buttons
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Logout", use_container_width=True):
                logger.info(f"User logged out: {st.session_state.get('user_email', 'unknown')}")
                st.session_state.clear()
                st.rerun()
        
        with col2:
            if st.button("New Chat", use_container_width=True):
                logger.info("New chat started")
                st.session_state.current_conversation = None
                st.session_state.first_message_sent = False
                # Clear message feedback for new chat
                st.session_state.message_feedback = {}
                st.rerun()
        
        st.divider()
        
        # Display conversations
        try:
            conversations = st.session_state.chat_manager.get_user_conversations(st.session_state.user_id)
            logger.debug(f"Loaded {len(conversations)} conversations for sidebar")
        except Exception as e:
            logger.error(f"Failed to load conversations: {str(e)}")
            conversations = []
        
        for conv in conversations:
            col1, col2 = st.columns([4, 1])
            
            with col1:
                title = conv['title'][:25] + "..." if len(conv['title']) > 25 else conv['title']
                if st.button(title, key=f"conv_{conv['id']}", use_container_width=True):
                    logger.info(f"Switched to conversation {conv['id']}: {conv['title']}")
                    st.session_state.current_conversation = conv['id']
                    st.session_state.first_message_sent = True
                    # Load existing feedback for this conversation
                    load_conversation_feedback(conv['id'])
                    st.rerun()
            
            with col2:
                if st.button("🗑️", key=f"del_{conv['id']}"):
                    try:
                        st.session_state.chat_manager.delete_conversation(conv['id'])
                        logger.info(f"Deleted conversation {conv['id']}")
                        if st.session_state.get('current_conversation') == conv['id']:
                            st.session_state.current_conversation = None
                            st.session_state.first_message_sent = False
                            st.session_state.message_feedback = {}
                        st.rerun()
                    except Exception as e:
                        logger.error(f"Failed to delete conversation {conv['id']}: {str(e)}")
                        st.error("Failed to delete conversation")

def load_conversation_feedback(conversation_id):
    """Load existing feedback for all messages in a conversation"""
    try:
        messages = st.session_state.chat_manager.get_conversation_messages(conversation_id)
        st.session_state.message_feedback = {}
        feedback_count = 0
        for msg in messages:
            if msg.get('feedback'):
                st.session_state.message_feedback[msg['id']] = msg['feedback']
                feedback_count += 1
        logger.debug(f"Loaded {feedback_count} feedback items for conversation {conversation_id}")
    except Exception as e:
        logger.error(f"Failed to load feedback for conversation {conversation_id}: {str(e)}")

def handle_feedback(message_id, feedback_type):
    """Handle feedback with simplified state management"""
    try:
        # Update in database
        success = st.session_state.chat_manager.add_message_feedback(message_id, feedback_type)
        
        if success:
            # Update session state
            st.session_state.message_feedback[message_id] = feedback_type
            logger.info(f"Feedback recorded: message {message_id} -> {feedback_type}")
            
            # Display a subtle message
            feedback_msg = f"{'👍' if feedback_type == 'like' else '👎'} Feedback recorded"
            placeholder = st.empty()
            placeholder.markdown(f"<p style='color: gray;'>{feedback_msg}</p>", unsafe_allow_html=True)
            
            time.sleep(0.5)
            st.rerun()
        else:
            logger.error(f"Failed to record feedback for message {message_id}")
            st.error("Failed to record feedback")
    except Exception as e:
        logger.error(f"Error handling feedback for message {message_id}: {str(e)}")
        st.error("Failed to record feedback")

def display_message_feedback(message_id, has_existing_feedback, existing_feedback_type):
    """Display feedback buttons or status for a message"""
    # Check session state for feedback
    feedback_in_session = st.session_state.message_feedback.get(message_id)
    
    if feedback_in_session:
        # Show existing feedback from session state
        feedback_text = "👍 Liked" if feedback_in_session == 'like' else "👎 Disliked"
        st.caption(f"Feedback: {feedback_text}")
    elif has_existing_feedback:
        # Show existing feedback from database
        feedback_text = "👍 Liked" if existing_feedback_type == 'like' else "👎 Disliked"
        st.caption(f"Feedback: {feedback_text}")
        # Also update session state
        st.session_state.message_feedback[message_id] = existing_feedback_type
    else:
        # Show feedback buttons
        col1, col2, col3 = st.columns([1, 1, 8])
        
        with col1:
            if st.button("👍", key=f"like_msg_{message_id}"):
                handle_feedback(message_id, 'like')
                
        with col2:
            if st.button("👎", key=f"dislike_msg_{message_id}"):
                handle_feedback(message_id, 'dislike')

def display_message_sources(message_id):
    """Display sources for a message in an expander"""
    try:
        sources = st.session_state.chat_manager.get_message_sources(message_id)
        if not sources:
            return
        
        web_sources = [s for s in sources if s['type'] == 'web']
        rag_sources = [s for s in sources if s['type'] == 'rag']
        
        logger.debug(f"Displaying {len(web_sources)} web sources and {len(rag_sources)} RAG sources")
        
        # Display web sources
        if web_sources:
            st.write("**Web Sources:**")
            for source in web_sources:
                st.write(f"**{source['title']}**")
                if source.get('source'):
                    st.write(f"**URL:** {source['source']}")
                metadata = source.get('metadata', {})
                if metadata.get('date'):
                    st.write(f"**Date:** {metadata['date']}")
                if metadata.get('source'):
                    st.write(f"**Source:** {metadata['source']}")
                st.write("")
        
        # Display RAG sources as bullet points
        if rag_sources:
            if web_sources:
                st.divider()
            st.write("**Knowledge Base:**")
            for source in rag_sources:
                st.write(f"• {source.get('text', 'No content available')}")
                st.write("")
    except Exception as e:
        logger.error(f"Failed to display sources for message {message_id}: {str(e)}")
        st.error("Failed to load sources")

def display_messages():
    """Display all conversation messages"""
    messages = []
    if st.session_state.get('current_conversation'):
        try:
            messages = st.session_state.chat_manager.get_conversation_messages(
                st.session_state.current_conversation
            )
            logger.debug(f"Displaying {len(messages)} messages for conversation {st.session_state.current_conversation}")
        except Exception as e:
            logger.error(f"Failed to load messages: {str(e)}")
            st.error("Failed to load conversation messages")
            return
    
    for msg in messages:
        if msg['role'] == 'user':
            with st.chat_message(msg['role'], avatar="app/static/user.png"):
                st.markdown(f'<div class="user-message">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            with st.chat_message(msg['role'], avatar="app/static/bot_logo.png"):
                st.markdown(f'<div class="assistant-message">{msg["content"]}</div>', unsafe_allow_html=True)
                
                # Display feedback buttons/status
                has_feedback = msg.get('feedback') is not None
                display_message_feedback(msg['id'], has_feedback, msg.get('feedback'))
                
                #method details if available
                if msg.get('method_used'):
                    with st.expander("Response Details & Sources"):
                        st.markdown("### Performance Metrics")
                        
                        col1, col2, col3 = st.columns([1, 1, 1])
                        
                        with col1:
                            method_display = msg['method_used'].upper()
                            st.markdown(f"**Method**  \n{method_display}")
                        
                        with col2:
                            rag_score = msg.get('rag_score')
                            if rag_score is not None:
                                try:
                                    rag_score = float(rag_score)
                                    st.markdown(f"**RAG Score**  \n{rag_score:.2f}")
                                except (ValueError, TypeError):
                                    st.markdown(f"**RAG Score**  \nN/A")
                            else:
                                st.markdown(f"**RAG Score**  \nN/A")
                        
                        with col3:
                            web_score = msg.get('web_score')
                            if web_score is not None:
                                try:
                                    web_score = float(web_score)
                                    st.markdown(f"**Web Score**  \n{web_score:.2f}")
                                except (ValueError, TypeError):
                                    st.markdown(f"**Web Score**  \nN/A")
                            else:
                                st.markdown(f"**Web Score**  \nN/A")
                        
                        st.markdown("---")

                        display_message_sources(msg['id'])

def chat_page():
    """Main chat page"""
    has_conversation = st.session_state.get('current_conversation') is not None
    
    if not has_conversation and not st.session_state.first_message_sent:
        st.markdown('<div class="main-heading">Hi, what can AI Insight help you with today?</div>', unsafe_allow_html=True)
    else:
        #conversation title if we have one
        if has_conversation:
            try:
                conversations = st.session_state.chat_manager.get_user_conversations(st.session_state.user_id)
                current_conv = next((conv for conv in conversations if conv['id'] == st.session_state.current_conversation), None)
                if current_conv:
                    st.markdown(f"### {current_conv['title']}")
            except Exception as e:
                logger.error(f"Failed to load conversation title: {str(e)}")
        
        display_messages()
    
    if prompt := st.chat_input("Chat with AI Insight"):
        logger.info(f"User prompt received: {prompt[:100]}...")
        
        # Set flag that first message was sent
        st.session_state.first_message_sent = True
        
        # Reset streaming thoughts for new message
        st.session_state.streaming_thoughts = []
        st.session_state.last_thought_count = 0
        
        # Display user message immediately
        with st.chat_message("user", avatar="app/static/user.png"):
            st.markdown(f'<div class="user-message">{prompt}</div>', unsafe_allow_html=True)
        
        # Display assistant response with streaming
        with st.chat_message("assistant", avatar="app/static/bot_logo.png"):
            # Create placeholder for answer
            answer_placeholder = st.empty()
            
            # Define streaming callback function
            def streaming_callback(update_type, content):
                if update_type == "thought":
                    # Add new thought to session state
                    st.session_state.streaming_thoughts.append(content)
                    
                    # Show the current thought in the answer area
                    answer_placeholder.markdown(f'<div class="thought-item">{content}</div>', unsafe_allow_html=True)
                
                elif update_type == "answer":
                    # Final answer - update with the complete response
                    answer_placeholder.markdown(f"<div class='assistant-message'>{content}</div>", unsafe_allow_html=True)
            
            try:
                # Call chat manager with streaming callback
                result = st.session_state.chat_manager.chat(
                    st.session_state.user_id, 
                    prompt, 
                    st.session_state.get('current_conversation'),
                    streaming_callback=streaming_callback
                )
                
                # Update conversation ID
                st.session_state.current_conversation = result['conversation_id']
                
                # Ensure final answer is displayed
                final_answer = result['response']['answer']
                answer_placeholder.markdown(f"<div class='assistant-message'>{final_answer}</div>", unsafe_allow_html=True)
                
                # Display feedback buttons for new message
                msg_id = result['message_id']
                display_message_feedback(msg_id, False, None)
                
                logger.info(f"Chat completed successfully: conversation {result['conversation_id']}, message {msg_id}")
                
                # Show details in a single, well-organized expander
                with st.expander("Response Details & Sources", expanded=False):
                    response = result['response']
                    
                    st.markdown("### Performance Metrics")
                    
                    col1, col2, col3 = st.columns([1, 1, 1])
                    
                    with col1:
                        method_display = response['method'].upper()
                        st.markdown(f"**Method**  \n{method_display}")
                    
                    with col2:
                        rag_score = response.get('rag_score', 0.0)
                        if rag_score is not None:
                            rag_score = float(rag_score)
                            st.markdown(f"**RAG Score**  \n{rag_score:.2f}")
                        else:
                            st.markdown(f"**RAG Score**  \nN/A")
                    
                    with col3:
                        web_score = response.get('web_score', 0.0)
                        if web_score is not None:
                            web_score = float(web_score)
                            st.markdown(f"**Web Score**  \n{web_score:.2f}")
                        else:
                            st.markdown(f"**Web Score**  \nN/A")
                    
                    st.markdown("---")
                    
                    # Sources section
                    if response.get('rag_chunks') or response.get('web_results'):
                        st.markdown("### Sources")
                        
                        # Web sources
                        if response['method'] == 'web' and response.get('web_results'):
                            st.markdown("**Web Sources:**")
                            for i, web_result in enumerate(response.get('web_results', []), 1):
                                with st.container():
                                    st.markdown(f"**{i}. {web_result.get('title', 'Web Result')}**")
                                    if web_result.get('url'):
                                        st.markdown(f"[{web_result.get('url', '')}]({web_result.get('url', '')})")
                                    
                                    # Create metadata line
                                    metadata_parts = []
                                    if web_result.get('date'):
                                        metadata_parts.append(f"Date: {web_result.get('date', 'Unknown')}")
                                    if web_result.get('source'):
                                        metadata_parts.append(f"Source: {web_result.get('source', 'Unknown')}")
                                    
                                    if metadata_parts:
                                        st.markdown(f"*{' • '.join(metadata_parts)}*")
                                    
                                    if i < len(response.get('web_results', [])):
                                        st.markdown("") 
                        
                        # RAG sources
                        elif response['method'] == 'rag' and response.get('rag_chunks'):
                            st.markdown("**Knowledge Base:**")
                            for i, chunk in enumerate(response.get('rag_chunks', []), 1):
                                st.markdown(f"**{i}.** {chunk.get('text', '')}")
                                if i < len(response.get('rag_chunks', [])):
                                    st.markdown("")
                    else:
                        st.markdown("### Sources")
                        st.markdown("*No sources available for this response*")
                
                st.rerun()
                
            except Exception as e:
                logger.error(f"Error during chat processing: {str(e)}")
                answer_placeholder.error("Sorry, there was an error processing your request. Please try again.")

def main():
    """Main application entry point"""
    logger.info("Streamlit app started")
    add_custom_css()
    
    if not st.session_state.user_id:
        login_page()
    else:
        sidebar()
        chat_page()

if __name__ == "__main__":
    main()