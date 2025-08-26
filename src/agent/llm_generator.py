import os
from openai import OpenAI
from typing import List, Dict, Any
import tiktoken
from loguru import logger

class LLMGenerator:
    """Generate final answers using OpenAI."""
    
    def __init__(self):
        try:
            self.client = OpenAI(
                api_key=os.getenv("OPENAI_API_KEY")
            )
            logger.info("OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {str(e)}")
            raise
        
        try:
            self.tokenizer = tiktoken.encoding_for_model("gpt-4o")
            logger.debug("Tokenizer initialized for GPT-4o")
        except Exception as e:
            logger.error(f"Failed to initialize tokenizer: {str(e)}")
            raise
        
        #leaving buffer for response
        self.max_context_tokens = 128000  # GPT-4o context window
        self.max_response_tokens = 4000    # Increased for better responses
        self.available_tokens = self.max_context_tokens - self.max_response_tokens
        
        # Hardcoded approximately 150 tokens for base prompt template
        self.base_prompt_tokens = 150  
        
        logger.info(f"Token limits set - Context: {self.max_context_tokens}, Response: {self.max_response_tokens}, Available: {self.available_tokens}")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken."""
        if not text:
            return 0
        return len(self.tokenizer.encode(text))
    
    def truncate_history(self, history: List[Dict[str, Any]], max_tokens: int) -> tuple[str, int]:
        """
        Truncate history to fit within token limit, keeping most recent messages.
        Returns (formatted_history_text, actual_tokens_used)
        """
        if not history:
            logger.debug("No history provided")
            return "", 0
        
        #start with most recent messages and work backwards
        recent_history = history[-10:]  #10 messages max
        formatted_messages = []
        total_tokens = 0
        
        logger.debug(f"Processing {len(recent_history)} recent messages from history")
        
        # Add messages from most recent backwards until we hit token limit
        for msg in reversed(recent_history):
            role = "User" if msg['role'] == 'user' else "Assistant"
            content_text = msg['content']
            
            # Include feedback if available for assistant messages
            feedback_note = ""
            if role == "Assistant" and msg.get('feedback'):
                feedback = "User liked this response" if msg['feedback'] == 'like' else "User disliked this response"
                feedback_note = f" [{feedback}]"
            
            message_text = f"{role}: {content_text}{feedback_note}\n"
            message_tokens = self.count_tokens(message_text)
            
            # Check if adding this message would exceed limit
            if total_tokens + message_tokens > max_tokens:
                logger.debug(f"History truncated at {len(formatted_messages)} messages due to token limit")
                break
                
            formatted_messages.append(message_text)
            total_tokens += message_tokens
        
        if formatted_messages:
            # Reverse back to chronological order
            history_text = "Previous conversation:\n" + "".join(reversed(formatted_messages)) + "\n"
            # Add the header tokens
            header_tokens = self.count_tokens("Previous conversation:\n\n")
            final_tokens = total_tokens + header_tokens
            logger.debug(f"History formatted: {len(formatted_messages)} messages, {final_tokens} tokens")
            return history_text, final_tokens
        
        logger.debug("No history messages fit within token limit")
        return "", 0
    
    def truncate_content(self, content: str, max_tokens: int) -> str:
        """
        Truncate content to fit within token limit, prioritizing the beginning.
        For web search results, keep the most relevant parts.
        """
        if not content:
            return content
            
        content_tokens = self.count_tokens(content)
        
        if content_tokens <= max_tokens:
            logger.debug(f"Content fits within limit: {content_tokens}/{max_tokens} tokens")
            return content
        
        logger.warning(f"Content too long ({content_tokens} tokens), truncating to {max_tokens}")
        
        # If content is too long, truncate it
        sentences = content.split('. ')
        
        truncated_content = ""
        current_tokens = 0
        sentences_kept = 0
        
        for sentence in sentences:
            sentence_with_period = sentence + ". " if not sentence.endswith('.') else sentence + " "
            sentence_tokens = self.count_tokens(sentence_with_period)
            
            if current_tokens + sentence_tokens > max_tokens:
                # Add truncation indicator
                truncated_content += "\n\n[Content truncated due to length...]"
                break
                
            truncated_content += sentence_with_period
            current_tokens += sentence_tokens
            sentences_kept += 1
        
        logger.debug(f"Content truncated: kept {sentences_kept}/{len(sentences)} sentences, {current_tokens} tokens")
        return truncated_content.strip()
    
    def generate_answer(self, query: str, content: str, history: List[Dict[str, Any]] = None) -> str:
        """
        Generate final answer with smart token management.
        
        Args:
            query: The current user query
            content: The information to use for answering (from RAG or web search)
            history: Previous messages in the conversation with optional feedback
            
        Returns:
            Generated answer
        """
        logger.info(f"Generating answer for query: {query[:100]}...")
        
        #query tokens
        query_tokens = self.count_tokens(f"Current Question: {query}\n")
        
        #available tokens for history and content
        remaining_tokens = self.available_tokens - self.base_prompt_tokens - query_tokens
        
        #20% for history, 80% for content (prioritize content more with larger context)
        max_history_tokens = int(remaining_tokens * 0.2)
        max_content_tokens = remaining_tokens - max_history_tokens
        
        logger.debug(f"Token allocation - Query: {query_tokens}, History: {max_history_tokens}, Content: {max_content_tokens}")
        
        #truncate history first
        history_text, actual_history_tokens = self.truncate_history(history, max_history_tokens)
        
        #recalculate available tokens for content
        final_content_tokens = remaining_tokens - actual_history_tokens
        
        #truncate content if necessary
        truncated_content = self.truncate_content(content, final_content_tokens)
        
        prompt = f"""{history_text}Current Question: {query}

Information: {truncated_content}

Provide a helpful answer to the current question based on the information above. 
Consider the conversation history and any feedback on previous responses to improve your answer.
If the user previously disliked a response, try to avoid similar issues in your current answer.
Focus on being accurate, concise, and helpful:"""
        
        final_tokens = self.count_tokens(prompt)
        content_tokens_used = self.count_tokens(truncated_content)
        logger.info(f"Final prompt - Total tokens: {final_tokens}, History: {actual_history_tokens}, Content: {content_tokens_used}")
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=self.max_response_tokens
            )
            
            answer = response.choices[0].message.content.strip()
            answer_tokens = self.count_tokens(answer)
            logger.info(f"Answer generated successfully, {answer_tokens} tokens")
            return answer
            
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            return f"Error generating answer: {str(e)}"