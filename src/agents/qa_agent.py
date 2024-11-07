from typing import Dict, List
import logging
import asyncio
from .base_agent import RetrievIOAgent

logger = logging.getLogger(__name__)

class QAAgent(RetrievIOAgent):
    def __init__(self, name: str = "QA Agent"):
        super().__init__(
            name=name,
            role="qa",
            instructions="Answer questions based on retrieved context"
        )
    
    def format_context(self, results: List[Dict]) -> str:
        """Format search results into context"""
        context = "\n\nRelevant passages:\n"
        for result in results:
            context += f"\n[From: {result['file']}]\n{result['text']}\n"
        return context
    
    async def generate_answer(self, query: str, results: List[Dict]) -> Dict:
        """Generate answer based on search results"""
        try:
            context = self.format_context(results)
            
            prompt = f"""Based on the following context, answer the question.
            Question: {query}
            
            {context}
            
            Answer the question using ONLY the information provided above."""
            
            # Run model inference in thread pool
            response = await asyncio.get_event_loop().run_in_executor(
                None, self.process, prompt
            )
            
            if "error" in response:
                raise Exception(response["error"])
            
            return {
                "answer": response["content"],
                "model": response["model"],
                "sources": [r["file"] for r in results],
                "usage": response["usage"]
            }
            
        except Exception as e:
            logger.error(f"Failed to generate answer: {str(e)}")
            return {
                "error": str(e),
                "sources": [r["file"] for r in results]
            } 