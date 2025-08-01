from langchain.tools import BaseTool
from typing import Dict, Any, Optional
from src.storage.graph_storage import Neo4jStorageAgent
from src.utils.logger import logger

class GraphQueryTool(BaseTool):
    """Tool for querying the business graph database"""
    
    name: str = "graph_query"
    description: str = """
    Query the business graph database for products, vendors, customers, transactions, and relationships.
    Use this tool when users ask about business data, want to see products, vendors, or transaction history.
    """
    
    def __init__(self):
        super().__init__()
        # Initialize Neo4j agent lazily to avoid Pydantic issues
        self._neo4j_agent = None
    
    @property
    def neo4j_agent(self):
        if self._neo4j_agent is None:
            self._neo4j_agent = Neo4jStorageAgent()
        return self._neo4j_agent
    
    def _run(self, query: str, user_id: str = None) -> str:
        """Execute graph query using LLM-driven Cypher generation"""
        try:
            logger.info(f"Executing graph query for user {user_id}: {query}")
            result = self.neo4j_agent.run_cypher_from_llm(query, context=None)
            
            if isinstance(result, dict) and 'error' in result:
                return f"Error executing query: {result['error']}"
            
            return str(result)
            
        except Exception as e:
            logger.error(f"Error in graph query tool: {e}")
            return f"Error executing graph query: {str(e)}"

class AddProductTool(BaseTool):
    """Tool for adding products to the business database"""
    
    name: str = "add_product"
    description: str = """
    Add a new product to the business database with name, price, and optional description.
    Use this tool when users want to add or create new products.
    """
    
    def __init__(self):
        super().__init__()
        # Initialize Neo4j agent lazily to avoid Pydantic issues
        self._neo4j_agent = None
    
    @property
    def neo4j_agent(self):
        if self._neo4j_agent is None:
            self._neo4j_agent = Neo4jStorageAgent()
        return self._neo4j_agent
    
    def _run(self, name: str, price: float, description: str = None) -> str:
        """Add product to graph database"""
        try:
            logger.info(f"Adding product: {name}, price: {price}")
            
            # Create Cypher query for adding product
            cypher_query = f"""
            MERGE (p:Product {{normalized_name: toLower(trim('{name}'))}})
            SET p.name = '{name}', p.price = {price}
            """
            
            if description:
                cypher_query += f", p.description = '{description}'"
            
            result = self.neo4j_agent.run_cypher_from_llm(
                f"Add product {name} with price {price}" + (f" and description {description}" if description else ""),
                context=None
            )
            
            return f"Product '{name}' added successfully with price {price}"
            
        except Exception as e:
            logger.error(f"Error adding product: {e}")
            return f"Error adding product: {str(e)}"

class LogTransactionTool(BaseTool):
    """Tool for logging business transactions"""
    
    name: str = "log_transaction"
    description: str = """
    Log a business transaction (purchase, sale, commission) with details.
    Use this tool when users mention buying, selling, or any business transaction.
    """
    
    def __init__(self):
        super().__init__()
        # Initialize Neo4j agent lazily to avoid Pydantic issues
        self._neo4j_agent = None
    
    @property
    def neo4j_agent(self):
        if self._neo4j_agent is None:
            self._neo4j_agent = Neo4jStorageAgent()
        return self._neo4j_agent
    
    def _run(self, transaction_type: str, amount: float, product: str, 
              vendor: str = None, customer: str = None, quantity: int = 1, date: str = None) -> str:
        """Log transaction in graph database"""
        try:
            logger.info(f"Logging transaction: {transaction_type}, {product}, {amount}")
            
            # Use LLM to generate proper Cypher query
            transaction_desc = f"{transaction_type} of {product} for {amount}"
            if vendor:
                transaction_desc += f" from {vendor}"
            if customer:
                transaction_desc += f" to {customer}"
            
            result = self.neo4j_agent.run_cypher_from_llm(transaction_desc, context=None)
            
            return f"Successfully logged {transaction_type} of {product} for {amount}"
            
        except Exception as e:
            logger.error(f"Error logging transaction: {e}")
            return f"Error logging transaction: {str(e)}"

class BusinessAnalyticsTool(BaseTool):
    """Tool for business analytics and reporting"""
    
    name: str = "business_analytics"
    description: str = """
    Generate business analytics, reports, and insights from the graph database.
    Use this tool when users ask for reports, analytics, or business insights.
    """
    
    def __init__(self):
        super().__init__()
        # Initialize Neo4j agent lazily to avoid Pydantic issues
        self._neo4j_agent = None
    
    @property
    def neo4j_agent(self):
        if self._neo4j_agent is None:
            self._neo4j_agent = Neo4jStorageAgent()
        return self._neo4j_agent
    
    def _run(self, analysis_type: str, user_id: str = None) -> str:
        """Generate business analytics"""
        try:
            logger.info(f"Generating analytics: {analysis_type}")
            
            # Map analysis types to queries
            analysis_queries = {
                "total_sales": "Show me total sales amount",
                "top_products": "What are my top selling products?",
                "vendor_summary": "Show me vendor transaction summary",
                "revenue_trends": "Show me revenue trends",
                "product_performance": "Which products are performing best?"
            }
            
            query = analysis_queries.get(analysis_type, analysis_type)
            result = self.neo4j_agent.run_cypher_from_llm(query, context=None)
            
            return f"Analytics for {analysis_type}: {result}"
            
        except Exception as e:
            logger.error(f"Error in analytics tool: {e}")
            return f"Error generating analytics: {str(e)}" 