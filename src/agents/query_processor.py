from typing import Dict, List
import logging
import asyncio
from .base_agent import RetrievIOAgent
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class QueryProcessorAgent(RetrievIOAgent):
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", name: str = "Query Processor"):
        super().__init__(
            name=name,
            role="query_processor",
            instructions="Process and embed search queries"
        )
        self.model = SentenceTransformer(model_name)
    
    async def process_query(self, query: str) -> Dict:
        """Process and embed a search query"""
        try:
            # Generate embedding in thread pool
            embedding = await asyncio.get_event_loop().run_in_executor(
                None,
                self.model.encode,
                query,
                True  # normalize_embeddings
            )
            
            result = {
                "query": query,
                "embedding": embedding.tolist(),
            }
            
            # Notify completion
            await self.send_message(
                "vector_store",
                {
                    "action": "query_processed",
                    "result": result
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            await self.send_message(
                "vector_store",
                {
                    "action": "query_failed",
                    "error": str(e)
                }
            )
            raise
    
    async def format_results(self, results: Dict, query: str) -> List[Dict]:
        """Format search results for display"""
        formatted_results = []
        
        for i, (doc, metadata, distance) in enumerate(zip(
            results["documents"],
            results["metadatas"],
            results["distances"]
        )):
            formatted_results.append({
                "rank": i + 1,
                "text": doc,
                "file": metadata["file_name"],
                "relevance": round((1 - distance) * 100, 2),
                "metadata": metadata
            })
        
        # Notify formatting complete
        await self.send_message(
            "frontend",
            {
                "action": "results_formatted",
                "results": formatted_results,
                "query": query
            }
        )
        
        return formatted_results
    
    async def handle_message(self, message: AsyncMessage):
        """Handle incoming messages"""
        try:
            if message.message_type == "process_query":
                result = await self.process_query(message.content["query"])
                await self.send_message(
                    message.sender,
                    {
                        "action": "query_response",
                        "result": result,
                        "request_id": message.id
                    }
                )
            elif message.message_type == "format_results":
                formatted = await self.format_results(
                    message.content["results"],
                    message.content["query"]
                )
                await self.send_message(
                    message.sender,
                    {
                        "action": "format_response",
                        "results": formatted,
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