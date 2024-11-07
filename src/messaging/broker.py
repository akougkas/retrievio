import asyncio
from typing import Dict, Set
import logging
from .queue import AsyncMessageQueue, AsyncMessage

logger = logging.getLogger(__name__)

class MessageBroker:
    def __init__(self):
        self.queue = AsyncMessageQueue()
        self.subscriptions: Dict[str, Set[str]] = {}
        self._running = True
        
    async def start(self):
        """Start the message broker"""
        try:
            while self._running:
                # Process messages
                await asyncio.sleep(0.1)  # Prevent CPU hogging
                
        except Exception as e:
            logger.error(f"Broker error: {str(e)}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the message broker"""
        self._running = False
        self.queue.stop()
    
    async def register_agent(self, agent_id: str):
        """Register an agent with the broker"""
        await self.queue.register_agent(agent_id)
    
    async def subscribe(self, subscriber: str, publisher: str):
        """Subscribe to messages from a publisher"""
        if publisher not in self.subscriptions:
            self.subscriptions[publisher] = set()
        self.subscriptions[publisher].add(subscriber)
        await self.queue.subscribe(subscriber, publisher)
    
    async def publish(self, message: AsyncMessage):
        """Publish a message"""
        return await self.queue.publish(message) 