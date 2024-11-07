from typing import Dict, List
import logging
from .base_agent import RetrievIOAgent

logger = logging.getLogger(__name__)

class EngagementAgent(RetrievIOAgent):
    def __init__(self, name: str = "Engagement Agent"):
        super().__init__(
            name=name,
            role="engagement",
            instructions="Analyze documents and generate engaging questions and insights"
        )
    
    def analyze_document(self, text: str, metadata: Dict) -> Dict:
        """Analyze document content and generate engagement suggestions"""
        try:
            prompt = f"""Analyze this document and provide a structured engagement summary.
            Focus on the main concepts and potential areas of interest.
            
            Document: {text[:3000]}...
            
            Provide the following in JSON format:
            1. Main topic and brief overview
            2. Key concepts (max 3)
            3. Three questions at different levels:
               - Basic understanding
               - Detailed comprehension
               - Practical application
            4. Suggested follow-up topics
            
            Format as:
            {{
                "topic": "Main topic",
                "overview": "Brief overview",
                "key_concepts": ["concept1", "concept2", "concept3"],
                "questions": {{
                    "basic": "Question about fundamental concept",
                    "detailed": "Question about specific details",
                    "practical": "Question about real-world application"
                }},
                "follow_up": ["topic1", "topic2"]
            }}
            """
            
            response = self.process(prompt)
            
            if "error" in response:
                raise Exception(response["error"])
            
            return {
                "document": metadata["file_name"],
                "analysis": response["content"],
                "model": response["model"]
            }
            
        except Exception as e:
            logger.error(f"Failed to generate engagement content: {str(e)}")
            return {
                "document": metadata.get("file_name", "unknown"),
                "error": str(e)
            } 