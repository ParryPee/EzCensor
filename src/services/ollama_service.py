"""
Ollama service for LLM integration
"""
import logging
import ollama
from typing import Optional, Dict, Any
from src.config import Config

logger = logging.getLogger(__name__)

class OllamaService:
    def __init__(self):
        self.client = ollama.Client(host=Config.OLLAMA_BASE_URL)
        self.model = Config.OLLAMA_MODEL
        
    async def is_available(self) -> bool:
        """Check if Ollama service is available"""
        try:
            models = self.client.list()
            model_names = [model['name'] for model in models['models']]
            return self.model in model_names
        except Exception as e:
            logger.error(f"Error checking Ollama availability: {e}")
            return False
    
    async def analyze_text_for_pii(self, text: str) -> Dict[str, Any]:
        """
        Analyze text for personally identifiable information (PII)
        
        Args:
            text: The text to analyze
            
        Returns:
            Dictionary containing analysis results
        """
        try:
            prompt = f"""
Analyze the following text for personally identifiable information (PII) and sensitive data. 
Identify and categorize any sensitive information found.

Categories to look for:
- Names (first, last, full names)
- Email addresses
- Phone numbers
- Addresses (street, city, postal codes)
- Credit card numbers
- Social security numbers
- Bank account numbers
- ID numbers (passport, driver's license, etc.)
- Date of birth
- Medical information

Text to analyze:
{text}

Respond in JSON format with:
{{
    "found_pii": true/false,
    "categories": ["category1", "category2", ...],
    "details": [
        {{
            "type": "category",
            "text": "actual sensitive text found",
            "confidence": 0.0-1.0,
            "start_pos": position_in_text,
            "end_pos": position_in_text
        }}
    ],
    "recommendation": "brief recommendation"
}}

Do NOT include additional explanation as the response will be put into json.loads to convert into a json readable format.
"""

            response = self.client.chat(
                model=self.model,
                messages=[{
                    'role': 'user',
                    'content': prompt
                }],
                options={
                    'temperature': 0.1,  # Low temperature for consistent results
                    'top_p': 0.9
                }
            )
            
            result_text = response['message']['content']
            
            # Try to parse as JSON, fallback to text analysis if needed
            try:
                import json
                result = json.loads(result_text)
                return result
            except json.JSONDecodeError:
                # If JSON parsing fails, return a basic structure
                logger.warning("Failed to parse LLM response as JSON")
                return {
                    "found_pii": True,
                    "categories": ["unknown"],
                    "details": [],
                    "recommendation": "Manual review recommended",
                    "raw_response": result_text
                }
                
        except Exception as e:
            logger.error(f"Error analyzing text with Ollama: {e}")
            return {
                "found_pii": False,
                "categories": [],
                "details": [],
                "recommendation": "Analysis failed - manual review required",
                "error": str(e)
            }
    
    async def generate_redaction_suggestions(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate suggestions for redacting sensitive information
        
        Args:
            analysis_result: Result from analyze_text_for_pii
            
        Returns:
            Dictionary with redaction suggestions
        """
        if not analysis_result.get('found_pii', False):
            return {
                "needs_redaction": False,
                "suggestions": []
            }
        
        suggestions = []
        for detail in analysis_result.get('details', []):
            if detail.get('confidence', 0) >= Config.CONFIDENCE_THRESHOLD:
                suggestions.append({
                    "text": detail['text'],
                    "replacement": self._generate_replacement(detail['type']),
                    "type": detail['type'],
                    "confidence": detail['confidence']
                })
        
        return {
            "needs_redaction": len(suggestions) > 0,
            "suggestions": suggestions
        }
    
    def _generate_replacement(self, pii_type: str) -> str:
        """Generate appropriate replacement text for different PII types"""
        replacements = {
            "name": "[NAME REDACTED]",
            "email": "[EMAIL REDACTED]",
            "phone": "[PHONE REDACTED]",
            "address": "[ADDRESS REDACTED]",
            "credit_card": "[CARD NUMBER REDACTED]",
            "ssn": "[SSN REDACTED]",
            "bank_account": "[ACCOUNT NUMBER REDACTED]",
            "id_number": "[ID NUMBER REDACTED]",
            "date_of_birth": "[DOB REDACTED]",
            "medical": "[MEDICAL INFO REDACTED]"
        }
        
        return replacements.get(pii_type.lower(), "[SENSITIVE INFO REDACTED]")

# Global instance
ollama_service = OllamaService()
