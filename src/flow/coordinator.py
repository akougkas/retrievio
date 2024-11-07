import logging
from typing import Dict, List, Optional
from pathlib import Path
from ..agents.communication import AgentCommunication, Message
from ..config import WATCH_DIR

logger = logging.getLogger(__name__)

class FlowCoordinator:
    def __init__(self):
        self.comm = AgentCommunication()
        self.active_flows = {}
        
    def start_flow(self, flow_id: str, document_path: str):
        """Start a new document processing flow"""
        self.active_flows[flow_id] = {
            "status": "started",
            "document": document_path,
            "steps_completed": [],
            "current_step": "parsing"
        }
        
    def update_flow(self, flow_id: str, status: str, step: str):
        """Update flow status"""
        if flow_id in self.active_flows:
            self.active_flows[flow_id]["status"] = status
            self.active_flows[flow_id]["steps_completed"].append(step)
            logger.info(f"Flow {flow_id}: Completed {step}")
    
    def get_flow_status(self, flow_id: str) -> Dict:
        """Get current flow status"""
        return self.active_flows.get(flow_id, {}) 