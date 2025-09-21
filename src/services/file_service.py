"""
File service for handling file downloads, uploads, and management
"""
import logging
import os
import tempfile
import aiohttp
from typing import Optional, Tuple
from telegram import Document, PhotoSize
from src.config import Config

logger = logging.getLogger(__name__)

class FileService:
    """Service for handling file operations"""
    
    def __init__(self):
        self.temp_dir = os.path.join(os.getcwd(), 'temp')
        os.makedirs(self.temp_dir, exist_ok=True)
    
    async def download_telegram_file(self, telegram_file, original_filename: str = None) -> Tuple[str, str]:
        """
        Download a file from Telegram servers
        
        Args:
            telegram_file: Telegram File object
            original_filename: Original filename from the message
            
        Returns:
            Tuple of (local_file_path, filename)
        """
        try:
            # Create a temporary file
            if original_filename:
                temp_file = tempfile.NamedTemporaryFile(
                    dir=self.temp_dir,
                    suffix=f"_{original_filename}",
                    delete=False
                )
            else:
                temp_file = tempfile.NamedTemporaryFile(
                    dir=self.temp_dir,
                    delete=False
                )
            
            temp_file.close()
            
            # Download the file
            await telegram_file.download_to_drive(temp_file.name)
            
            filename = original_filename or os.path.basename(temp_file.name)
            logger.info(f"Downloaded Telegram file: {filename} -> {temp_file.name}")
            
            return temp_file.name, filename
            
        except Exception as e:
            logger.error(f"Error downloading Telegram file: {e}")
            raise Exception(f"Failed to download file: {str(e)}")
    
    async def download_document(self, document: Document) -> Tuple[str, str]:
        """Download a Telegram document"""
        file = await document.get_file()
        return await self.download_telegram_file(file, document.file_name)
    
    async def download_photo(self, photo: PhotoSize) -> Tuple[str, str]:
        """Download a Telegram photo"""
        file = await photo.get_file()
        filename = f"photo_{photo.file_id}.jpg"
        return await self.download_telegram_file(file, filename)
    
    def validate_file_size(self, file_size: int) -> bool:
        """Validate file size against limits"""
        max_bytes = Config.MAX_FILE_SIZE_MB * 1024 * 1024
        return file_size <= max_bytes
    
    def get_file_extension(self, filename: str) -> str:
        """Extract file extension from filename"""
        if not filename:
            return ""
        return os.path.splitext(filename)[1].lower().strip('.')
    
    def is_supported_format(self, file_extension: str) -> bool:
        """Check if file format is supported"""
        return file_extension.lower() in Config.SUPPORTED_FORMATS
    
    def cleanup_file(self, file_path: str) -> None:
        """Clean up a temporary file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.debug(f"Cleaned up file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup file {file_path}: {e}")
    
    def cleanup_temp_files(self, max_age_hours: int = 24) -> None:
        """Clean up old temporary files"""
        try:
            import time
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            for filename in os.listdir(self.temp_dir):
                file_path = os.path.join(self.temp_dir, filename)
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getctime(file_path)
                    if file_age > max_age_seconds:
                        self.cleanup_file(file_path)
                        logger.debug(f"Cleaned up old temp file: {filename}")
                        
        except Exception as e:
            logger.warning(f"Error during temp file cleanup: {e}")
    
    def get_file_info(self, file_path: str) -> dict:
        """Get information about a file"""
        try:
            stat = os.stat(file_path)
            return {
                'size': stat.st_size,
                'size_mb': stat.st_size / (1024 * 1024),
                'created': stat.st_ctime,
                'modified': stat.st_mtime,
                'extension': self.get_file_extension(file_path)
            }
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {e}")
            return {}

# Global instance
file_service = FileService()