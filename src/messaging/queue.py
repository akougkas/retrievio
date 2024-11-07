import asyncio
from typing import Dict, Any, Optional, List
from collections import defaultdict
import logging
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)

@dataclass
class AsyncMessage:
    id: str
    sender: str
    receiver: str
    content: Any
    message_type: str = "data"
    metadata: Optional[Dict] = None

class AsyncMessageQueue:
    def __init__(self):
        self.queues: Dict[str, asyncio.Queue] = defaultdict(asyncio.Queue)
        self.subscribers: Dict[str, List[str]] = defaultdict(list)
        self._running = True
    
    async def register_agent(self, agent_id: str):
        """Register an agent for messaging"""
        if agent_id not in self.queues:
            self.queues[agent_id] = asyncio.Queue()
            logger.info(f"Registered agent: {agent_id}")
    
    async def subscribe(self, subscriber: str, publisher: str):
        """Subscribe to messages from a specific publisher"""
        if subscriber not in self.subscribers[publisher]:
            self.subscribers[publisher].append(subscriber)
            logger.debug(f"{subscriber} subscribed to {publisher}")
    
    async def publish(self, message: AsyncMessage):
        """Publish a message to all subscribers"""
        try:
            # Get all subscribers for this sender
            receivers = self.subscribers.get(message.sender, [])
            if message.receiver:
                receivers.append(message.receiver)
            
            # Put message in each subscriber's queue
            tasks = []
            for receiver in receivers:
                if receiver in self.queues:
                    task = asyncio.create_task(
                        self.queues[receiver].put(message)
                    )
                    tasks.append(task)
            
            if tasks:
                await asyncio.gather(*tasks)
                logger.debug(f"Message from {message.sender} published to {len(tasks)} receivers")
            
            return True
            
        except Exception as e:
            logger.error(f"Error publishing message: {str(e)}")
            return False
    
    async def get_message(self, agent_id: str, timeout: Optional[float] = None) -> Optional[AsyncMessage]:
        """Get next message for an agent"""
        try:
            if agent_id not in self.queues:
                return None
                
            if timeout:
                try:
                    message = await asyncio.wait_for(
                        self.queues[agent_id].get(),
                        timeout=timeout
                    )
                except asyncio.TimeoutError:
                    return None
            else:
                message = await self.queues[agent_id].get()
                
            return message
            
        except Exception as e:
            logger.error(f"Error getting message: {str(e)}")
            return None
    
    async def get_all_messages(self, agent_id: str) -> List[AsyncMessage]:
        """Get all pending messages for an agent"""
        messages = []
        while not self.queues[agent_id].empty():
            message = await self.get_message(agent_id)
            if message:
                messages.append(message)
        return messages
    
    def stop(self):
        """Stop the message queue"""
        self._running = False 