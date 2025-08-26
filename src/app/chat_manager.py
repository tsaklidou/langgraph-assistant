import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.database import SQLiteChatDB
from agent.agent import LangGraphAgent
from loguru import logger

class ChatManager:
    def __init__(self):
        try:
            self.db = SQLiteChatDB()
            logger.info("Database connection initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            raise
            
        self.current_thoughts = []
        self.streaming_callback = None
        
        try:
            self.agent = LangGraphAgent(on_thought=self._capture_thought)
            logger.info("ChatManager initialized with LangGraphAgent")
        except Exception as e:
            logger.error(f"Failed to initialize LangGraphAgent: {str(e)}")
            raise
    
    def _capture_thought(self, thought: str):
        """Capture agent's thoughts and stream them if callback is available."""
        logger.debug(f"Agent thought: {thought}")
        self.current_thoughts.append(thought)
        
        # Streaming callback
        if self.streaming_callback:
            try:
                self.streaming_callback("thought", thought)
            except Exception as e:
                logger.error(f"Error in streaming callback: {str(e)}")
    
    def login_user(self, email: str) -> int:
        """Simple login - just get/create user."""
        try:
            user_id = self.db.get_or_create_user(email)
            logger.info(f"User logged in: {email} (ID: {user_id})")
            return user_id
        except Exception as e:
            logger.error(f"Failed to login user {email}: {str(e)}")
            raise
    
    def get_user_conversations(self, user_id: int):
        """Get all conversations for user."""
        try:
            conversations = self.db.get_user_conversations(user_id)
            logger.debug(f"Retrieved {len(conversations)} conversations for user {user_id}")
            return conversations
        except Exception as e:
            logger.error(f"Failed to get conversations for user {user_id}: {str(e)}")
            return []
    
    def get_conversation_messages(self, conversation_id: int):
        """Get messages in conversation."""
        try:
            messages = self.db.get_conversation_messages(conversation_id)
            logger.debug(f"Retrieved {len(messages)} messages for conversation {conversation_id}")
            return messages
        except Exception as e:
            logger.error(f"Failed to get messages for conversation {conversation_id}: {str(e)}")
            return []
    
    def get_message_sources(self, message_id: int):
        """Get sources for a message."""
        try:
            sources = self.db.get_message_sources(message_id)
            logger.debug(f"Retrieved {len(sources)} sources for message {message_id}")
            return sources
        except Exception as e:
            logger.error(f"Failed to get sources for message {message_id}: {str(e)}")
            return []
    
    def add_message_feedback(self, message_id: int, feedback: str):
        """Add user feedback (like/dislike) to a message."""
        try:
            self.db.update_message_feedback(message_id, feedback)
            logger.info(f"Saved {feedback} feedback for message ID {message_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving feedback for message {message_id}: {str(e)}")
            return False
    
    def chat(self, user_id: int, message: str, conversation_id: int = None, streaming_callback=None):
        """Handle a chat message with history context."""
        logger.info(f"Starting chat for user {user_id}: {message[:100]}...")
        
        # Set streaming callback
        self.streaming_callback = streaming_callback
        
        # Clear previous thoughts at the start of each chat
        self.current_thoughts = []
        logger.debug("Cleared thoughts array for new chat")
        
        try:
            # Create new conversation if needed
            if not conversation_id:
                title = self._generate_smart_title(message)
                conversation_id = self.db.create_conversation(user_id, title)
                logger.info(f"Created new conversation {conversation_id} with title: {title}")
            
            # Save user message
            self.db.add_message(conversation_id, 'user', message)
            logger.debug("Saved user message to database")
            
            # Get conversation history
            history = []
            if conversation_id:
                messages = self.db.get_conversation_messages(conversation_id)
                # Exclude the message we just added
                history = messages[:-1] if messages else []
                logger.debug(f"Retrieved {len(history)} previous messages for context")
            
            # Get agent response
            logger.debug("Calling agent.answer()...")
            response = self.agent.answer(message, history)
            logger.info(f"Agent responded using {response['method']} method with {len(self.current_thoughts)} thoughts")
            
            # Save assistant response
            message_id = self.db.add_message(
                conversation_id, 
                'assistant', 
                response['answer'],
                response['method'],
                response.get('rag_score'),
                response.get('web_score')
            )
            logger.debug(f"Saved assistant message with ID {message_id}")
            
            # Save sources
            sources_saved = 0
            if response['method'] == 'rag' and response.get('rag_chunks'):
                for chunk in response.get('rag_chunks', []):
                    self.db.add_message_source(
                        message_id=message_id,
                        source_type='rag',
                        source=chunk.get('source', 'Knowledge Base'),
                        title=chunk.get('title', 'Document Chunk'),
                        text=chunk.get('text', ''),
                        score=chunk.get('score', 0.0),
                        metadata=chunk.get('metadata', {})
                    )
                    sources_saved += 1
                logger.debug(f"Saved {sources_saved} RAG sources")
            
            elif response['method'] == 'web' and response.get('web_results'):
                for result in response.get('web_results', []):
                    self.db.add_message_source(
                        message_id=message_id,
                        source_type='web',
                        source=result.get('url', ''),
                        title=result.get('title', ''),
                        text=result.get('content', ''),
                        score=result.get('score', 0.0),
                        metadata={
                            'date': result.get('date', ''),
                            'source': result.get('source', '')
                        }
                    )
                    sources_saved += 1
                logger.debug(f"Saved {sources_saved} web sources")
            
            # Stream the answer
            if self.streaming_callback:
                try:
                    self.streaming_callback("answer", response['answer'])
                except Exception as e:
                    logger.error(f"Error streaming answer: {str(e)}")
            
            # Clear the callback
            self.streaming_callback = None
            
            # Prepare result
            result = {
                'conversation_id': conversation_id,
                'message_id': message_id,
                'response': response,
                'thoughts': self.current_thoughts.copy()
            }
            
            logger.info(f"Chat completed successfully for conversation {conversation_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error in chat processing: {str(e)}")
            # Clear the callback on error
            self.streaming_callback = None
            raise
    
    def delete_conversation(self, conversation_id: int):
        """Delete a conversation."""
        try:
            self.db.delete_conversation(conversation_id)
            logger.info(f"Deleted conversation {conversation_id}")
        except Exception as e:
            logger.error(f"Failed to delete conversation {conversation_id}: {str(e)}")
            raise
    
    def _generate_smart_title(self, message: str) -> str:
        """Generate a smart title based on the query content."""
        try:
            # Remove common question words and punctuation
            message_lower = message.lower().strip()
            
            # Remove question marks and periods
            message_clean = message.replace('?', '').replace('.', '').replace('!', '')
            
            # Common question starters to potentially remove
            question_starters = [
                'what is', 'what are', 'how to', 'how do', 'how does', 
                'can you', 'could you', 'please', 'tell me about', 'tell me',
                'give me', 'find me', 'search for', 'look up', 'search',
                'explain', 'describe', 'show me', 'help me', 'i need',
                'where is', 'where are', 'when is', 'when are',
                'why is', 'why are', 'who is', 'who are'
            ]
            
            # Check if message starts with common question words
            for starter in question_starters:
                if message_lower.startswith(starter):
                    # Remove the starter and capitalize properly
                    core_message = message_clean[len(starter):].strip()
                    if core_message:
                        # Take first 4-6 words of the core message
                        words = core_message.split()[:5]
                        title = " ".join(words)
                        if len(core_message.split()) > 5:
                            title += "..."
                        logger.debug(f"Generated smart title: {title}")
                        return title.title()
            
            # If no common starter found, use the original approach but smarter
            words = message_clean.split()
            
            if len(words) > 3:
                # Skip first word if it's a common question word
                skip_words = ['what', 'how', 'can', 'could', 'please', 'why', 'when', 'where', 'who']
                if words[0].lower() in skip_words and len(words) > 4:
                    words = words[1:]
            
            # Take up to 5 words for the title
            title_words = words[:5]
            title = " ".join(title_words)
            
            # Add ellipsis if we truncated
            if len(words) > 5:
                title += "..."
                
            # Capitalize properly
            result_title = title.title()
            logger.debug(f"Generated fallback title: {result_title}")
            return result_title
            
        except Exception as e:
            logger.error(f"Error generating smart title: {str(e)}")
            return self._generate_title(message)
    
    def _generate_title(self, message: str) -> str:
        """Generate simple title from first message (fallback method)."""
        try:
            words = message.split()[:5]
            title = " ".join(words)
            if len(message.split()) > 5:
                title += "..."
            result = title.title()
            logger.debug(f"Generated simple title: {result}")
            return result
        except Exception as e:
            logger.error(f"Error generating simple title: {str(e)}")
            return "New Conversation"