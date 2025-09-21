"""
PDF file processor using PyMuPDF (fitz)
"""
import logging
import os
from typing import Dict, Any, List
from .base_processor import BaseProcessor, ProcessingResult

logger = logging.getLogger(__name__)

class PDFProcessor(BaseProcessor):
    """Processor for PDF files"""
    
    def __init__(self):
        super().__init__()
        self.supported_extensions = ['pdf']
    
    async def extract_text(self, file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            import fitz  # PyMuPDF
            
            doc = fitz.open(file_path)
            text_content = ""
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text_content += page.get_text()
                text_content += "\n---PAGE BREAK---\n"
            
            doc.close()
            logger.info(f"Extracted {len(text_content)} characters from PDF")
            return text_content
            
        except ImportError:
            logger.error("PyMuPDF (fitz) not installed. Install with: pip install PyMuPDF")
            raise Exception("PDF processing library not available")
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise Exception(f"Failed to extract text from PDF: {str(e)}")
    
    async def apply_redactions(self, file_path: str, redactions: List[Dict[str, Any]], output_path: str) -> bool:
        """Apply redactions to PDF file"""
        try:
            import fitz
            
            doc = fitz.open(file_path)
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # Find and redact text on each page
                for redaction in redactions:
                    text_to_redact = redaction.get('text', '')
                    if not text_to_redact:
                        continue
                    
                    # Search for text instances on the page
                    text_instances = page.search_for(text_to_redact)
                    
                    for inst in text_instances:
                        # Create redaction annotation
                        redact_annot = page.add_redact_annot(inst)
                        redact_annot.set_colors(stroke=None, fill=(0, 0, 0))  # Black redaction
                        redact_annot.update()
                
                # Apply redactions
                page.apply_redactions()
            
            # Save the redacted document
            doc.save(output_path)
            doc.close()
            
            logger.info(f"Applied {len(redactions)} redactions to PDF, saved to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error applying redactions to PDF: {e}")
            return False
    
    async def process_file(self, file_path: str, ollama_service) -> ProcessingResult:
        """Complete processing workflow for PDF files"""
        try:
            # Extract text
            extracted_text = await self.extract_text(file_path)
            
            if not extracted_text.strip():
                return ProcessingResult(
                    success=False,
                    message="No text found in PDF file"
                )
            
            # Analyze for PII using Ollama
            pii_analysis = await ollama_service.analyze_text_for_pii(extracted_text)
            
            if not pii_analysis.get('found_pii', False):
                return ProcessingResult(
                    success=True,
                    message="No sensitive information detected in PDF",
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
                    message="Failed to apply redactions to PDF"
                )
                
        except Exception as e:
            logger.error(f"Error processing PDF file: {e}")
            return ProcessingResult(
                success=False,
                message=f"Error processing PDF: {str(e)}"
            )