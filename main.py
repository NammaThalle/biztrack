from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from src.config.bot_config import TELEGRAM_BOT_TOKEN
from src.storage.sqlite_storage import init_db
from src.orchestrator import handle_message
from src.memory.conversation_memory import langchain_memory_manager
import asyncio
from src.utils.logger import logger

async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text
    telegram_date = update.message.date.strftime('%Y-%m-%d')
    user_id = update.message.from_user.id
    logger.info(f"Received message from user {user_id}")
    reply = handle_message(message, telegram_date, user_id)
    if asyncio.iscoroutine(reply):
        reply = await reply
    logger.info(f"Replying to user {user_id}")
    await update.message.reply_text(str(reply))

def main():
    logger.info("Initializing database...")
    init_db()
    
    # Clean up old memory on startup
    logger.info("Cleaning up old memory...")
    langchain_memory_manager.cleanup_old_memory(days_to_keep=30)
    
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), on_message))
    logger.info("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main() 