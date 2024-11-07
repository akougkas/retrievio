import logging
from typing import Dict, Any, Optional, Callable
from pathlib import Path
import asyncio
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class Action:
    name: str
    input: Any
    metadata: Optional[Dict] = None

class ActionHandler:
    def __init__(self):
        self.actions = {}
        self._register_default_actions()
    
    def _register_default_actions(self):
        """Register default system actions"""
        self.register_action("set_workspace", self._handle_set_workspace)
        self.register_action("process_document", self._handle_process_document)
        self.register_action("search", self._handle_search)
        self.register_action("ask", self._handle_ask)
        
    def register_action(self, action_name: str, handler: Callable):
        """Register a new action handler"""
        self.actions[action_name] = handler
        logger.debug(f"Registered action handler: {action_name}")
    
    async def handle_action(self, action: Action) -> Dict:
        """Handle an action request"""
        try:
            if action.name not in self.actions:
                raise ValueError(f"Unknown action: {action.name}")
                
            handler = self.actions[action.name]
            result = await handler(action.input, action.metadata)
            
            return {
                "success": True,
                "action": action.name,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Action handling error: {str(e)}")
            return {
                "success": False,
                "action": action.name,
                "error": str(e)
            }
    
    async def _handle_set_workspace(self, path: str, metadata: Optional[Dict] = None) -> Dict:
        """Handle workspace setup"""
        workspace_path = Path(path).expanduser().resolve()
        
        if not workspace_path.exists():
            workspace_path.mkdir(parents=True)
            
        return {
            "path": str(workspace_path),
            "exists": True
        }
    
    async def _handle_process_document(self, file_path: str, metadata: Optional[Dict] = None) -> Dict:
        """Handle document processing request"""
        # This will be implemented by the session manager
        pass
    
    async def _handle_search(self, query: Dict, metadata: Optional[Dict] = None) -> Dict:
        """Handle search request"""
        # This will be implemented by the session manager
        pass
    
    async def _handle_ask(self, question: Dict, metadata: Optional[Dict] = None) -> Dict:
        """Handle question answering request"""
        # This will be implemented by the session manager
        pass 