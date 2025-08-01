from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from langchain_core.messages import BaseMessage

@dataclass
class AgentState:
    """
    State for LangGraph workflow with automatic memory management.
    Uses Gemini's chat sessions for conversation history.
    """
    user_id: str
    message: str
    intent: Optional[str] = None
    entities: Optional[Dict] = None
    extracted_data: Optional[Dict] = None
    response: Optional[str] = None
    context: Optional[str] = None
    memory_messages: List[BaseMessage] = field(default_factory=list)
    tools_used: List[str] = field(default_factory=list)
    error: Optional[str] = None
    
    def __post_init__(self):
        """Initialize state with context from Gemini chat session"""
        if not self.context:
            from src.utils.gemini_client import gemini_chat_client
            self.context = gemini_chat_client.get_context_summary(self.user_id)
    
    def update_intent(self, intent: str):
        """Update intent and log for debugging"""
        self.intent = intent
        from src.utils.logger import logger
        logger.info(f"Intent updated for user {self.user_id}: {intent}")
    
    def update_entities(self, entities: Dict):
        """Update extracted entities"""
        self.entities = entities
        from src.utils.logger import logger
        logger.info(f"Entities updated for user {self.user_id}: {entities}")
    
    def update_response(self, response: str):
        """Update response"""
        self.response = response
    
    def add_tool_used(self, tool_name: str):
        """Track tools used in this workflow execution"""
        self.tools_used.append(tool_name)
    
    def set_error(self, error: str):
        """Set error state"""
        self.error = error
        from src.utils.logger import logger
        logger.error(f"Error for user {self.user_id}: {error}")
    
    def is_complete(self) -> bool:
        """Check if workflow is complete"""
        return self.response is not None or self.error is not None
    
    def to_dict(self) -> Dict:
        """Convert state to dictionary for logging"""
        return {
            'user_id': self.user_id,
            'intent': self.intent,
            'entities': self.entities,
            'tools_used': self.tools_used,
            'error': self.error,
            'has_response': self.response is not None
        } 