from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path
import asyncio
import logging
from .base_agent import RetrievIOAgent

logger = logging.getLogger(__name__)

class AsyncDocumentEventHandler(FileSystemEventHandler):
    def __init__(self, agent):
        self.agent = agent
        self.loop = asyncio.get_event_loop()
        super().__init__()

    def on_created(self, event):
        if event.is_directory:
            return
        if Path(event.src_path).suffix.lower() == '.pdf':
            asyncio.run_coroutine_threadsafe(
                self.agent.handle_new_document(event.src_path),
                self.loop
            )

class DocumentWatcherAgent(RetrievIOAgent):
    def __init__(self, watch_dir: str, name: str = "Document Watcher"):
        super().__init__(
            name=name,
            role="watcher",
            instructions="Monitor directory for new PDF documents and trigger processing"
        )
        self.watch_dir = watch_dir
        self.event_handler = AsyncDocumentEventHandler(self)
        self.observer = Observer()
        
    async def start(self):
        """Start monitoring the directory"""
        self.observer.schedule(self.event_handler, self.watch_dir, recursive=False)
        self.observer.start()
        logger.info(f"Started watching directory: {self.watch_dir}")
        
    async def stop(self):
        """Stop monitoring the directory"""
        self.observer.stop()
        self.observer.join()
        logger.info("Stopped watching directory")
        
    async def handle_new_document(self, file_path: str):
        """Handle new document detection"""
        logger.info(f"New document detected: {file_path}")
        # This will be overridden by the session manager
        pass