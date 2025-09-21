"""
Processor factory to manage different file type processors
"""
import logging
from typing import Optional, Dict, Any
from .base_processor import BaseProcessor
from .txt_processor import TextProcessor
from .pdf_processor import PDFProcessor
from .image_processor import ImageProcessor

logger = logging.getLogger(__name__)

class ProcessorFactory:
    """Factory class to create appropriate processors for different file types"""
    
    def __init__(self):
        self._processors = {
            'txt': TextProcessor(),
            'pdf': PDFProcessor(), 
            'jpg': ImageProcessor(),
            'jpeg': ImageProcessor(),
            'png': ImageProcessor(),
            'gif': ImageProcessor(),
            'bmp': ImageProcessor(),
        }
        
        # TODO: Add these when we implement them
        # 'docx': DocxProcessor(),
        # 'xlsx': XlsxProcessor(),
    
    def get_processor(self, file_extension: str) -> Optional[BaseProcessor]:
        """
        Get the appropriate processor for a file extension
        
        Args:
            file_extension: File extension (without the dot)
            
        Returns:
            Processor instance or None if not supported
        """
        ext = file_extension.lower().strip('.')
        return self._processors.get(ext)
    
    def is_supported(self, file_extension: str) -> bool:
        """Check if a file extension is supported"""
        ext = file_extension.lower().strip('.')
        return ext in self._processors
    
    def get_supported_extensions(self) -> list:
        """Get list of all supported file extensions"""
        return list(self._processors.keys())
    
    def get_supported_by_category(self) -> Dict[str, list]:
        """Get supported extensions grouped by category"""
        return {
            'documents': ['txt', 'pdf'],  # TODO: add 'docx', 'xlsx' when implemented
            'images': ['jpg', 'jpeg', 'png', 'gif', 'bmp']
        }

# Global instance
processor_factory = ProcessorFactory()