"""
Configuration management for the Telegram Censor Bot
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Telegram Bot
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    
    # Ollama Configuration
    OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2')
    
    # Bot Settings
    MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', '20'))
    SUPPORTED_FORMATS = os.getenv('SUPPORTED_FORMATS', 'pdf,docx,xlsx,txt,jpg,jpeg,png,gif').split(',')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Censoring Settings
    CONFIDENCE_THRESHOLD = float(os.getenv('CONFIDENCE_THRESHOLD', '0.8'))
    REDACTION_COLOR = os.getenv('REDACTION_COLOR', 'black')
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN is required. Please set it in your .env file.")
        
        return True
