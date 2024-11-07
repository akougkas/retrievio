from typing import List, Dict, Optional
import logging
import asyncio
from .base_agent import RetrievIOAgent
from ..config import DEFAULT_COLLECTION

logger = logging.getLogger(__name__)

class VectorStoreAgent(RetrievIOAgent):
    def __init__(self, name: str = "Vector Store"):
        super().__init__(
            name=name,
            role="vector_store",
            instructions="Manage vector storage and retrieval operations"
        )
        self.collection = DEFAULT_COLLECTION
    
    async def store_chunks(self, chunks: List[Dict]) -> bool:
        """Store chunks in vector database"""
        try:
            # Prepare data for ChromaDB
            ids = [f"{chunk.metadata['source_file']}_{chunk.start_idx}" for chunk in chunks]
            embeddings = [chunk.metadata["embedding"] for chunk in chunks]
            texts = [chunk.text for chunk in chunks]
            metadatas = [
                {
                    "source_file": chunk.metadata["source_file"],
                    "start_idx": chunk.start_idx,
                    "end_idx": chunk.end_idx,
                    "file_name": chunk.metadata["file_name"]
                }
                for chunk in chunks
            ]
            
            # Run database operation in thread pool
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.collection.add,
                ids,
                embeddings,
                texts,
                metadatas
            )
            
            logger.info(f"Stored {len(chunks)} chunks in vector database")
            return True
            
        except Exception as e:
            logger.error(f"Error storing chunks: {str(e)}")
            return False
    
    async def search(
        self,
        query: str,
        n_results: int = 5,
        filter_dict: Optional[Dict] = None
    ) -> Dict:
        """Search for similar chunks"""
        try:
            # Run search in thread pool
            results = await asyncio.get_event_loop().run_in_executor(
                None,
                self.collection.query,
                query,
                n_results,
                filter_dict
            )
            
            return {
                "ids": results["ids"][0],
                "documents": results["documents"][0],
                "metadatas": results["metadatas"][0],
                "distances": results["distances"][0]
            }
            
        except Exception as e:
            logger.error(f"Error in similarity search: {str(e)}")
            return {}