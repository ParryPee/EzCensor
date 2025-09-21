"""
Main entry point for the Telegram Censor Bot
"""
import logging
import asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from src.config import Config
from src.handlers.message_handlers import (
    start_command,
    help_command, 
    status_command,
    handle_document,
    handle_photo,
    handle_unknown,
    error_handler
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO if not Config.DEBUG else logging.DEBUG
)
logger = logging.getLogger(__name__)

def main() -> None:
    """Start the bot"""
    try:
        # Validate configuration
        Config.validate()
        
        logger.info("Starting Telegram Censor Bot...")
        
        # Create application
        app = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        
        # Add command handlers
        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("status", status_command))
        
        # Add message handlers
        app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
        app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
        
        # Handle unknown message types
        app.add_handler(MessageHandler(
            ~(filters.COMMAND | filters.Document.ALL | filters.PHOTO), 
            handle_unknown
        ))
        
        # Add error handler
        app.add_error_handler(error_handler)
        
        logger.info("Bot setup complete. Starting polling...")
        
        # Start the bot
        app.run_polling(allowed_updates=["message"])
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        print(f"\n❌ Configuration Error: {e}")
        print("\n📝 Setup Instructions:")
        print("1. Copy '.env.example' to '.env'")
        print("2. Add your Telegram bot token to the .env file")
        print("3. Make sure Ollama is running: 'ollama serve'")
        print("4. Pull the required model: 'ollama pull llama3.2:3b'")
        
    except Exception as e:
        logger.error(f"Unexpected error starting bot: {e}")
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
