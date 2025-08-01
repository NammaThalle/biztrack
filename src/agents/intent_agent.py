import json
import re
from typing import Dict, Any
from src.utils.gemini_client import gemini_chat_client
from src.graph.state import AgentState
from src.utils.logger import logger

def extract_json(text):
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match:
        return match.group(1)
    return text

class IntentDetectionAgent:
    """
    Intent detection agent using Gemini's chat functionality for automatic memory.
    No manual message storage needed - Gemini maintains conversation history.
    """
    
    def __init__(self):
        self.llm = gemini_chat_client
    
    def detect_intent(self, state: AgentState) -> AgentState:
        """
        Detect user intent and route to appropriate action.
        Uses Gemini's chat session for context-aware intent detection.
        """
        try:
            system_prompt = """
            You are an intent detection agent for a business tracking system. 
            Analyze the user message and determine the appropriate action.
            
            Available intents:
            - graph_query: When user asks about business data, products, vendors, transactions
            - add_product: When user wants to add/create a new product
            - log_transaction: When user mentions buying, selling, or business transactions
            - chat: For general conversation, greetings, or casual chat
            - qa: When user asks business questions that need data analysis
            
            Return a JSON response with:
            {
                "intent": "one of the above intents",
                "confidence": 0.0-1.0,
                "entities": {
                    "product": "product name if mentioned",
                    "vendor": "vendor name will always be Sajan Ohol", 
                    "customer": "customer name if mentioned",
                    "amount": "amount if mentioned",
                    "transaction_type": "purchase/sale/commission if mentioned"
                },
                "action": "specific action to take"
            }
            
            Consider conversation context when determining intent.
            """
            
            # Send message with automatic history storage
            response = self.llm.send_message(
                user_id=state.user_id,
                message=state.message,
                system_instruction=system_prompt
            )
            
            # Parse JSON response
            try:
                json_str = extract_json(response)
                intent_data = json.loads(json_str)
                intent = intent_data.get('intent', 'chat')
                entities = intent_data.get('entities', {})
                action = intent_data.get('action', 'respond')
                
                # Update state
                state.update_intent(intent)
                state.update_entities(entities)
                state.extracted_data = intent_data
                
                logger.info(f"Intent detected for user {state.user_id}: {intent}")
                logger.info(f"Entities extracted: {entities}")
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse intent response as JSON: {e}")
                logger.error(f"Raw response: {response}")
                # Fallback to chat intent
                state.update_intent('chat')
                state.update_entities({})
            
            return state
            
        except Exception as e:
            logger.error(f"Error in intent detection for user {state.user_id}: {e}")
            state.set_error(f"Intent detection error: {str(e)}")
            return state
    
    def get_context_for_intent(self, user_id: str) -> str:
        """Get conversation context for intent detection"""
        return self.llm.get_context_summary(user_id) 