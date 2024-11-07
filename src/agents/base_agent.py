from swarm import Agent
from typing import Dict, List, Optional, Any
import logging
from ..llm.model_manager import ModelManager, ModelConfig
from ..tools.io_tools import io_fs
from .communication import AgentCommunication, Message
from ..messaging.queue import AsyncMessageQueue, AsyncMessage
import uuid

logger = logging.getLogger(__name__)

class RetrievIOAgent(Agent):
    def __init__(
        self,
        name: str,
        role: str,
        instructions: str,
        tools: List[callable] = None,
        message_queue: Optional[AsyncMessageQueue] = None
    ):
        super().__init__(
            name=name,
            instructions=instructions,
            functions=tools or []
        )
        self.role = role
        self.model_manager = ModelManager()
        self.model_config = self.model_manager.get_model_config(role)
        self.message_queue = message_queue or AsyncMessageQueue()
        self._initialize_messaging()
    
    async def _initialize_messaging(self):
        """Initialize agent messaging"""
        await self.message_queue.register_agent(self.name)
    
    async def send_message(
        self,
        receiver: str,
        content: Any,
        message_type: str = "data",
        metadata: Optional[Dict] = None
    ) -> bool:
        """Send an async message"""
        message = AsyncMessage(
            id=str(uuid.uuid4()),
            sender=self.name,
            receiver=receiver,
            content=content,
            message_type=message_type,
            metadata=metadata
        )
        return await self.message_queue.publish(message)
    
    async def get_messages(self, timeout: Optional[float] = None) -> List[AsyncMessage]:
        """Get all pending messages"""
        return await self.message_queue.get_all_messages(self.name)
    
    async def wait_for_message(self, timeout: Optional[float] = None) -> Optional[AsyncMessage]:
        """Wait for next message"""
        return await self.message_queue.get_message(self.name, timeout)
    
    async def process_messages(self):
        """Process pending messages"""
        messages = await self.get_messages()
        for message in messages:
            await self.handle_message(message)
    
    async def handle_message(self, message: AsyncMessage):
        """Handle a received message"""
        logger.debug(f"{self.name} received message from {message.sender}")
        # Override this in specific agents
        pass