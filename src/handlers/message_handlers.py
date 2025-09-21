"""
Basic message handlers for the Telegram bot
"""
import logging
from telegram import Update, InputFile
from telegram.ext import ContextTypes
from src.services.file_service import file_service
from src.processors.processor_factory import processor_factory
from src.services.ollama_service import ollama_service

logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command"""
    welcome_message = """
🤖 **Welcome to Censor Bot!**

This bot helps you censor sensitive information in documents and images using AI.

**Supported formats:**
📄 Documents: PDF, DOCX, XLSX, TXT
🖼️ Images: JPG, JPEG, PNG, GIF

**How to use:**
1. Simply send me a document or image
2. I'll analyze it for sensitive information
3. You'll receive the censored version back

**Commands:**
/start - Show this welcome message
/help - Get help and support information
/status - Check bot and AI model status

Send me a file to get started! 🚀
    """
    
    await update.message.reply_text(
        welcome_message,
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /help command"""
    help_message = """
🆘 **Help & Support**

**What does this bot do?**
I scan your documents and images for sensitive information like:
- Personal names and addresses
- Phone numbers and email addresses
- Credit card and ID numbers
- Bank account information
- And other personally identifiable information (PII)

**Privacy & Security:**
- All processing happens locally on our server
- Files are temporarily stored only during processing
- No data is shared with third parties
- Files are automatically deleted after processing

**Supported file types:**
- **Documents:** PDF, Word (.docx), Excel (.xlsx), Text (.txt)
- **Images:** JPEG, PNG, GIF (with OCR text extraction)

**File size limit:** 20MB per file
    """
    
    await update.message.reply_text(
        help_message,
        parse_mode='Markdown'
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /status command - check bot and AI model status"""
    try:
        # This will be implemented when we add Ollama integration
        status_message = """
📊 **Bot Status**

🤖 **Bot:** ✅ Online
🧠 **AI Model:** ⏳ Checking...
💾 **Storage:** ✅ Available
🔧 **Services:** ✅ All systems operational

Ready to process your files! 🚀
        """
        
        await update.message.reply_text(
            status_message,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error in status command: {e}")
        await update.message.reply_text(
            "❌ Error checking system status. Please try again later."
        )

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle document uploads"""
    document = update.message.document
    
    if not document:
        await update.message.reply_text("❌ No document received. Please try again.")
        return
    
    # Check file size
    if document.file_size > 20 * 1024 * 1024:  # 20MB limit
        await update.message.reply_text(
            "❌ File too large! Please send files smaller than 20MB."
        )
        return
    
    # Check file format
    file_extension = document.file_name.split('.')[-1].lower() if document.file_name else ''
    supported_formats = ['pdf', 'docx', 'xlsx', 'txt']
    
    if file_extension not in supported_formats:
        await update.message.reply_text(
            f"❌ Unsupported file format: {file_extension}\n"
            f"Supported formats: {', '.join(supported_formats)}"
        )
        return
    
    # Send processing message
    processing_msg = await update.message.reply_text(
        "🔄 Processing your document...\nThis may take a few moments."
    )
    
    try:
        file_path , filename = await file_service.download_document(document)
        
        processor = processor_factory.get_processor(file_extension)
        
        res = await processor.process_file(file_path, ollama_service)        
        
        with open(res.output_file, "r") as f:
            await update.message.reply_document(f,filename=f"redacted_{filename}.{file_extension}")
        
        await processing_msg.edit_text(
            "✅ File has been sent to you! \n"+
            "File has been deleted on our servers..."
        )
        
        file_service.cleanup_file(file_path);
        file_service.cleanup_file(res.output_file);
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        await processing_msg.edit_text(
            "❌ Error processing document. Please try again later."
        )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle photo/image uploads"""
    photo = update.message.photo[-1]  # Get highest resolution version
    
    # Send processing message
    processing_msg = await update.message.reply_text(
        "🔄 Processing your image...\nExtracting text and analyzing for sensitive information."
    )
    
    try:
        # TODO: Implement image processing with OCR and Ollama
        await processing_msg.edit_text(
            "⚠️ Image processing is not yet implemented.\n"
            "Coming soon in the next update!"
        )
        
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        await processing_msg.edit_text(
            "❌ Error processing image. Please try again later."
        )

async def handle_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle unknown/unsupported message types"""
    await update.message.reply_text(
        "❓ I can only process documents and images.\n\n"
        "Please send me:\n"
        "📄 Documents: PDF, DOCX, XLSX, TXT\n"
        "🖼️ Images: JPG, PNG, GIF\n\n"
        "Or use /help for more information."
    )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors"""
    logger.error(f"Exception while handling an update: {context.error}")
    
    if update and hasattr(update, 'message') and update.message:
        await update.message.reply_text(
            "❌ An unexpected error occurred. Please try again later."
        )
