from typing import Dict, Any, Optional
import logging
from dataclasses import dataclass
from queue import Queue
import json

logger = logging.getLogger(__name__)

@dataclass
class Message:
    sender: str
    receiver: str
    content: Any
    message_type: str = "data"
    metadata: Optional[Dict] = None

class AgentCommunication:
    def __init__(self):
        self.message_queues: Dict[str, Queue] = {}
        
    def register_agent(self, agent_name: str):
        """Register an agent for communication"""
        if agent_name not in self.message_queues:
            self.message_queues[agent_name] = Queue()
            logger.info(f"Registered agent: {agent_name}")
    
    def send_message(self, message: Message):
        """Send a message to an agent"""
        if message.receiver not in self.message_queues:
            logger.error(f"Unknown receiver: {message.receiver}")
            return False
            
        try:
            self.message_queues[message.receiver].put(message)
            logger.debug(f"Message sent: {message.sender} -> {message.receiver}")
            return True
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            return False
    
    def get_messages(self, agent_name: str) -> list:
        """Get all messages for an agent"""
        if agent_name not in self.message_queues:
            logger.error(f"Unknown agent: {agent_name}")
            return []
            
        messages = []
        queue = self.message_queues[agent_name]
        
        while not queue.empty():
            messages.append(queue.get())
            
        return messages 