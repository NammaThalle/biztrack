from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from src.graph.workflow import BusinessWorkflow
from src.graph.state import AgentState
from src.config.bot_config import TELEGRAM_BOT_TOKEN
from src.utils.logger import logger
from src.utils.gemini_client import gemini_chat_client
from src.utils.cleanup import ensure_clean_state

class BusinessTrackerBot:
    """
    Business Tracker Bot using LangGraph with automatic message storage via Gemini chat sessions.
    No manual message storage needed - Gemini maintains conversation history.
    """
    
    def __init__(self):
        self.workflow = BusinessWorkflow().create_workflow()
        logger.info("Business Tracker Bot initialized with automatic memory management")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming Telegram messages using LangGraph workflow"""
        try:
            message = update.message.text
            user_id = str(update.message.from_user.name)
            telegram_date = update.message.date.strftime('%Y-%m-%d')
            
            logger.info(f"Received message from user {user_id}: {message}")
            
            # Create initial state with automatic context from Gemini
            initial_state = AgentState(
                user_id=user_id,
                message=message
            )
            
            # Execute LangGraph workflow
            logger.info(f"Executing workflow for user {user_id}")
            result = await self.workflow.ainvoke(initial_state)
            
            # Send response with MarkdownV2 formatting
            response_text = result.get('response') or "I'm sorry, I couldn't process your request."
            
            # Send as plain text since we're not using markdown formatting anymore
            await update.message.reply_text(response_text)
            
            logger.info(f"Sent response to user {user_id}")
            
        except Exception as e:
            logger.error(f"Error handling message for user {user_id}: {e}")
            await update.message.reply_text(
                "I'm sorry, there was an error processing your request. Please try again."
            )
    
    def get_conversation_history(self, user_id: str, limit: int = 10):
        """Get conversation history from Gemini's chat session"""
        return gemini_chat_client.get_conversation_history(user_id, limit)
    
    def clear_user_history(self, user_id: str):
        """Clear conversation history for a user"""
        gemini_chat_client.clear_history(user_id)
        logger.info(f"Cleared history for user {user_id}")
    
    def get_active_users(self):
        """Get list of users with active chat sessions"""
        return gemini_chat_client.get_all_users()

def main():
    """Initialize and run the Business Tracker Bot"""
    logger.info("Starting Business Tracker Bot with automatic memory management...")
    
    # Ensure clean state by removing __pycache__ directories
    ensure_clean_state()
    
    # Clean up old sessions on startup
    gemini_chat_client.cleanup_old_sessions(max_sessions=50)
    
    # Create bot instance
    bot = BusinessTrackerBot()
    
    # Setup Telegram application
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), bot.handle_message))
    
    logger.info("Business Tracker Bot is running with automatic message storage...")
    
    # Start polling
    app.run_polling()

if __name__ == "__main__":
    main() 