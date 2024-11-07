from typing import List, Dict
import logging
from dataclasses import dataclass
import asyncio
from .base_agent import RetrievIOAgent

logger = logging.getLogger(__name__)

@dataclass
class TextChunk:
    text: str
    start_idx: int
    end_idx: int
    metadata: dict

class TextChunkerAgent(RetrievIOAgent):
    def __init__(self, chunk_size: int, overlap: int, name: str = "Text Chunker"):
        super().__init__(
            name=name,
            role="text_chunker",
            instructions=f"""Split text into chunks of approximately {chunk_size} characters 
            with {overlap} character overlap. Preserve context and avoid splitting mid-sentence."""
        )
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    async def chunk_text(self, text: str, metadata: dict = None) -> List[TextChunk]:
        """Split text into overlapping chunks"""
        try:
            prompt = f"""Split the following text into chunks:
            Text length: {len(text)} characters
            First 100 chars: {text[:100]}...
            
            Create chunks that:
            1. Are approximately {self.chunk_size} characters
            2. Have {self.overlap} character overlap
            3. Don't split mid-sentence
            4. Preserve context
            """
            
            # Run in thread pool to avoid blocking
            response = await asyncio.get_event_loop().run_in_executor(
                None, self.process, prompt
            )
            
            if "error" in response:
                raise Exception(response["error"])
            
            chunks = []
            start = 0
            
            while start < len(text):
                end = start + self.chunk_size
                
                # Adjust end to not split words
                if end < len(text):
                    end = text.rfind(' ', start, end) + 1
                
                chunk = TextChunk(
                    text=text[start:end],
                    start_idx=start,
                    end_idx=end,
                    metadata=metadata or {}
                )
                chunks.append(chunk)
                
                # Move start position considering overlap
                start = end - self.overlap
            
            # Notify completion
            await self.send_message(
                "document_parser",
                {
                    "action": "chunks_created",
                    "chunks": chunks,
                    "metadata": metadata
                }
            )
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error chunking text: {str(e)}")
            await self.send_message(
                "document_parser",
                {
                    "action": "chunking_failed",
                    "error": str(e),
                    "metadata": metadata
                }
            )
            return []
    
    async def handle_message(self, message: AsyncMessage):
        """Handle incoming messages"""
        try:
            if message.message_type == "chunk_request":
                chunks = await self.chunk_text(
                    message.content["text"],
                    message.content.get("metadata")
                )
                await self.send_message(
                    message.sender,
                    {
                        "action": "chunk_response",
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