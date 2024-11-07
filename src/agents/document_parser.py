from typing import Dict, Optional, List
from pathlib import Path
import logging
import asyncio
from .base_agent import RetrievIOAgent
from ..tools.io_tools import io_fs

logger = logging.getLogger(__name__)

class DocumentParserAgent(RetrievIOAgent):
    def __init__(self, name: str = "Document Parser"):
        super().__init__(
            name=name,
            role="document_parser",
            instructions="Extract and structure text content from documents",
            tools=[io_fs]
        )
    
    async def parse_pdf(self, file_path: Path) -> str:
        """Extract text from PDF file"""
        try:
            prompt = f"""Process the PDF file at {file_path} and extract its text content.
            Use the io_fs tool to read the file and extract text.
            Return the extracted text content."""
            
            # Run processing in thread pool to avoid blocking
            response = await asyncio.get_event_loop().run_in_executor(
                None, self.process, prompt
            )
            
            if "error" in response:
                raise Exception(response["error"])
            
            # Use io_fs tool to read PDF in thread pool
            content = await asyncio.get_event_loop().run_in_executor(
                None, io_fs, "read", file_path
            )
            
            if not content:
                logger.error(f"Failed to read PDF {file_path}")
                return ""
                
            return content
            
        except Exception as e:
            logger.error(f"Error parsing PDF {file_path}: {str(e)}")
            return ""
    
    async def chunk_text(self, text: str, metadata: dict = None) -> List[Dict]:
        """Split text into chunks asynchronously"""
        try:
            # Delegate to text chunker agent
            chunks = await self.send_message(
                "text_chunker",
                {
                    "action": "chunk_text",
                    "text": text,
                    "metadata": metadata
                }
            )
            return chunks
            
        except Exception as e:
            logger.error(f"Error chunking text: {str(e)}")
            return []