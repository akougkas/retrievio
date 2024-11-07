from pathlib import Path
import logging
from typing import Optional, List, Dict
from dataclasses import asdict
import uuid
import json

from .agents.document_watcher import DocumentWatcherAgent
from .agents.document_parser import DocumentParserAgent
from .agents.text_chunker import TextChunkerAgent
from .agents.embedder import EmbedderAgent
from .agents.vector_store import VectorStoreAgent
from .agents.qa_agent import QAAgent
from .agents.engagement_agent import EngagementAgent
from .flow.coordinator import FlowCoordinator
from .config import WATCH_DIR, PROCESSED_DIR, CHUNK_SIZE, CHUNK_OVERLAP

logger = logging.getLogger(__name__)

class DocumentPipeline:
    def __init__(self):
        self.coordinator = FlowCoordinator()
        
        # Initialize agents
        self.watcher = DocumentWatcherAgent(WATCH_DIR)
        self.parser = DocumentParserAgent()
        self.chunker = TextChunkerAgent(CHUNK_SIZE, CHUNK_OVERLAP)
        self.embedder = EmbedderAgent()
        self.vector_store = VectorStoreAgent()
        self.qa_agent = QAAgent()
        self.engagement_agent = EngagementAgent()
        
        # Override watcher's handle_new_document method
        self.watcher.handle_new_document = self.process_document
        
    def process_document(self, file_path: str) -> bool:
        """Process a single document through the pipeline"""
        try:
            flow_id = str(uuid.uuid4())
            file_path = Path(file_path)
            self.coordinator.start_flow(flow_id, str(file_path))
            
            logger.info(f"Starting flow {flow_id} for document: {file_path}")
            
            # 1. Parse document
            self.parser.send_message(
                "document_watcher",
                {"flow_id": flow_id, "status": "parsing_started"}
            )
            
            text = self.parser.parse_pdf(file_path)
            if not text:
                logger.error(f"Failed to extract text from {file_path}")
                return False
            
            self.coordinator.update_flow(flow_id, "parsed", "parsing")
            
            # 2. Create metadata
            metadata = {
                "source_file": str(file_path),
                "file_name": file_path.name,
                "creation_time": file_path.stat().st_ctime,
                "flow_id": flow_id
            }
            
            # 3. Chunk text
            self.chunker.send_message(
                "document_parser",
                {"flow_id": flow_id, "status": "chunking_started"}
            )
            
            chunks = self.chunker.chunk_text(text, metadata)
            logger.info(f"Created {len(chunks)} chunks from {file_path.name}")
            
            self.coordinator.update_flow(flow_id, "chunked", "chunking")
            
            # 4. Generate embeddings
            self.embedder.send_message(
                "text_chunker",
                {"flow_id": flow_id, "status": "embedding_started"}
            )
            
            chunks_with_embeddings = self.embedder.embed_chunks(chunks)
            
            self.coordinator.update_flow(flow_id, "embedded", "embedding")
            
            # 5. Store in vector database
            self.vector_store.send_message(
                "embedder",
                {"flow_id": flow_id, "status": "storing_started"}
            )
            
            if not self.vector_store.store_chunks(chunks_with_embeddings):
                logger.error(f"Failed to store chunks for {file_path.name}")
                return False
            
            self.coordinator.update_flow(flow_id, "stored", "storing")
            
            # 6. Generate engagement content
            self.engagement_agent.send_message(
                "vector_store",
                {
                    "flow_id": flow_id,
                    "status": "analyzing",
                    "document": file_path.name
                }
            )
            
            # Combine chunks for analysis
            full_text = "\n".join(chunk.text for chunk in chunks_with_embeddings)
            engagement = self.engagement_agent.analyze_document(
                full_text,
                metadata
            )
            
            if "error" not in engagement:
                logger.info(f"Generated engagement content for {file_path.name}")
                self._save_engagement(file_path.stem, engagement)
            
            # 7. Move processed file and save chunks
            processed_path = PROCESSED_DIR / file_path.name
            file_path.rename(processed_path)
            self._save_chunks(file_path.stem, chunks_with_embeddings)
            
            logger.info(f"Completed flow {flow_id} for {file_path.name}")
            logger.info(f"Engagement suggestions: {engagement}")
            
            return True
            
        except Exception as e:
            logger.exception(f"Error in flow {flow_id}: {str(e)}")
            return False
    
    def _save_engagement(self, document_id: str, engagement: Dict):
        """Save engagement content"""
        engagement_file = PROCESSED_DIR / document_id / "engagement.json"
        engagement_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(engagement_file, 'w') as f:
            json.dump(engagement, f, indent=2)
    
    def start(self):
        """Start the document processing pipeline"""
        logger.info("Starting RetrievIO document processing pipeline")
        self.watcher.start()
        
    def stop(self):
        """Stop the document processing pipeline"""
        logger.info("Stopping RetrievIO document processing pipeline")
        self.watcher.stop()
    
    def _save_chunks(self, document_id: str, chunks: list) -> None:
        """Save chunks to processed directory"""
        chunk_dir = PROCESSED_DIR / document_id / "chunks"
        chunk_dir.mkdir(parents=True, exist_ok=True)
        
        for i, chunk in enumerate(chunks):
            chunk_file = chunk_dir / f"chunk_{i:04d}.json"
            with open(chunk_file, 'w') as f:
                json.dump(asdict(chunk), f, indent=2)