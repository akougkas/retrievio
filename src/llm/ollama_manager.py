import requests
import json
import logging
from typing import Dict, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)

class OllamaManager:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self._verify_connection()
        
    def _verify_connection(self):
        """Verify connection to Ollama server"""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            logger.info("Successfully connected to Ollama server")
        except Exception as e:
            logger.error(f"Failed to connect to Ollama server: {str(e)}")
            raise ConnectionError("Could not connect to Ollama server")
    
    def list_models(self) -> List[str]:
        """Get list of available models"""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            return [model['name'] for model in response.json()['models']]
        except Exception as e:
            logger.error(f"Failed to list models: {str(e)}")
            return []
    
    def generate(
        self,
        prompt: str,
        model: str = "llama2",
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> Dict:
        """Generate response from Ollama model"""
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                }
            }
            
            if system_prompt:
                payload["system"] = system_prompt
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload
            )
            response.raise_for_status()
            
            return {
                "text": response.json()["response"],
                "model": model,
                "usage": {
                    "prompt_tokens": response.json().get("prompt_eval_count", 0),
                    "completion_tokens": response.json().get("eval_count", 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Generation failed: {str(e)}")
            return {"error": str(e)} 
