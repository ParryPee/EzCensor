"""
Text file processor
"""
import logging
import os
from typing import Dict, Any, List
from .base_processor import BaseProcessor, ProcessingResult

logger = logging.getLogger(__name__)

class TextProcessor(BaseProcessor):
    """Processor for plain text files"""
    
    def __init__(self):
        super().__init__()
        self.supported_extensions = ['txt']
    
    async def extract_text(self, file_path: str) -> str:
        """Extract text from text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            logger.info(f"Extracted {len(content)} characters from text file")
            return content
            
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, 'r', encoding='latin-1') as file:
                    content = file.read()
                logger.info(f"Extracted {len(content)} characters from text file (latin-1)")
                return content
            except Exception as e:
                logger.error(f"Error reading text file with latin-1 encoding: {e}")
                raise Exception(f"Failed to read text file: {str(e)}")
        except Exception as e:
            logger.error(f"Error extracting text from file: {e}")
            raise Exception(f"Failed to extract text: {str(e)}")
    
    async def apply_redactions(self, file_path: str, redactions: List[Dict[str, Any]], output_path: str) -> bool:
        """Apply redactions to text file"""
        try:
            # Read original content
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Apply redactions by replacing text
            redacted_content = content
            for redaction in redactions:
                text_to_redact = redaction.get('text', '')
                replacement = redaction.get('replacement', '[REDACTED]')
                
                if text_to_redact:
                    redacted_content = redacted_content.replace(text_to_redact, replacement)
            
            # Save redacted content
            with open(output_path, 'w', encoding='utf-8') as file:
                file.write(redacted_content)
            
            logger.info(f"Applied {len(redactions)} redactions to text file, saved to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error applying redactions to text file: {e}")
            return False
    
    async def process_file(self, file_path: str, ollama_service) -> ProcessingResult:
        """Complete processing workflow for text files"""
        try:
            # Extract text
            extracted_text = await self.extract_text(file_path)
            
            if not extracted_text.strip():
                return ProcessingResult(
                    success=False,
                    message="No text content found in file"
                )
            
            # Analyze for PII using Ollama
            pii_analysis = await ollama_service.analyze_text_for_pii(extracted_text)
            
            if not pii_analysis.get('found_pii', False):
                return ProcessingResult(
                    success=True,
                    message="No sensitive information detected in text file",
                    extracted_text=extracted_text,
                    pii_found=False
                )
            
            # Generate redactions
            redaction_suggestions = await ollama_service.generate_redaction_suggestions(pii_analysis)
            
            if not redaction_suggestions.get('needs_redaction', False):
                return ProcessingResult(
                    success=True,
                    message="No redactions needed based on confidence threshold",
                    extracted_text=extracted_text,
                    pii_found=True,
                    redaction_count=0
                )
            
            # Create output file
            output_path = await self.create_temp_file(f"redacted_{os.path.basename(file_path)}")
            
            # Apply redactions
            success = await self.apply_redactions(
                file_path, 
                redaction_suggestions['suggestions'], 
                output_path
            )
            
            if success:
                return ProcessingResult(
                    success=True,
                    message=f"Successfully redacted {len(redaction_suggestions['suggestions'])} sensitive items",
                    extracted_text=extracted_text,
                    output_file=output_path,
                    pii_found=True,
                    redaction_count=len(redaction_suggestions['suggestions'])
                )
            else:
                return ProcessingResult(
                    success=False,
                    message="Failed to apply redactions to text file"
                )
                
        except Exception as e:
            logger.error(f"Error processing text file: {e}")
            return ProcessingResult(
                success=False,
                message=f"Error processing text file: {str(e)}"
            )