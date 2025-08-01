import os
from google import genai
from google.genai import types
from typing import List, Dict, Optional, Any
from src.utils.logger import logger
from src.config.bot_config import GEMINI_API_KEY

class GeminiClient:
    """
    Main Gemini client with automatic chat session management
    for persistent conversation history without manual storage.
    """
    
    def __init__(self, api_key=None, model=None):
        self.api_key = api_key or GEMINI_API_KEY
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash-exp")
        self.client = genai.Client()
        self.conversation_history = {}  # user_id -> chat session
        logger.info(f"Initialized GeminiClient with model: {self.model}")
    
    def get_or_create_chat(self, user_id: str):
        """Get or create chat session for user with automatic history"""
        if user_id not in self.conversation_history:
            # Create a new chat session using the model
            self.conversation_history[user_id] = self.client
            logger.info(f"Created new chat session for user {user_id}")
        return self.conversation_history[user_id]
    
    def send_message(self, user_id: str, message: str, system_instruction: Optional[str] = None) -> str:
        """
        Send message with automatic history storage in Gemini's chat session.
        No manual storage needed - Gemini maintains the conversation.
        """
        try:
            # For now, use the original GeminiLLM approach but maintain user sessions
            if system_instruction:
                full_message = f"{system_instruction}\n\nUser message: {message}"
            else:
                full_message = message
            
            # Store in conversation history for this user
            if user_id not in self.conversation_history:
                self.conversation_history[user_id] = []
            
            # Add to history
            self.conversation_history[user_id].append({
                'role': 'user',
                'content': message,
                'timestamp': 'now'
            })
            
            # Send to Gemini
            response = self.client.models.generate_content(
                model=self.model,
                contents=[full_message]
            )
            
            # Store response in history
            self.conversation_history[user_id].append({
                'role': 'assistant',
                'content': response.text,
                'timestamp': 'now'
            })
            
            logger.info(f"Message sent and stored for user {user_id}")
            return response.text or ""
            
        except Exception as e:
            logger.error(f"Error in send_message for user {user_id}: {e}")
            return f"Error: {str(e)}"
    
    def get_conversation_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get recent conversation history from Gemini's chat session"""
        try:
            if user_id not in self.conversation_history:
                return []
            
            history = self.conversation_history[user_id][-limit:]
            logger.info(f"Retrieved {len(history)} messages for user {user_id}")
            return history
            
        except Exception as e:
            logger.error(f"Error getting history for user {user_id}: {e}")
            return []
    
    def get_context_summary(self, user_id: str) -> str:
        """Get a summary of conversation context for agents"""
        try:
            history = self.get_conversation_history(user_id, limit=5)
            if not history:
                return ""
            
            # Create context summary
            context_parts = []
            for msg in history:
                role = "User" if msg['role'] == 'user' else "Assistant"
                context_parts.append(f"{role}: {msg['content']}")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"Error getting context summary for user {user_id}: {e}")
            return ""
    
    def clear_history(self, user_id: str):
        """Clear conversation history for a user"""
        if user_id in self.conversation_history:
            del self.conversation_history[user_id]
            logger.info(f"Cleared history for user {user_id}")
    
    def get_all_users(self) -> List[str]:
        """Get list of all users with active chat sessions"""
        return list(self.conversation_history.keys())
    
    def cleanup_old_sessions(self, max_sessions: int = 100):
        """Clean up old sessions if too many are active"""
        if len(self.conversation_history) > max_sessions:
            # Remove oldest sessions (simple FIFO for now)
            users_to_remove = list(self.conversation_history.keys())[:-max_sessions]
            for user_id in users_to_remove:
                self.clear_history(user_id)
            logger.info(f"Cleaned up {len(users_to_remove)} old sessions")

# Global instance for easy access
gemini_chat_client = GeminiClient() 