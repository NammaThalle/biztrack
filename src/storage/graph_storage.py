import os
from neo4j import GraphDatabase, basic_auth
from dotenv import load_dotenv
from src.utils.logger import logger
from src.utils.gemini_client import gemini_chat_client

load_dotenv()

class Neo4jStorageAgent:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "changeme123")
        self.driver = GraphDatabase.driver(self.uri, auth=basic_auth(self.user, self.password))
        # Using the global gemini_chat_client instance
        self.schema = (
            "Schema:\n"
            "(:Transaction)-[:INVOLVES_PRODUCT]->(:Product)\n"
            "(:Transaction)-[:FROM_VENDOR]->(:Vendor)\n"
            "(:Transaction)-[:TO_CUSTOMER]->(:Customer)\n"
            "(:Commission)-[:FROM_VENDOR]->(:Vendor)\n"
            "(:Product {name, price, description})\n"
            "(:Vendor {name})\n"
            "(:Customer {name})\n"
            "(:Transaction {transaction_id, type, amount, quantity, date, notes})\n"
            "(:Commission {commission_id, amount, date, ref_id, notes})\n"
        )

    def close(self):
        self.driver.close()

    def run_cypher_from_llm(self, user_message, context=None):
        """
        Given a user message, ask Gemini to generate a Cypher query, execute it, and return the result.
        """
        prompt = (
            f"You are a business graph database assistant. Given the following user request and the Neo4j schema, generate a Cypher query that fulfills the request. "
            f"Return only the Cypher query in a Markdown code block.\n"
            f"{self.schema}\n"
            f"User request: '{user_message}'"
        )
        logger.info("Prompting Gemini for Cypher query generation.")
        cypher_response = gemini_chat_client.send_message(
            user_id="system",  # Use system user for database operations
            message=prompt,
            system_instruction="You are a business graph database assistant. Generate Cypher queries only."
        )
        logger.info("Gemini responded with Cypher query.")
        cypher_query = self._extract_cypher_from_code_block(cypher_response)
        # logger.info(f"Executing Cypher: {cypher_query}")
        with self.driver.session() as session:
            try:
                result = session.run(cypher_query)
                records = [record.data() for record in result]
                logger.info(f"Cypher executed, {len(records)} records returned.")
                return records
            except Exception as e:
                logger.error(f"Cypher execution failed: {e}")
                return {"error": str(e), "cypher": cypher_query}

    def _extract_cypher_from_code_block(self, text):
        text = text.strip()
        if text.startswith('```'):
            lines = text.splitlines()
            # Remove lines starting and ending with triple backticks
            lines = [line for line in lines if not line.strip().startswith('```')]
            return '\n'.join(lines)
        return text 