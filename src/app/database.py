
import sqlite3
from typing import Dict, List
import json

class SQLiteChatDB:
    def __init__(self, db_path: str = "chat.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Create tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    title TEXT DEFAULT 'New Chat',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY,
                    conversation_id INTEGER,
                    role TEXT CHECK (role IN ('user', 'assistant')),
                    content TEXT,
                    method_used TEXT,
                    rag_score REAL,
                    web_score REAL,
                    feedback TEXT CHECK (feedback IN ('like', 'dislike', NULL)),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (conversation_id) REFERENCES conversations (id)
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS message_sources (
                    id INTEGER PRIMARY KEY,
                    message_id INTEGER,
                    type TEXT CHECK (type IN ('rag', 'web')),
                    source TEXT,
                    title TEXT,
                    text TEXT,
                    score REAL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (message_id) REFERENCES messages (id)
                )
            ''')
            conn.commit()
    
    def get_or_create_user(self, email: str) -> int:
        """Get user ID or create new user."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT id FROM users WHERE email = ?", (email,))
            result = cursor.fetchone()
            
            if result:
                return result[0]
            
            cursor = conn.execute("INSERT INTO users (email) VALUES (?) RETURNING id", (email,))
            return cursor.fetchone()[0]
    
    def create_conversation(self, user_id: int, title: str = "New Chat") -> int:
        """Create new conversation."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO conversations (user_id, title) VALUES (?, ?) RETURNING id",
                (user_id, title)
            )
            return cursor.fetchone()[0]
    
    def add_message(self, conversation_id: int, role: str, content: str, 
                   method_used: str = None, rag_score: float = None, 
                   web_score: float = None) -> int:
        """Add message to conversation and return message ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                INSERT INTO messages (conversation_id, role, content, method_used, rag_score, web_score)
                VALUES (?, ?, ?, ?, ?, ?) RETURNING id
            ''', (conversation_id, role, content, method_used, rag_score, web_score))
            
            message_id = cursor.fetchone()[0]
            
            conn.execute(
                "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (conversation_id,)
            )
            conn.commit()
            
            return message_id
    
    def add_message_source(self, message_id: int, source_type: str, source: str, 
                          title: str, text: str, score: float, metadata: dict = None):
        """Add a source for a message."""

        if metadata is None:
            metadata = {}
        metadata_json = json.dumps(metadata)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO message_sources
                (message_id, type, source, title, text, score, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (message_id, source_type, source, title, text, score, metadata_json))
            conn.commit()
    
    def update_message_feedback(self, message_id: int, feedback: str):
        """Update feedback (like/dislike) for a message."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE messages SET feedback = ? WHERE id = ?",
                (feedback, message_id)
            )
            conn.commit()
    
    def get_user_conversations(self, user_id: int) -> List[Dict]:
        """Get all conversations for user."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT c.id, c.title, c.created_at, c.updated_at, COUNT(m.id) as message_count
                FROM conversations c
                LEFT JOIN messages m ON c.id = m.conversation_id
                WHERE c.user_id = ?
                GROUP BY c.id
                ORDER BY c.updated_at DESC
            ''', (user_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_conversation_messages(self, conversation_id: int) -> List[Dict]:
        """Get all messages in conversation."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT id, role, content, method_used, rag_score, web_score, feedback, created_at
                FROM messages
                WHERE conversation_id = ?
                ORDER BY created_at ASC
            ''', (conversation_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_message_sources(self, message_id: int) -> List[Dict]:
        """Get all sources for a message with parsed metadata."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT id, type, source, title, text, score, metadata
                FROM message_sources
                WHERE message_id = ?
                ORDER BY score DESC
            ''', (message_id,))
            
            sources = []
            for row in cursor.fetchall():
                source_dict = dict(row)
                
                # Parse metadata JSON string back to dict
                if source_dict['metadata']:
                    try:
                        source_dict['metadata'] = json.loads(source_dict['metadata'])
                    except json.JSONDecodeError:
                        # If parsing fails, set to empty dict
                        source_dict['metadata'] = {}
                else:
                    source_dict['metadata'] = {}
                
                sources.append(source_dict)
            
            return sources
    
    def delete_conversation(self, conversation_id: int):
        """Delete conversation and its messages."""
        with sqlite3.connect(self.db_path) as conn:
            # Get all message IDs first to delete their sources
            cursor = conn.execute("SELECT id FROM messages WHERE conversation_id = ?", (conversation_id,))
            message_ids = [row[0] for row in cursor.fetchall()]
            
            # Delete sources for each message
            for message_id in message_ids:
                conn.execute("DELETE FROM message_sources WHERE message_id = ?", (message_id,))
            
            # Delete messages
            conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
            
            # Delete conversation
            conn.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
            conn.commit()