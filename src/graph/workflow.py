from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from typing import Dict, Any
from src.graph.state import AgentState
from src.agents.intent_agent import IntentDetectionAgent
from src.tools.graph_tools import GraphQueryTool, AddProductTool, LogTransactionTool, BusinessAnalyticsTool
from src.utils.logger import logger

class BusinessWorkflow:
    """
    Main LangGraph workflow for business tracking bot.
    Uses Gemini's chat sessions for automatic memory management.
    """
    
    def __init__(self):
        self.intent_agent = IntentDetectionAgent()
        self.graph_tool = GraphQueryTool()
        self.add_product_tool = AddProductTool()
        self.log_transaction_tool = LogTransactionTool()
        self.analytics_tool = BusinessAnalyticsTool()
        
    def create_workflow(self):
        """Create the optimized workflow graph with unified processing"""
        workflow = StateGraph(AgentState)
        
        # Add nodes - simplified workflow with unified processing
        workflow.add_node("unified_processing", self.unified_processing_node)
        workflow.add_node("fallback_processing", self.fallback_processing_node)
        
        # Define edges - much simpler flow
        workflow.add_edge(START, "unified_processing")
        
        # Add conditional edge for fallback if needed
        workflow.add_conditional_edges(
            "unified_processing",
            self.check_processing_result,
            {
                "complete": END,
                "fallback": "fallback_processing"
            }
        )
        
        workflow.add_edge("fallback_processing", END)
        
        return workflow.compile()
    
    def unified_processing_node(self, state: AgentState) -> AgentState:
        """
        Unified processing node that handles intent detection and action execution in one step.
        This replaces the multi-step workflow with a single optimized LLM call.
        """
        logger.info(f"Processing unified request for user {state.user_id}")
        return self.intent_agent.detect_intent_and_execute(state)
    
    def check_processing_result(self, state: AgentState) -> str:
        """Check if unified processing was successful or needs fallback"""
        if state.response and not state.error:
            return "complete"
        else:
            logger.warning(f"Unified processing incomplete for user {state.user_id}, using fallback")
            return "fallback"
    
    def fallback_processing_node(self, state: AgentState) -> AgentState:
        """Fallback to original workflow if unified processing fails"""
        try:
            logger.info(f"Using fallback processing for user {state.user_id}")
            
            # Use the original intent detection if unified failed
            state = self.intent_agent.detect_intent(state)
            
            # Route to appropriate tool based on intent
            intent = state.intent
            if intent == "graph_query":
                state = self.graph_operation_node(state)
                state = self.format_response_node(state)
            elif intent == "add_product":
                state = self.add_product_operation_node(state)
                state = self.format_response_node(state)
            elif intent == "log_transaction":
                state = self.log_transaction_operation_node(state)
                state = self.format_response_node(state)
            elif intent in ["analytics", "report"]:
                state = self.analytics_operation_node(state)
                state = self.format_response_node(state)
            else:
                state = self.chat_response_node(state)
            
            return state
            
        except Exception as e:
            logger.error(f"Error in fallback processing for user {state.user_id}: {e}")
            state.set_error(f"Fallback processing error: {str(e)}")
            state.update_response("I'm sorry, there was an error processing your request. Please try again.")
            return state
    
    def intent_detection_node(self, state: AgentState) -> AgentState:
        """Intent detection node"""
        logger.info(f"Processing intent detection for user {state.user_id}")
        return self.intent_agent.detect_intent(state)
    
    def graph_operation_node(self, state: AgentState) -> AgentState:
        """Graph query operation node"""
        try:
            logger.info(f"Executing graph operation for user {state.user_id}")
            
            # Use the graph query tool
            result = self.graph_tool._run(
                query=state.message,
                user_id=state.user_id
            )
            
            state.add_tool_used("graph_query")
            # Store raw result for formatting
            state.extracted_data = {"raw_result": result, "operation_type": "graph_query"}
            
            return state
            
        except Exception as e:
            logger.error(f"Error in graph operation: {e}")
            state.set_error(f"Graph operation error: {str(e)}")
            return state
    
    def add_product_operation_node(self, state: AgentState) -> AgentState:
        """Add product operation node"""
        try:
            logger.info(f"Executing add product operation for user {state.user_id}")
            
            entities = state.entities or {}
            product_name = entities.get('product', 'Unknown Product')
            price = entities.get('amount', 0)
            description = entities.get('description')
            
            result = self.add_product_tool._run(
                name=product_name,
                price=float(price),
                description=description or ""
            )
            
            state.add_tool_used("add_product")
            # Store raw result for formatting
            state.extracted_data = {"raw_result": result, "operation_type": "add_product"}
            
            return state
            
        except Exception as e:
            logger.error(f"Error in add product operation: {e}")
            state.set_error(f"Add product error: {str(e)}")
            return state
    
    def log_transaction_operation_node(self, state: AgentState) -> AgentState:
        """Log transaction operation node"""
        try:
            logger.info(f"Executing log transaction operation for user {state.user_id}")
            
            entities = state.entities or {}
            transaction_type = entities.get('transaction_type', 'purchase')
            amount = entities.get('amount', 0)
            product = entities.get('product', 'Unknown Product')
            vendor = entities.get('vendor')
            customer = entities.get('customer')
            
            result = self.log_transaction_tool._run(
                transaction_type=transaction_type,
                amount=float(amount),
                product=product,
                vendor=vendor or "",
                customer=customer or ""
            )
            
            state.add_tool_used("log_transaction")
            # Store raw result for formatting
            state.extracted_data = {"raw_result": result, "operation_type": "log_transaction"}
            
            return state
            
        except Exception as e:
            logger.error(f"Error in log transaction operation: {e}")
            state.set_error(f"Log transaction error: {str(e)}")
            return state
    
    def analytics_operation_node(self, state: AgentState) -> AgentState:
        """Analytics operation node"""
        try:
            logger.info(f"Executing analytics operation for user {state.user_id}")
            
            # Determine analysis type from message
            message_lower = state.message.lower()
            if 'sales' in message_lower or 'revenue' in message_lower:
                analysis_type = "total_sales"
            elif 'product' in message_lower and 'performance' in message_lower:
                analysis_type = "product_performance"
            elif 'vendor' in message_lower:
                analysis_type = "vendor_summary"
            else:
                analysis_type = "general"
            
            result = self.analytics_tool._run(
                analysis_type=analysis_type,
                user_id=state.user_id
            )
            
            state.add_tool_used("business_analytics")
            # Store raw result for formatting
            state.extracted_data = {"raw_result": result, "operation_type": "analytics"}
            
            return state
            
        except Exception as e:
            logger.error(f"Error in analytics operation: {e}")
            state.set_error(f"Analytics error: {str(e)}")
            return state
    
    def format_response_node(self, state: AgentState) -> AgentState:
        """Format raw results into user-friendly responses using LLM"""
        try:
            logger.info(f"Formatting response for user {state.user_id}")
            
            if not state.extracted_data or 'raw_result' not in state.extracted_data:
                return state
            
            raw_result = state.extracted_data['raw_result']
            operation_type = state.extracted_data.get('operation_type', 'unknown')
            
            # Create formatting prompt based on operation type
            if operation_type == "graph_query":
                formatting_prompt = f"""
                Format this database query result into a user-friendly Telegram message.
                Use proper formatting with bold text, bullet points, and clear structure.
                
                Original user query: {state.message}
                Database result: {raw_result}
                
                Format the response using Telegram MarkdownV2 formatting:
                - Use **bold** for headers and important information
                - Use bullet points (•) for lists
                - Make it conversational and helpful
                - If it's a list of products, format as a nice table or list
                - If the list has Amount, then use the currency symbol of INR for the currency.
                - If empty result, explain that no data was found
                
                Return only the formatted message, no additional text.
                """
            elif operation_type == "add_product":
                formatting_prompt = f"""
                Format this product addition result into a user-friendly confirmation message.
                
                Result: {raw_result}
                
                Create a friendly confirmation message using Telegram formatting.
                Use **bold** for the product name and price.
                Make it sound like a helpful assistant confirming the action.
                """
            elif operation_type == "log_transaction":
                formatting_prompt = f"""
                Format this transaction logging result into a user-friendly confirmation message.
                
                Result: {raw_result}
                
                Create a friendly confirmation message using Telegram formatting.
                Use **bold** for important details like amounts and product names.
                Make it sound like a helpful assistant confirming the transaction.
                """
            else:
                formatting_prompt = f"""
                Format this business operation result into a user-friendly message.
                
                Result: {raw_result}
                
                Create a helpful, well-formatted response using Telegram MarkdownV2 formatting.
                Use **bold** for headers and important information.
                Make it conversational and informative.
                """
            
            # Send to LLM for formatting
            from src.utils.gemini_client import gemini_chat_client
            
            formatted_response = gemini_chat_client.send_message(
                user_id=state.user_id,
                message=formatting_prompt,
                system_instruction="You are a helpful formatting assistant. Format responses for Telegram using MarkdownV2 syntax."
            )
            
            # Store the formatted response
            state.update_response(formatted_response)
            
            return state
            
        except Exception as e:
            logger.error(f"Error in response formatting: {e}")
            # Fallback to raw result if formatting fails
            if state.extracted_data and 'raw_result' in state.extracted_data:
                state.update_response(str(state.extracted_data['raw_result']))
            return state
    
    def chat_response_node(self, state: AgentState) -> AgentState:
        """Generate chat response using Gemini's chat functionality"""
        try:
            logger.info(f"Generating chat response for user {state.user_id}")
            
            # If we already have a response from tools, use it
            if state.response:
                return state
            
            # Generate contextual response using Gemini
            from src.utils.gemini_client import gemini_chat_client
            
            system_prompt = """
            You are a helpful business assistant. Generate a friendly, contextual response.
            Consider the conversation history and provide helpful information.
            Use Telegram MarkdownV2 formatting for better presentation.
            The output should be very concise, within 3-4 lines max; only go beyond that if absolutely necessary.
            """
            
            response = gemini_chat_client.send_message(
                user_id=state.user_id,
                message=state.message,
                system_instruction=system_prompt
            )
            
            state.update_response(response)
            return state
            
        except Exception as e:
            logger.error(f"Error in chat response: {e}")
            state.set_error(f"Chat response error: {str(e)}")
            return state
    
    def route_to_action(self, state: AgentState) -> str:
        """Route to appropriate action based on intent"""
        intent = state.intent
        
        logger.info(f"Routing user {state.user_id} with intent: {intent}")
        
        if intent == "graph_query":
            return "graph_query"
        elif intent == "add_product":
            return "add_product"
        elif intent == "log_transaction":
            return "log_transaction"
        elif intent in ["analytics", "report"]:
            return "analytics"
        elif intent in ["chat", "qa"]:
            return "chat"
        else:
            # Default to chat for unknown intents
            return "chat" 