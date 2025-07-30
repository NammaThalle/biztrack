from crewai import Agent
from pydantic import PrivateAttr

class GeminiLLM:
    def __init__(self, api_key):
        self.api_key = api_key
    def chat(self, prompt, context=None):
        return "[Gemini LLM response]"

class IntentDetectionAgent(Agent):
    def __init__(self, llm):
        super().__init__(
            role="Intent Detection Agent",
            goal="Autonomously decide the user's intent and required action, returning a structured JSON object.",
            backstory="You are an expert at understanding business communication. For each message, you decide the next action and return a JSON object with 'action' and 'data'."
        )
        self.llm = llm
    def detect_intent(self, message, context=None):
        context_str = f"\nContext:\n{context}" if context else ""
        prompt = (
            "IMPORTANT: NEVER use any APOC procedures or functions in Cypher. If you use any APOC function, it will cause an error. Use only standard Cypher and built-in functions. For unique IDs, use randomUUID(). Never use apoc.create.uuid().\n"
            "You are an autonomous business assistant. Given a user message and conversation context, decide what action to take and return a JSON object with:\n"
            "- 'action': one of ['graph_query', 'answer_question', 'chat']\n"
            "- 'data': for 'graph_query', include:\n"
            "    - 'cypher_intent': the user's message\n"
            "    - 'cypher': the Cypher query to execute\n"
            "    - any relevant structured data (e.g., for product addition, include a 'product' object with name, price, description)\n"
            "For 'answer_question', include the question; for 'chat', generate a helpful, friendly, and context-aware reply to the user and include it as the value of the 'message' field. For chat responses, be conversational and contextual - if the user asks 'Anything else?', respond appropriately based on the conversation context.\n"
            "If the user wants to add, update, or query the business graph (e.g., products, vendors, transactions, commissions), use 'graph_query'.\n"
            "IMPORTANT: For any entity with a name (vendor, product, customer), always use a 'normalized_name' property set to toLower(trim(name)) for all MERGE and MATCH operations, and also store the original 'name' property for display.\n"
            f"Message: \"{message}\"{context_str}\n"
            "Return only the JSON object."
        )
        return self.llm.chat(prompt, context)

class TransactionExtractionAgent(Agent):
    def __init__(self, llm):
        super().__init__(
            role="Transaction Extraction Agent",
            goal="Extract structured transaction data from business messages.",
            backstory="You are skilled at parsing business messages and extracting structured data for purchases, sales, and commissions."
        )
        self.llm = llm
    def extract(self, message, context=None):
        return self.llm.chat(f"Extract transaction data from this message: {message}", context)

class KnowledgeQAAgent(Agent):
    def __init__(self, llm):
        super().__init__(
            role="Knowledge QA Agent",
            goal="Answer business-related questions using transaction data.",
            backstory="You are a business assistant who can answer questions about sales, purchases, commissions, and other business metrics using stored data."
        )
        self.llm = llm
    def answer(self, question, facts, context=None):
        context_str = f"\nContext:\n{context}" if context else ""
        return self.llm.chat(f"Answer this question: {question}\nFacts: {facts}{context_str}")

class StorageAgent(Agent):
    _use_neo4j: bool = PrivateAttr(default=False)
    _neo4j_agent: object = PrivateAttr(default=None)

    def __init__(self, use_neo4j=False, neo4j_agent=None, **kwargs):
        super().__init__(**kwargs)
        self._use_neo4j = use_neo4j
        self._neo4j_agent = neo4j_agent

    def store(self, data):
        return "(SQLite integration removed)"

    def run_graph_query(self, user_message, context=None):
        if self._use_neo4j and self._neo4j_agent:
            return self._neo4j_agent.run_cypher_from_llm(user_message, context)
        return {"error": "Neo4j not enabled or not configured."}

class ChatAgent(Agent):
    def __init__(self, llm):
        super().__init__(
            role="Chat Agent",
            goal="Provide friendly, context-aware responses to the user.",
            backstory="You are a helpful and conversational assistant for business and general queries."
        )
        self.llm = llm
    def reply(self, message, context=None):
        context_str = f"\nContext:\n{context}" if context else ""
        prompt = f"You are a helpful business assistant. Generate a friendly and helpful response to: {message}{context_str}"
        return self.llm.chat(prompt, context) 