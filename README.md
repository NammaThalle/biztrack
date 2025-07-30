# Business Tracker Bot

A sophisticated Telegram bot for business transaction tracking using CrewAI, Neo4j, and LangChain memory.

## Project Structure

```
crew-ai-chatbot/
├── main.py                          # Entry point
├── requirements.txt                  # Dependencies
├── docker-compose.yml               # Neo4j Docker setup
├── .env                             # Environment variables
├── README.md                        # This file
├── src/                             # Source code
│   ├── __init__.py
│   ├── orchestrator.py              # Main orchestration logic
│   ├── agents/                      # CrewAI agents
│   │   ├── __init__.py
│   │   └── business_agents.py       # Business logic agents
│   ├── memory/                      # Memory management
│   │   ├── __init__.py
│   │   └── conversation_memory.py   # LangChain memory system
│   ├── storage/                     # Data storage
│   │   ├── __init__.py
│   │   ├── graph_storage.py         # Neo4j operations
│   │   └── sqlite_storage.py        # SQLite operations (legacy)
│   ├── config/                      # Configuration
│   │   ├── __init__.py
│   │   └── bot_config.py            # Bot configuration
│   └── utils/                       # Utilities
│       ├── __init__.py
│       ├── gemini_client.py         # Gemini API client
│       └── logger.py                # Logging utilities
├── tests/                           # Test files
└── docs/                            # Documentation
```

## Features

### 🤖 Multi-Agent Architecture (CrewAI)
- **IntentDetectionAgent**: Automatically identifies user intent
- **TransactionExtractionAgent**: Extracts structured data from messages
- **KnowledgeQAAgent**: Answers business questions using RAG
- **StorageAgent**: Manages data persistence
- **ChatAgent**: Handles conversational responses

### 💾 Advanced Memory System (LangChain)
- **ConversationBufferMemory**: Maintains conversation history
- **SQLChatMessageHistory**: Persistent SQL storage
- **Context-Aware Responses**: Uses conversation history for better responses
- **User-Specific Memory**: Each user has isolated memory

### 🗄️ Graph Database (Neo4j)
- **Transaction Nodes**: Purchase, sale, commission records
- **Entity Nodes**: Products, vendors, customers
- **Relationships**: Tracks business relationships
- **LLM-Driven Queries**: Dynamic Cypher generation

### 🔧 Key Capabilities
- **Natural Language Processing**: No explicit commands needed
- **Business Tracking**: Log purchases, sales, commissions
- **Product Management**: Add and track products
- **Contextual Understanding**: Remembers conversation history
- **Graph Queries**: Complex business analytics

## Setup

### 1. Environment Setup
```bash
# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Variables (.env)
```env
GEMINI_API_KEY=your_gemini_api_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=changeme123
USE_NEO4J=true
GEMINI_MODEL=gemini-2.5-flash
```

### 3. Start Neo4j
```bash
docker-compose up -d
```

### 4. Run the Bot
```bash
python main.py
```

## Usage Examples

### Basic Interactions
```
User: "Hi"
Bot: "Hello! How can I help you today?"

User: "Add product ortho kit price 500"
Bot: "Product 'ortho kit' added with price 500."

User: "Bought ortho kits for 5000 from sajan"
Bot: "Logged purchase of ortho kits for 5000 from sajan."

User: "Show me all products"
Bot: "Here are your products: [list of products]"
```

### Context-Aware Responses
```
User: "Add the same product"
Bot: "I'll add another ortho kit for you." (remembers last product)

User: "How much did I pay sajan?"
Bot: "You paid 5000 to sajan for ortho kits." (remembers vendor and amount)
```

## Architecture Highlights

### Memory System
- **LangChain Integration**: Uses proven conversation memory
- **SQL Persistence**: Reliable database storage
- **Context Window**: Last 10 messages for context
- **User Isolation**: Each user has separate memory

### Agent Orchestration
- **Intent Detection**: Autonomous action routing
- **Entity Extraction**: Structured data parsing
- **Graph Operations**: LLM-driven Neo4j queries
- **Response Formatting**: User-friendly output

### Data Storage
- **Neo4j Graph**: Business relationships and analytics
- **SQLite Legacy**: Backup storage (deprecated)
- **Memory Database**: Conversation history

## Development

### Adding New Features
1. **Agents**: Add to `src/agents/business_agents.py`
2. **Storage**: Add to `src/storage/` directory
3. **Memory**: Extend `src/memory/conversation_memory.py`
4. **Configuration**: Update `src/config/bot_config.py`

### Testing
```bash
# Run tests
python -m pytest tests/

# Test memory system
python -c "from src.memory.conversation_memory import langchain_memory_manager; print('Memory system working')"
```

## Dependencies

- **CrewAI**: Multi-agent orchestration
- **LangChain**: Memory and conversation management
- **Neo4j**: Graph database
- **python-telegram-bot**: Telegram integration
- **google-genai**: Gemini API client
- **python-dotenv**: Environment management

## License

MIT License 