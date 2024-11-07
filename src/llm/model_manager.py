import ollama
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ModelParams(Enum):
    TEMPERATURE = "temperature"
    TOP_P = "top_p"
    TOP_K = "top_k"
    NUM_PREDICT = "num_predict"
    STOP = "stop"

@dataclass
class ModelConfig:
    model_id: str
    system_prompt: str
    params: Dict = None
    
    def to_dict(self) -> Dict:
        return {
            "model": self.model_id,
            "system": self.system_prompt,
            **(self.params or {})
        }

class ModelManager:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        ollama.set_base_url(base_url)
        self._verify_connection()
        
    def _verify_connection(self):
        try:
            models = ollama.list()
            logger.info(f"Connected to Ollama. Available models: {models}")
        except Exception as e:
            logger.error(f"Failed to connect to Ollama: {str(e)}")
            raise ConnectionError("Could not connect to Ollama server")
    
    def get_model_config(self, role: str) -> ModelConfig:
        """Get model configuration for specific agent role"""
        configs = {
            "document_parser": ModelConfig(
                model_id="llama2",
                system_prompt="""You are a document parsing assistant. Your role is to:
                1. Extract and structure text content
                2. Identify document sections and metadata
                3. Clean and normalize text
                Use the provided tools to process documents.""",
                params={
                    "temperature": 0.2,
                    "num_predict": 1000
                }
            ),
            "qa": ModelConfig(
                model_id="llama2",
                system_prompt="""You are a helpful assistant answering questions based on provided context.
                Always:
                1. Base answers strictly on the given context
                2. Cite sources when possible
                3. Admit when information is not available
                4. Be concise but thorough""",
                params={
                    "temperature": 0.7,
                    "num_predict": 500
                }
            ),
            # Add more role-specific configs
        }
        return configs.get(role, configs["qa"])  # Default to QA config
    
    def chat(
        self,
        messages: List[Dict],
        model_config: ModelConfig,
        stream: bool = False
    ) -> Dict:
        """Send chat completion request to Ollama"""
        try:
            response = ollama.chat(
                model=model_config.model_id,
                messages=messages,
                stream=stream,
                options=model_config.params
            )
            
            return {
                "content": response["message"]["content"],
                "model": model_config.model_id,
                "usage": {
                    "prompt_tokens": response.get("prompt_eval_count", 0),
                    "completion_tokens": response.get("eval_count", 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Chat completion failed: {str(e)}")
            return {"error": str(e)} 