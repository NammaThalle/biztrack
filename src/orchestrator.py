import os
from src.storage.graph_storage import Neo4jStorageAgent  # Ensure this is always imported for type checking
from src.agents.business_agents import IntentDetectionAgent, TransactionExtractionAgent, KnowledgeQAAgent, StorageAgent, ChatAgent
from src.utils.gemini_client import GeminiLLM
from src.storage.sqlite_storage import query_transactions
from src.utils.logger import logger
from src.memory.conversation_memory import langchain_memory_manager
import json

# Neo4j integration config
USE_NEO4J = os.getenv("USE_NEO4J", "false").lower() == "true"
neo4j_agent = None
if USE_NEO4J:
    neo4j_agent = Neo4jStorageAgent()

llm = GeminiLLM()
intent_agent = IntentDetectionAgent(llm)
extract_agent = TransactionExtractionAgent(llm)
qa_agent = KnowledgeQAAgent(llm)
# Pass Neo4j agent to StorageAgent if enabled
storage_agent = StorageAgent(
    use_neo4j=USE_NEO4J,
    neo4j_agent=neo4j_agent,
    role="Storage Agent",
    goal="Store structured transaction data in the database.",
    backstory="You are responsible for reliably saving all business transactions and related data."
)
chat_agent = ChatAgent(llm)

def extract_json_from_code_block(text):
    """Remove Markdown code block formatting if present."""
    text = text.strip()
    if text.startswith('```'):
        lines = text.splitlines()
        # Remove lines starting and ending with triple backticks
        lines = [line for line in lines if not line.strip().startswith('```')]
        return '\n'.join(lines)
    return text

