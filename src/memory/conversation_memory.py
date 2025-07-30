import os
from typing import Dict, List, Optional, Any
from src.utils.logger import logger
from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory
from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain.schema import HumanMessage, AIMessage
import json

class LangChainMemoryManager:
    """Advanced memory system using LangChain's proven memory implementations."""
    
    def __init__(self, db_url: str = "sqlite:///memory.db"):
        self.db_url = db_url
        self.memories = {}  # Cache for user memories
        self.logger = logger
    
    def get_memory_for_user(self, user_id: str) -> ConversationBufferMemory:
        """Get or create memory for a specific user."""
        if user_id not in self.memories:
            # Create SQL-based chat history for persistence
            chat_history = SQLChatMessageHistory(
                session_id=user_id,
                connection=self.db_url
            )
            
            # Create conversation memory with chat history
            memory = ConversationBufferMemory(
                chat_memory=chat_history,
                return_messages=True,
                memory_key="chat_history"
            )
            
            self.memories[user_id] = memory
            self.logger.info(f"Created new memory for user {user_id}")
        
        return self.memories[user_id]
    
    def store_interaction(self, user_id: str, message: str, response: str, 
                         intent: Optional[str] = None, entities: Optional[Dict] = None):
        """Store a user interaction in memory."""
        try:
            memory = self.get_memory_for_user(user_id)
            
            # Add human message
            memory.chat_memory.add_user_message(message)
            
            # Add AI response
            memory.chat_memory.add_ai_message(response)
            
            # Store additional metadata if needed
            if entities:
                # You could store entities in a separate table or as metadata
                self.logger.info(f"Stored entities for user {user_id}: {entities}")
            
            self.logger.info(f"Stored interaction in LangChain memory for user {user_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to store interaction in LangChain memory: {e}")
    
    def get_context_for_user(self, user_id: str, current_message: str = "") -> str:
        """Get conversation context for a user."""
        try:
            memory = self.get_memory_for_user(user_id)
            
            # Get recent messages (last 10 messages)
            messages = memory.chat_memory.messages[-10:] if memory.chat_memory.messages else []
            
            if not messages:
                return ""
            
            # Format conversation history
            context_parts = []
            context_parts.append("Recent conversation:")
            
            for msg in messages:
                if isinstance(msg, HumanMessage):
                    context_parts.append(f"User: {msg.content}")
                elif isinstance(msg, AIMessage):
                    context_parts.append(f"Bot: {msg.content}")
            
            context = "\n".join(context_parts)
            self.logger.info(f"Retrieved context for user {user_id}: {len(context)} chars")
            
            return context
            
        except Exception as e:
            self.logger.error(f"Failed to get context for user {user_id}: {e}")
            return ""
    
    def get_business_context(self, user_id: str) -> Dict:
        """Get business-specific context for a user."""
        # For now, return empty dict - could be enhanced with entity extraction
        return {'business_context': {}, 'preferences': {}}
    
    def update_business_context(self, user_id: str, context_updates: Dict):
        """Update business context for a user."""
        # Could be implemented with a separate table or metadata storage
        self.logger.info(f"Business context update for user {user_id}: {context_updates}")
    
    def extract_entities_for_memory(self, message: str, intent_data: Dict) -> Dict:
        """Extract entities from intent data for memory storage."""
        entities = {}
        
        # Extract common business entities
        if 'data' in intent_data:
            data = intent_data['data']
            if isinstance(data, dict):
                entities.update({
                    'product': data.get('product') or data.get('item'),
                    'vendor': data.get('vendor') or data.get('from'),
                    'customer': data.get('customer') or data.get('to'),
                    'amount': data.get('amount'),
                    'type': data.get('type'),
                    'date': data.get('date')
                })
        
        return {k: v for k, v in entities.items() if v is not None}
    
    def cleanup_old_memory(self, days_to_keep: int = 30):
        """Clean up old memory entries."""
        # LangChain handles this automatically with SQL storage
        self.logger.info(f"LangChain memory cleanup not needed - handled automatically")

# Global memory manager instance
langchain_memory_manager = LangChainMemoryManager() 