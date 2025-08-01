# Business Tracker Bot

A sophisticated Telegram bot for business transaction tracking using **LangGraph**, **Neo4j**, and **Gemini's automatic chat sessions**.

## 🚀 **Architecture**

The Business Tracker Bot uses **LangGraph** with automatic memory management through **Gemini's chat sessions**.

### **Key Features:**
- ✅ **Automatic Memory**: Messages stored in Gemini chat sessions
- ✅ **Response Formatting**: Raw data → LLM formatting → User-friendly output
- ✅ **Telegram Integration**: Rich MarkdownV2 formatting
- ✅ **Graph Database**: Neo4j for business relationships
- ✅ **Error Handling**: Graceful fallbacks for all operations

## Project Structure

```
crew-ai-chatbot/
├── main.py                          # Business Tracker Bot entry point
├── requirements.txt                  # Bot dependencies
├── docker-compose.yml               # Neo4j Docker setup
├── .env                             # Environment variables
├── README.md                        # This file
├── workflow_diagram.md              # Workflow documentation
├── src/                             # Source code
│   ├── __init__.py
│   ├── graph/                       # LangGraph workflow
│   │   ├── __init__.py
│   │   ├── state.py                 # State management
│   │   └── workflow.py              # Main workflow
│   ├── agents/                      # LangGraph agents
│   │   ├── __init__.py
│   │   └── intent_agent.py          # Intent detection
│   ├── tools/                       # LangChain tools
│   │   ├── __init__.py
│   │   └── graph_tools.py           # Database operations
│   ├── storage/                     # Data storage
│   │   ├── __init__.py
│   │   └── graph_storage.py         # Neo4j operations
│   ├── config/                      # Configuration
│   │   ├── __init__.py
│   │   └── bot_config.py            # Bot configuration
│   └── utils/                       # Utilities
│       ├── __init__.py
│       ├── gemini_client.py          # Main Gemini client
│       ├── cleanup.py                # Cache cleanup utilities
│       └── logger.py                # Logging utilities
├── tests/                           # Test files
└── docs/                            # Documentation
```

## Features

### 🤖 **Workflow Architecture**
- **Intent Detection**: Automatic intent recognition using Gemini
- **Conditional Routing**: Smart routing based on user intent
- **Tool Integration**: LangChain tools for database operations
- **Response Formatting**: LLM-powered response formatting
- **State Management**: Centralized state management

### 💾 **Memory System (Gemini)**
- **Chat Sessions**: Automatic message storage in Gemini
- **Context Preservation**: Full conversation history available
- **No Manual Storage**: Eliminates complex memory management
- **User Isolation**: Each user has isolated chat sessions

### 🗄️ **Graph Database (Neo4j)**
- **Transaction Nodes**: Purchase, sale, commission records
- **Entity Nodes**: Products, vendors, customers
- **Relationships**: Tracks business relationships
- **LLM-Driven Queries**: Dynamic Cypher generation

### 🔧 **Key Capabilities**
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
Bot: "**Product Added Successfully!**\n\n• **ortho kit** - ₹500\n\nYour product has been added to the database."

User: "Bought ortho kits for 5000 from sajan"
Bot: "**Transaction Logged!**\n\n• **Purchase**: ortho kits\n• **Amount**: ₹5000\n• **Vendor**: Sajan Ohol\n\nTransaction has been recorded successfully."

User: "Show me all products"
Bot: "**Your Products:**\n\n• **ortho success** - ₹700\n• **ortho kits** - ₹500\n\nYou have 2 products in your database."
```

### Context-Aware Responses
```
User: "Add the same product"
Bot: "I'll add another ortho kit for you." (remembers last product)

User: "How much did I pay sajan?"
Bot: "You paid ₹5000 to Sajan Ohol for ortho kits." (remembers vendor and amount)
```

## Architecture Highlights

### **Workflow Design**
- **State-Driven**: Centralized state management with AgentState
- **Conditional Routing**: Smart routing based on intent
- **Tool Integration**: Clean tool-based architecture
- **Error Handling**: Better error handling and recovery

### **Memory System**
- **Gemini Integration**: Uses proven chat session functionality
- **No Manual Storage**: Eliminates complex SQL operations
- **Context Window**: Full conversation history available
- **User Isolation**: Each user has separate chat sessions

### **Response Formatting**
- **LLM Processing**: Raw data → LLM formatting → User-friendly output
- **Telegram Optimized**: Uses MarkdownV2 for rich formatting
- **Error Fallbacks**: Graceful handling of formatting failures

## Development

### Adding New Features
1. **Tools**: Add to `src/tools/` directory
2. **Agents**: Add to `src/agents/` directory
3. **Workflow**: Update `src/graph/workflow.py`
4. **Configuration**: Update `src/config/bot_config.py`

### Testing
```bash
# Run the Business Tracker Bot
python main.py

# Test memory functionality
python -c "from src.utils.gemini_client import gemini_chat_client; print('Gemini client working')"
```

## Dependencies

- **LangGraph**: Workflow orchestration
- **LangChain**: Tools and agents
- **Neo4j**: Graph database
- **python-telegram-bot**: Telegram integration
- **google-genai**: Gemini API client
- **python-dotenv**: Environment management

## License

MIT License 