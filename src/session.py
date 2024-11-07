import asyncio
import logging
from pathlib import Path
from typing import Dict, Optional
from .agents.frontend_agent import FrontendAgent
from .agents.document_watcher import DocumentWatcherAgent
from .agents.document_parser import DocumentParserAgent
from .agents.engagement_agent import EngagementAgent
from .agents.vector_store import VectorStoreAgent
from .agents.qa_agent import QAAgent
from .config import WATCH_DIR
from .actions.handler import Action, ActionHandler
from .messaging.broker import MessageBroker

logger = logging.getLogger(__name__)

class RetrievIOSession:
    def __init__(self):
        """Initialize RetrievIO session"""
        # Initialize message broker
        self.broker = MessageBroker()
        
        # Initialize agents with shared message broker
        self.frontend = FrontendAgent(message_queue=self.broker.queue)
        self.watcher = DocumentWatcherAgent(WATCH_DIR, message_queue=self.broker.queue)
        self.parser = DocumentParserAgent(message_queue=self.broker.queue)
        self.engagement = EngagementAgent(message_queue=self.broker.queue)
        self.vector_store = VectorStoreAgent(message_queue=self.broker.queue)
        self.qa_agent = QAAgent(message_queue=self.broker.queue)
        
        # Set up subscriptions
        self._setup_subscriptions()
        
    async def _setup_subscriptions(self):
        """Set up message subscriptions between agents"""
        subscriptions = [
            (self.parser.name, self.watcher.name),
            (self.vector_store.name, self.parser.name),
            (self.engagement.name, self.vector_store.name),
            (self.qa_agent.name, self.vector_store.name),
            (self.frontend.name, self.engagement.name),
        ]
        
        for subscriber, publisher in subscriptions:
            await self.broker.subscribe(subscriber, publisher)
    
    async def start(self):
        """Start the RetrievIO session"""
        try:
            # Start message broker
            broker_task = asyncio.create_task(self.broker.start())
            
            # Start agents
            await self.watcher.start()
            
            # Start frontend conversation
            await self.frontend.start_conversation()
            
        except Exception as e:
            logger.error(f"Session error: {str(e)}")
        finally:
            await self.cleanup()
    
    async def _handle_document_added(self, document_path: str):
        """Handle new document detection"""
        try:
            # Notify frontend
            await self.frontend.notify_document_added(document_path)
            
            # Create and handle process document action
            action = Action(
                name="process_document",
                input=document_path,
                metadata={"source": "watcher"}
            )
            
            # Process document in background
            asyncio.create_task(self.action_handler.handle_action(action))
            
        except Exception as e:
            logger.error(f"Error handling new document: {str(e)}")
    
    async def _handle_process_document(self, document_path: str, metadata: Optional[Dict] = None) -> Dict:
        """Process document action handler"""
        try:
            # 1. Parse document
            text = await self.parser.parse_pdf(document_path)
            if not text:
                raise Exception(f"Failed to extract text from {document_path}")
            
            # 2. Create metadata
            doc_metadata = {
                "source_file": str(document_path),
                "file_name": Path(document_path).name,
                "creation_time": Path(document_path).stat().st_ctime
            }
            
            # 3. Generate chunks
            chunks = await self.parser.chunk_text(text, doc_metadata)
            
            # 4. Store in vector database
            await self.vector_store.store_chunks(chunks)
            
            # 5. Generate engagement content
            engagement = await self.engagement.analyze_document(text, doc_metadata)
            
            # 6. Move to processed directory
            processed_path = WATCH_DIR / "processed" / Path(document_path).name
            Path(document_path).rename(processed_path)
            
            return {
                "success": True,
                "document": Path(document_path).name,
                "chunks": len(chunks),
                "engagement": engagement
            }
            
        except Exception as e:
            logger.error(f"Document processing error: {str(e)}")
            return {"error": str(e)}
    
    async def _handle_search(self, query: Dict, metadata: Optional[Dict] = None) -> Dict:
        """Handle search action"""
        try:
            results = await self.vector_store.search(
                query=query["text"],
                n_results=query.get("n_results", 5),
                filter_dict=query.get("filter")
            )
            
            return {
                "success": True,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            return {"error": str(e)}
    
    async def _handle_ask(self, question: Dict, metadata: Optional[Dict] = None) -> Dict:
        """Handle question answering action"""
        try:
            # First search for relevant context
            search_results = await self._handle_search(
                {"text": question["text"], "n_results": question.get("n_results", 5)},
                metadata
            )
            
            if "error" in search_results:
                raise Exception(search_results["error"])
            
            # Generate answer
            answer = await self.qa_agent.generate_answer(
                question["text"],
                search_results["results"]
            )
            
            return {
                "success": True,
                "answer": answer
            }
            
        except Exception as e:
            logger.error(f"QA error: {str(e)}")
            return {"error": str(e)}
    
    async def cleanup(self):
        """Clean up resources"""
        try:
            await self.watcher.stop()
            # Add other cleanup tasks as needed
            
        except Exception as e:
            logger.error(f"Cleanup error: {str(e)}")