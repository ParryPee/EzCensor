"""
Base processor class for all file types
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import tempfile
import os
import logging

logger = logging.getLogger(__name__)

class BaseProcessor(ABC):
    """Abstract base class for all file processors"""
    
    def __init__(self):
        self.supported_extensions: List[str] = []
        self.max_file_size_mb: int = 20
    
    @abstractmethod
    async def extract_text(self, file_path: str) -> str:
        """
        Extract text content from the file
        
        Args:
            file_path: Path to the file to process
            
        Returns:
            Extracted text content
        """
        pass
    
    @abstractmethod
    async def apply_redactions(self, file_path: str, redactions: List[Dict[str, Any]], output_path: str) -> bool:
        """
        Apply redactions to the file and save to output path
        
        Args:
            file_path: Original file path
            redactions: List of redaction instructions
            output_path: Where to save the redacted file
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    def is_supported(self, file_extension: str) -> bool:
        """Check if file extension is supported by this processor"""
        return file_extension.lower() in self.supported_extensions
    
    def validate_file_size(self, file_size: int) -> bool:
        """Validate file size is within limits"""
        max_bytes = self.max_file_size_mb * 1024 * 1024
        return file_size <= max_bytes
    
    async def create_temp_file(self, original_filename: str) -> str:
        """Create a temporary file for processing"""
        temp_dir = os.path.join(os.getcwd(), 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        temp_file = tempfile.NamedTemporaryFile(
            dir=temp_dir,
            suffix=f"_{original_filename}",
            delete=False
        )
        temp_file.close()
        return temp_file.name
    
    def cleanup_temp_file(self, file_path: str) -> None:
        """Clean up temporary file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.debug(f"Cleaned up temp file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temp file {file_path}: {e}")

class ProcessingResult:
    """Result of file processing operation"""
    
    def __init__(self, success: bool, message: str = "", 
                 extracted_text: str = "", output_file: Optional[str] = None,
                 pii_found: bool = False, redaction_count: int = 0):
        self.success = success
        self.message = message
        self.extracted_text = extracted_text
        self.output_file = output_file
        self.pii_found = pii_found
        self.redaction_count = redaction_count