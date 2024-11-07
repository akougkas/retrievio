from typing import List, Dict, Optional
import logging
from .agents.query_processor import QueryProcessorAgent
from .agents.vector_store import VectorStoreAgent
from .agents.qa_agent import QAAgent

logger = logging.getLogger(__name__)

class SearchManager:
    def __init__(self):
        self.query_processor = QueryProcessorAgent()
        self.vector_store = VectorStoreAgent()
        self.qa_agent = QAAgent()
        
    def search(
        self,
        query: str,
        n_results: int = 5,
        min_relevance: float = 0.7,
        file_filter: Optional[str] = None
    ) -> List[Dict]:
        """Execute a search query and return formatted results"""
        try:
            # Process query
            processed_query = self.query_processor.process_query(query)
            
            # Prepare filter
            filter_dict = {"file_name": {"$eq": file_filter}} if file_filter else None
            
            # Search vector store
            results = self.vector_store.similarity_search(
                query_embedding=processed_query["embedding"],
                n_results=n_results,
                filter_dict=filter_dict
            )
            
            # Format results
            formatted_results = self.query_processor.format_results(results, query)
            
            # Filter by relevance
            filtered_results = [
                r for r in formatted_results
                if r["relevance"] / 100 >= min_relevance
            ]
            
            return filtered_results
            
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            return [] 
    
    def ask(
        self,
        question: str,
        n_results: int = 5,
        min_relevance: float = 0.7,
        file_filter: Optional[str] = None
    ) -> Dict:
        """Ask a question and get an answer based on document context"""
        try:
            # First search for relevant context
            search_results = self.search(
                query=question,
                n_results=n_results,
                min_relevance=min_relevance,
                file_filter=file_filter
            )
            
            if not search_results:
                return {
                    "answer": "I could not find any relevant information to answer your question.",
                    "sources": []
                }
            
            # Generate answer
            answer = self.qa_agent.generate_answer(question, search_results)
            return answer
            
        except Exception as e:
            logger.error(f"Error in QA: {str(e)}")
            return {"error": str(e)}