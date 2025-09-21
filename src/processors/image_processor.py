"""
Image processor with OCR capabilities
"""
import logging
import os
from typing import Dict, Any, List
from .base_processor import BaseProcessor, ProcessingResult

logger = logging.getLogger(__name__)

class ImageProcessor(BaseProcessor):
    """Processor for image files with OCR text extraction"""
    
    def __init__(self):
        super().__init__()
        self.supported_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp']
    
    async def extract_text(self, file_path: str) -> str:
        """Extract text from image using OCR"""
        try:
            import easyocr
            
            # Initialize OCR reader (English by default)
            reader = easyocr.Reader(['en'])
            
            # Extract text from image
            results = reader.readtext(file_path)
            
            # Combine all text results
            extracted_text = ""
            for (bbox, text, confidence) in results:
                if confidence > 0.5:  # Only include text with decent confidence
                    extracted_text += text + " "
            
            logger.info(f"Extracted {len(extracted_text)} characters from image via OCR")
            return extracted_text.strip()
            
        except ImportError:
            logger.error("EasyOCR not installed. Install with: pip install easyocr")
            raise Exception("OCR processing library not available")
        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            raise Exception(f"Failed to extract text from image: {str(e)}")
    
    async def apply_redactions(self, file_path: str, redactions: List[Dict[str, Any]], output_path: str) -> bool:
        """Apply redactions to image by drawing black rectangles over sensitive areas"""
        try:
            from PIL import Image, ImageDraw
            import easyocr
            
            # Open image
            image = Image.open(file_path)
            draw = ImageDraw.Draw(image)
            
            # Initialize OCR reader to get text positions
            reader = easyocr.Reader(['en'])
            ocr_results = reader.readtext(file_path)
            
            # Apply redactions
            redacted_count = 0
            for redaction in redactions:
                text_to_redact = redaction.get('text', '').strip()
                if not text_to_redact:
                    continue
                
                # Find matching text in OCR results
                for (bbox, detected_text, confidence) in ocr_results:
                    if confidence > 0.5 and text_to_redact.lower() in detected_text.lower():
                        # Draw black rectangle over the text
                        # bbox is in format: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                        x_coords = [point[0] for point in bbox]
                        y_coords = [point[1] for point in bbox]
                        
                        min_x, max_x = min(x_coords), max(x_coords)
                        min_y, max_y = min(y_coords), max(y_coords)
                        
                        # Draw filled black rectangle
                        draw.rectangle([min_x, min_y, max_x, max_y], fill='black')
                        redacted_count += 1
            
            # Save redacted image
            image.save(output_path)
            
            logger.info(f"Applied {redacted_count} redactions to image, saved to {output_path}")
            return True
            
        except ImportError as e:
            logger.error(f"Required libraries not installed: {e}")
            return False
        except Exception as e:
            logger.error(f"Error applying redactions to image: {e}")
            return False
    
    async def process_file(self, file_path: str, ollama_service) -> ProcessingResult:
        """Complete processing workflow for image files"""
        try:
            # Extract text using OCR
            extracted_text = await self.extract_text(file_path)
            
            if not extracted_text.strip():
                return ProcessingResult(
                    success=True,
                    message="No text detected in image",
                    extracted_text="",
                    pii_found=False
                )
            
            # Analyze for PII using Ollama
            pii_analysis = await ollama_service.analyze_text_for_pii(extracted_text)
            
            if not pii_analysis.get('found_pii', False):
                return ProcessingResult(
                    success=True,
                    message="No sensitive information detected in image text",
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
            file_extension = os.path.splitext(file_path)[1]
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
                    message=f"Successfully redacted {len(redaction_suggestions['suggestions'])} sensitive items from image",
                    extracted_text=extracted_text,
                    output_file=output_path,
                    pii_found=True,
                    redaction_count=len(redaction_suggestions['suggestions'])
                )
            else:
                return ProcessingResult(
                    success=False,
                    message="Failed to apply redactions to image"
                )
                
        except Exception as e:
            logger.error(f"Error processing image file: {e}")
            return ProcessingResult(
                success=False,
                message=f"Error processing image: {str(e)}"
            )