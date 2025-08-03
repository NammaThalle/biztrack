import json
import re
from typing import Dict, Any
from src.utils.gemini_client import gemini_chat_client
from src.graph.state import AgentState
from src.utils.logger import logger
from src.storage.graph_storage import Neo4jStorageAgent

def extract_json(text):
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match:
        return match.group(1)
    return text

class IntentDetectionAgent:
    """
    Unified intent detection and action execution agent using Gemini's chat functionality.
    Combines intent detection, entity extraction, and direct action execution in a single LLM call.
    """
    
    def __init__(self):
        self.llm = gemini_chat_client
        self.neo4j_agent = Neo4jStorageAgent()
    
    def detect_intent_and_execute(self, state: AgentState) -> AgentState:
        """
        Unified intent detection and action execution in a single LLM call.
        Reduces multiple API calls by combining intent detection, entity extraction, and action execution.
        """
        try:
            # Get Neo4j schema for database operations
            schema = self.neo4j_agent.schema
            
            system_prompt = f"""
            You are a unified business assistant that can detect intent and execute actions in one step.
            Analyze the user message and either execute the action directly or provide a conversational response.
            
            Available actions:
            1. GRAPH_QUERY: Query business data (products, vendors, transactions)
            2. ADD_PRODUCT: Add new products to database
            3. LOG_TRANSACTION: Log business transactions (purchase/sale/commission)
            4. CHAT: Provide conversational responses for greetings, general questions
            
            Database Schema:
            {schema}
            
            IMPORTANT Cypher Guidelines:
            - Use randomUUID() for generating IDs (NOT apoc.create.uuid())
            - Use native Neo4j functions only (no APOC plugins)
            - For transactions, use: CREATE (t:Transaction {{transaction_id: randomUUID(), ...}})
            - Always escape quotes properly in Cypher strings
            - For transaction history, ALWAYS include product, vendor, and customer relationships:
              MATCH (t:Transaction) OPTIONAL MATCH (t)-[:INVOLVES_PRODUCT]->(p:Product) OPTIONAL MATCH (t)-[:FROM_VENDOR]->(v:Vendor) OPTIONAL MATCH (t)-[:TO_CUSTOMER]->(c:Customer) RETURN t, p.name AS Product, v.name AS Vendor, c.name AS Customer
            
            For database operations, generate the appropriate Cypher query and provide a user-friendly response.
            For chat responses, provide direct conversational responses.
            
            Return a JSON response with:
            {{
                "intent": "graph_query|add_product|log_transaction|chat",
                "confidence": 0.0-1.0,
                "entities": {{
                    "product": "product name if mentioned",
                    "vendor": "vendor name (default: Sajan Ohol)", 
                    "customer": "customer name if mentioned",
                    "amount": "numeric amount if mentioned",
                    "transaction_type": "purchase/sale/commission if mentioned"
                }},
                "cypher_query": "Neo4j query for database operations (null for chat)",
                "response": "Direct user-friendly response in plain text",
                "raw_data": "Raw database result (null for chat or if no data)"
            }}
            
            For plain text formatting:
            - Use simple text without special characters
            - Use "1." or "-" for lists
            - Use "Rs" for currency
            - Keep responses clean and simple
            
            CRITICAL JSON Requirements:
            - ALWAYS return valid JSON without syntax errors
            - NEVER include random text like "enzymes" in JSON fields
            - Ensure proper comma placement and quote escaping
            - Double-check JSON structure before responding
            
            Product Name Consistency:
            - Always use exact product names from database
            - For "ortho kit" queries, search for BOTH "ortho kit" AND "ortho kits"
            - Use CONTAINS or regex matching for flexible product searches
            
            Consider conversation context when determining intent and generating responses.
            """
            
            # Single LLM call for intent detection + action execution
            response = self.llm.send_message(
                user_id=state.user_id,
                message=state.message,
                system_instruction=system_prompt
            )
            
            # Parse unified response
            try:
                json_str = extract_json(response)
                logger.info(f"LLM JSON response: {json_str}")
                unified_data = json.loads(json_str)
                
                intent = unified_data.get('intent', 'chat')
                entities = unified_data.get('entities', {})
                cypher_query = unified_data.get('cypher_query')
                formatted_response = unified_data.get('response', '')
                raw_data = unified_data.get('raw_data')
                
                logger.info(f"Parsed - Intent: {intent}, Cypher: {cypher_query}, Response: {formatted_response[:100]}...")
                
                # Normalize intent to lowercase for consistency
                intent = intent.lower() if intent else 'chat'
                
                # Execute database operation if cypher query is provided
                if cypher_query and intent in ['graph_query', 'add_product', 'log_transaction']:
                    try:
                        logger.info(f"Executing Cypher query: {cypher_query}")
                        with self.neo4j_agent.driver.session() as session:
                            result = session.run(cypher_query)
                            records = [record.data() for record in result]
                            raw_data = records
                            logger.info(f"Executed Cypher query, {len(records)} records returned: {records}")
                            
                            # Generate a complete response with actual data - always override LLM response with data
                            if records:
                                # Create a detailed response with the actual data
                                if intent == "graph_query":
                                    if "product" in state.message.lower():
                                        # Format products nicely
                                        product_list = []
                                        for record in records:
                                            name = record.get('ProductName') or record.get('name', 'Unknown')
                                            price = record.get('Price') or record.get('price')
                                            if price:
                                                product_list.append(f"- {name} - Rs {price}")
                                            else:
                                                product_list.append(f"- {name}")
                                        
                                        if product_list:
                                            formatted_response = "Our Products:\n\n" + "\n".join(product_list)
                                        else:
                                            formatted_response = "No products found in database."
                                    
                                    elif "transaction" in state.message.lower():
                                        # Check if this is transaction count or transaction history
                                        if any('count' in str(k).lower() or 'total' in str(k).lower() for record in records for k in record.keys()):
                                            # Format transaction count
                                            for record in records:
                                                count = record.get('totalTransactions') or record.get('total_transactions', 0)
                                                formatted_response = f"Transaction Summary:\n\nWe have {count} transaction{'s' if count != 1 else ''} recorded in the database."
                                                break
                                        else:
                                            # Format transaction history
                                            transaction_list = []
                                            for i, record in enumerate(records, 1):
                                                # Handle nested transaction object
                                                tx_data = record.get('t', record)
                                                transaction_type = tx_data.get('type', record.get('Type', 'Unknown'))
                                                amount = tx_data.get('amount', record.get('Amount', 0))
                                                product = record.get('Product', 'Unknown')
                                                vendor = record.get('Vendor', '')
                                                customer = record.get('Customer', '')
                                                date = tx_data.get('date', record.get('Date', ''))
                                                
                                                # Format date properly
                                                date_str = str(date) if date else 'Unknown date'
                                                if 'neo4j.time.Date' in str(type(date)):
                                                    date_str = f"{date.year}-{date.month:02d}-{date.day:02d}"
                                                
                                                transaction_detail = f"{i}. {transaction_type}\n"
                                                transaction_detail += f"   - Product: {product}\n"
                                                transaction_detail += f"   - Amount: Rs {amount}\n"
                                                if vendor:
                                                    transaction_detail += f"   - Vendor: {vendor}\n"
                                                if customer:
                                                    transaction_detail += f"   - Customer: {customer}\n"
                                                transaction_detail += f"   - Date: {date_str}\n"
                                                
                                                transaction_list.append(transaction_detail)
                                            
                                            if transaction_list:
                                                formatted_response = f"Transaction History:\n\n" + "\n".join(transaction_list)
                                            else:
                                                formatted_response = "No transaction history found."
                                    
                                    else:
                                        # Generic data formatting
                                        formatted_response = f"Query Results:\n\nFound {len(records)} record{'s' if len(records) != 1 else ''}.\n\n"
                                        for i, record in enumerate(records[:5]):  # Show max 5 records
                                            formatted_response += f"Record {i+1}: "
                                            items = [f"{k}: {v}" for k, v in record.items() if v is not None]
                                            formatted_response += ", ".join(items) + "\n"
                            
                            elif not formatted_response:
                                formatted_response = "No data found for your query."
                    except Exception as db_error:
                        logger.error(f"Database operation failed: {db_error}")
                        formatted_response = f"Error: Database operation failed. {str(db_error)}"
                        raw_data = None
                
                # Update state with unified results
                state.update_intent(intent)
                state.update_entities(entities)
                state.update_response(formatted_response)
                state.extracted_data = {
                    'unified_response': unified_data,
                    'raw_result': raw_data,
                    'operation_type': intent
                }
                
                logger.info(f"Unified intent + action executed for user {state.user_id}: {intent}")
                logger.info(f"Entities extracted: {entities}")
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse unified response as JSON: {e}")
                logger.error(f"Raw response: {response}")
                
                # Try to fix common JSON issues and retry
                try:
                    # Remove common malformed patterns
                    cleaned_json = json_str.replace(' enzymes,', '').replace('"purchase" enzymes,', '"purchase"')
                    # Remove trailing commas
                    cleaned_json = re.sub(r',(\s*[}\]])', r'\1', cleaned_json)
                    
                    unified_data = json.loads(cleaned_json)
                    logger.info("Successfully parsed cleaned JSON")
                    
                    intent = unified_data.get('intent', 'chat')
                    entities = unified_data.get('entities', {})
                    cypher_query = unified_data.get('cypher_query')
                    formatted_response = unified_data.get('response', '')
                    raw_data = unified_data.get('raw_data')
                    
                    logger.info(f"Cleaned - Intent: {intent}, Cypher: {cypher_query}, Response: {formatted_response[:100]}...")
                    
                    # Continue with the cleaned data - copy the processing logic
                    intent = intent.lower() if intent else 'chat'
                    
                    # Execute database operation if cypher query is provided
                    if cypher_query and intent in ['graph_query', 'add_product', 'log_transaction']:
                        try:
                            logger.info(f"Executing Cypher query: {cypher_query}")
                            with self.neo4j_agent.driver.session() as session:
                                result = session.run(cypher_query)
                                records = [record.data() for record in result]
                                raw_data = records
                                logger.info(f"Executed Cypher query, {len(records)} records returned: {records}")
                                
                                # Generate a complete response with actual data - always override LLM response with data
                                if records:
                                    # Create a detailed response with the actual data
                                    if intent == "graph_query":
                                        if "product" in state.message.lower():
                                            # Format products nicely
                                            product_list = []
                                            for record in records:
                                                name = record.get('ProductName') or record.get('name', 'Unknown')
                                                price = record.get('Price') or record.get('price')
                                                if price:
                                                    product_list.append(f"- {name} - Rs {price}")
                                                else:
                                                    product_list.append(f"- {name}")
                                            
                                            if product_list:
                                                formatted_response = "Our Products:\n\n" + "\n".join(product_list)
                                            else:
                                                formatted_response = "No products found in database."
                                        
                                        elif "transaction" in state.message.lower():
                                            # Check if this is transaction count or transaction history
                                            if any('count' in str(k).lower() or 'total' in str(k).lower() for record in records for k in record.keys()):
                                                # Format transaction count
                                                for record in records:
                                                    count = record.get('totalTransactions') or record.get('total_transactions', 0)
                                                    formatted_response = f"Transaction Summary:\n\nWe have {count} transaction{'s' if count != 1 else ''} recorded in the database."
                                                    break
                                            else:
                                                # Format transaction history
                                                transaction_list = []
                                                for i, record in enumerate(records, 1):
                                                    # Handle nested transaction object
                                                    tx_data = record.get('t', record)
                                                    transaction_type = tx_data.get('type', record.get('Type', 'Unknown'))
                                                    amount = tx_data.get('amount', record.get('Amount', 0))
                                                    product = record.get('Product', 'Unknown')
                                                    vendor = record.get('Vendor', '')
                                                    customer = record.get('Customer', '')
                                                    date = tx_data.get('date', record.get('Date', ''))
                                                    
                                                    # Format date properly
                                                    date_str = str(date) if date else 'Unknown date'
                                                    if 'neo4j.time.Date' in str(type(date)):
                                                        date_str = f"{date.year}-{date.month:02d}-{date.day:02d}"
                                                    
                                                    transaction_detail = f"{i}. {transaction_type}\n"
                                                    transaction_detail += f"   - Product: {product}\n"
                                                    transaction_detail += f"   - Amount: Rs {amount}\n"
                                                    if vendor:
                                                        transaction_detail += f"   - Vendor: {vendor}\n"
                                                    if customer:
                                                        transaction_detail += f"   - Customer: {customer}\n"
                                                    transaction_detail += f"   - Date: {date_str}\n"
                                                    
                                                    transaction_list.append(transaction_detail)
                                                
                                                if transaction_list:
                                                    formatted_response = f"Transaction History:\n\n" + "\n".join(transaction_list)
                                                else:
                                                    formatted_response = "No transaction history found."
                                        
                                        else:
                                            # Generic data formatting
                                            formatted_response = f"Query Results:\n\nFound {len(records)} record{'s' if len(records) != 1 else ''}.\n\n"
                                            for i, record in enumerate(records[:5]):  # Show max 5 records
                                                formatted_response += f"Record {i+1}: "
                                                items = [f"{k}: {v}" for k, v in record.items() if v is not None]
                                                formatted_response += ", ".join(items) + "\n"
                                
                                elif not formatted_response:
                                    formatted_response = "No data found for your query."
                        except Exception as db_error:
                            logger.error(f"Database operation failed: {db_error}")
                            formatted_response = f"Error: Database operation failed. {str(db_error)}"
                            raw_data = None
                    
                    # Update state with unified results
                    state.update_intent(intent)
                    state.update_entities(entities)
                    state.update_response(formatted_response)
                    state.extracted_data = {
                        'unified_response': unified_data,
                        'raw_result': raw_data,
                        'operation_type': intent
                    }
                    
                    logger.info(f"Unified intent + action executed for user {state.user_id}: {intent} (recovered from JSON error)")
                    logger.info(f"Entities extracted: {entities}")
                    
                except json.JSONDecodeError:
                    logger.error("Could not repair JSON, falling back to chat")
                    # Final fallback to chat with the raw response
                    state.update_intent('chat')
                    state.update_entities({})
                    state.update_response("I had trouble processing that request. Could you please rephrase it?")
                    return state
            
            return state
            
        except Exception as e:
            logger.error(f"Error in unified intent + action for user {state.user_id}: {e}")
            state.set_error(f"Unified processing error: {str(e)}")
            return state
    
    def detect_intent(self, state: AgentState) -> AgentState:
        """Backward compatibility wrapper - now calls unified method"""
        return self.detect_intent_and_execute(state)
    
    def get_context_for_intent(self, user_id: str) -> str:
        """Get conversation context for intent detection"""
        return self.llm.get_context_summary(user_id) 