def handle_message(message, telegram_date, user_id=None):
    logger.info("Handling message")
    
    # Get relevant context from memory
    logger.info(f"Getting context for user {user_id} with message: {message}")
    context = langchain_memory_manager.get_context_for_user(str(user_id), message)
    logger.info(f"Retrieved context for user {user_id}: {context[:200] if context else 'No context'}")
    logger.info(f"Context length: {len(context) if context else 0}")
    
    # 1. Detect intent and action (fully autonomous) with context
    intent_response = intent_agent.detect_intent(message, context)
    logger.info(f"Intent agent response received.")
    try:
        json_str = extract_json_from_code_block(intent_response)
        intent_json = json.loads(json_str)
        action = intent_json.get('action')
        data = intent_json.get('data', {})
        logger.info(f"Parsed intent: action={action}, data={data}")
    except Exception as e:
        logger.error(f"Failed to parse intent agent response as JSON: {e}")
        logger.error(f"Raw response: {intent_response}")
        return chat_agent.reply(f"Sorry, I couldn't understand your request. (Intent agent error: {e})")

    if action == 'log_transaction':
        # Add date and raw_message if not present
        if 'date' not in data:
            data['date'] = telegram_date
        data['raw_message'] = message

        # Map LLM fields to DB schema fields
        data['product'] = data.get('product') or data.get('item')
        data['vendor'] = data.get('vendor') or data.get('from') or data.get('party') or data.get('counterparty')
        data['customer'] = data.get('customer')  # Add more mappings if needed

        logger.info(f"Storing transaction: {data}")
        storage_agent.store(data)
        logger.info("Neo4j updated with transaction." if getattr(storage_agent, '_use_neo4j', False) else "Transaction stored in SQLite only.")
        # Compose a user-friendly confirmation message
        if data.get('type') == 'purchase':
            confirmation = (
                f"Logged purchase of {data.get('quantity', '')} {data.get('product', '')} "
                f"for {data.get('amount', '')} from {data.get('vendor', '')}."
            )
        else:
            confirmation = "Transaction logged successfully."
        logger.info(f"Reply after storing: {confirmation}")
        return confirmation
    elif action == 'add_product':
        # Map LLM synonyms for product fields
        product_name = data.get('name') or data.get('product') or data.get('product_name')
        price = data.get('price') or data.get('unit_price')
        description = data.get('description')
        if not product_name or price is None:
            logger.error(f"Missing product name or price in add_product: {data}")
            return "Sorry, I couldn't add the product. Please specify both name and price."
        from src.storage.sqlite_storage import add_product
        try:
            add_product(product_name, float(price), description)
            logger.info(f"Product added to SQLite: {product_name}, price: {price}")
            if getattr(storage_agent, '_use_neo4j', False) and getattr(storage_agent, '_neo4j_agent', None):
                logger.info(f"Neo4j update for product addition is now handled via LLM-driven Cypher queries.")
            confirmation = f"Product '{product_name}' added with price {price}."
            return confirmation
        except Exception as e:
            logger.error(f"Failed to add product: {e}")
            return f"Sorry, there was an error adding the product: {e}"
    elif action == 'answer_question':
        from src.storage.sqlite_storage import query_transactions
        facts = query_transactions()
        logger.info(f"Facts for QA: {len(facts)} records.")
        question = data.get('question', message)
        reply = qa_agent.answer(question, facts, context)
        logger.info(f"QA reply sent.")
        return reply
    elif action == 'chat':
        # Handle different possible formats of chat response
        if isinstance(data, dict):
            chat_message = data.get('message') or data.get('response') or data.get('reply')
        else:
            chat_message = data
        
        # If no message found, generate a default response
        if not chat_message or chat_message.strip() == '':
            chat_message = "Hello! How can I help you today?"
        
        logger.info(f"Chat reply sent: {chat_message}")
        return chat_message
    elif action == 'graph_query':
        # LLM-driven Cypher query for Neo4j only
        result = storage_agent.run_graph_query(message, context)
        logger.info(f"Graph query executed, result: {result}")
        # Format the result for the user using the ChatAgent
        formatted_reply = chat_agent.reply(
            f"User message: {message}\nGraph result: {result}\n"
            "Generate a clear, concise, and friendly reply for the user. If the result is a list, summarize it. If it's a confirmation, state what was done. If the result is empty, confirm the action or explain that nothing was found.",
            context
        )
        logger.info(f"Formatted reply sent.")
        # Fallback: if reply is empty, too short, or looks like a raw list/dict, return a default message
        if not formatted_reply or len(str(formatted_reply).strip()) < 5 or str(formatted_reply).strip().startswith('[') or str(formatted_reply).strip().startswith('{'):
            if isinstance(result, list) and not result:
                return "Action completed successfully, but there is nothing to display."
            elif isinstance(result, dict) and 'error' in result:
                return f"Sorry, there was an error: {result['error']}"
            else:
                return "Action completed successfully."
        return formatted_reply
    else:
        logger.error(f"Unknown action from intent agent: {action}")
        response = "Sorry, I couldn't understand your request. (Unknown action: {action})"
    
    # Store the interaction in memory
    try:
        logger.info(f"Storing interaction in memory for user {user_id}")
        entities = langchain_memory_manager.extract_entities_for_memory(message, intent_json)
        logger.info(f"Extracted entities for memory: {entities}")
        langchain_memory_manager.store_interaction(
            user_id=str(user_id),
            message=message,
            response=response,
            intent=action,
            entities=entities
        )
        logger.info(f"Successfully stored interaction in memory")
        
        # Update business context if this was a transaction
        if action == 'graph_query' and entities:
            business_updates = {}
            if entities.get('product'):
                business_updates['last_product'] = entities['product']
            if entities.get('vendor'):
                business_updates['last_vendor'] = entities['vendor']
            if entities.get('customer'):
                business_updates['last_customer'] = entities['customer']
            if entities.get('type'):
                business_updates['last_transaction_type'] = entities['type']
            
            if business_updates:
                langchain_memory_manager.update_business_context(str(user_id), business_updates)
        
        logger.info(f"Stored interaction in memory for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to store interaction in memory: {e}")
    
    return response 