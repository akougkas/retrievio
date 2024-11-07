from typing import List, Dict
import logging
import asyncio
from .base_agent import RetrievIOAgent
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class EmbedderAgent(RetrievIOAgent):
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", name: str = "Embedder"):
        super().__init__(
            name=name,
            role="embedder",
            instructions="Generate embeddings for text chunks"
        )
        self.model = SentenceTransformer(model_name)
    
    async def embed_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """Generate embeddings for chunks"""
        try:
            # Extract text from chunks
            texts = [chunk.text for chunk in chunks]
            
            # Generate embeddings in thread pool
            embeddings = await asyncio.get_event_loop().run_in_executor(
                None,
                self.model.encode,
                texts,
                True  # normalize_embeddings
            )
            
            # Add embeddings to chunk metadata
            for chunk, embedding in zip(chunks, embeddings):
                chunk.metadata["embedding"] = embedding.tolist()
            
            # Notify completion
            await self.send_message(
                "vector_store",
                {
                    "action": "embeddings_created",
                    "chunks": chunks
                }
            )
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            await self.send_message(
                "vector_store",
                {
                    "action": "embedding_failed",
                    "error": str(e)
                }
            )
            raise
    
    async def handle_message(self, message: AsyncMessage):
        """Handle incoming messages"""
        try:
            if message.message_type == "embed_request":
                chunks = await self.embed_chunks(message.content["chunks"])
                await self.send_message(
                    message.sender,
                    {
                        "action": "embed_response",
                        "chunks": chunks,
                        "request_id": message.id
                    }
                )
                
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            await self.send_message(
                message.sender,
                {
                    "action": "error",
                    "error": str(e),
                    "request_id": message.id
                }
            )