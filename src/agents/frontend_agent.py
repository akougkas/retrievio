import asyncio
import logging
from typing import Optional, Dict
from .base_agent import RetrievIOAgent
from ..config import WATCH_DIR, ModelConfig
from pathlib import Path
from ..actions.handler import Action, ActionHandler

logger = logging.getLogger(__name__)

class FrontendAgent(RetrievIOAgent):
    def __init__(self, name: str = "Granite3-MOE"):
        super().__init__(
            name=name,
            role="frontend",
            instructions="""You are Granite3-MOE, the friendly interface to RetrievIO.
            Guide users through document management and information retrieval using natural conversation.
            Always maintain a helpful and informative tone."""
        )
        self.workspace: Optional[str] = None
        self.conversation_active = False
        self.action_handler = ActionHandler()
        
    async def start_conversation(self):
        """Start the interactive session"""
        self.conversation_active = True
        
        # Initial greeting
        welcome_prompt = """
        Welcome to RetrievIO! I'm Granite3-MOE, your document assistant.
        I'll help you manage and query your documents effectively.
        
        First, I'll need a workspace to monitor. Where should I look for documents?
        """
        
        print(welcome_prompt)
        
        while self.conversation_active:
            try:
                user_input = await asyncio.get_event_loop().run_in_executor(
                    None, input, "\nYou: "
                )
                
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    await self.handle_exit()
                    break
                
                await self.process_input(user_input)
                
            except KeyboardInterrupt:
                await self.handle_exit()
                break
            except Exception as e:
                logger.error(f"Error in conversation: {str(e)}")
                print("\nI encountered an error. Please try again.")
    
    async def process_input(self, user_input: str):
        """Process user input and generate response"""
        try:
            if not self.workspace:
                await self.handle_workspace_setup(user_input)
                return
            
            # Process the input
            prompt = f"""User input: {user_input}
            Current workspace: {self.workspace}
            
            Respond naturally and determine if this is:
            1. A question about documents
            2. A request for document processing
            3. A system configuration request
            4. General conversation
            
            Format response in a conversational way."""
            
            response = self.process(prompt)
            
            if "error" in response:
                print("\nI'm having trouble understanding. Could you rephrase that?")
                return
            
            print(f"\n{self.name}: {response['content']}")
            
            # Handle any required actions based on input
            await self.handle_actions(user_input, response)
            
        except Exception as e:
            logger.error(f"Error processing input: {str(e)}")
            print("\nI'm sorry, I couldn't process that properly. Please try again.")
    
    async def handle_workspace_setup(self, path: str):
        """Handle workspace initialization"""
        try:
            # Validate and set up workspace
            workspace_path = Path(path).expanduser().resolve()
            
            if not workspace_path.exists():
                print(f"\n{self.name}: That path doesn't exist. Should I create it for you? (yes/no)")
                create = await asyncio.get_event_loop().run_in_executor(None, input)
                
                if create.lower() == 'yes':
                    workspace_path.mkdir(parents=True)
                else:
                    print(f"\n{self.name}: Please provide a valid path to your workspace.")
                    return
            
            self.workspace = str(workspace_path)
            
            # Notify other agents
            self.send_message(
                "document_watcher",
                {"action": "set_workspace", "path": self.workspace}
            )
            
            print(f"\n{self.name}: Perfect! I'm now watching {self.workspace} for documents.")
            print("You can add PDFs anytime and I'll process them automatically.")
            print("What would you like to know about your documents?")
            
        except Exception as e:
            logger.error(f"Error setting up workspace: {str(e)}")
            print(f"\n{self.name}: I couldn't set up that workspace. Please try again.")
    
    async def handle_actions(self, user_input: str, response: Dict):
        """Handle any actions needed based on user input"""
        try:
            # Extract action from response
            if "content" not in response:
                return
                
            # Parse response for action requests
            content = response["content"].lower()
            
            if "set workspace" in content or "workspace" in content and not self.workspace:
                # Handle workspace setup
                action = Action(
                    name="set_workspace",
                    input=user_input,
                    metadata={"source": "user_input"}
                )
                result = await self.action_handler.handle_action(action)
                
                if result["success"]:
                    self.workspace = result["result"]["path"]
                    
            elif "search" in content or "find" in content:
                # Handle search request
                action = Action(
                    name="search",
                    input=user_input,
                    metadata={"workspace": self.workspace}
                )
                result = await self.action_handler.handle_action(action)
                
                if result["success"]:
                    self._display_search_results(result["result"])
                    
            elif "question" in content or "ask" in content:
                # Handle question
                action = Action(
                    name="ask",
                    input=user_input,
                    metadata={"workspace": self.workspace}
                )
                result = await self.action_handler.handle_action(action)
                
                if result["success"]:
                    self._display_answer(result["result"])
                    
        except Exception as e:
            logger.error(f"Error handling actions: {str(e)}")
    
    def _display_search_results(self, results: Dict):
        """Display search results to user"""
        if not results.get("matches"):
            print("\nNo relevant results found.")
            return
            
        print("\nHere's what I found:")
        for i, match in enumerate(results["matches"], 1):
            print(f"\n{i}. From: {match['source']}")
            print("-" * 40)
            print(match["text"])
    
    def _display_answer(self, result: Dict):
        """Display answer to user"""
        if "error" in result:
            print("\nI'm sorry, I couldn't find an answer to that question.")
            return
            
        print(f"\nBased on your documents:")
        print("-" * 40)
        print(result["answer"])
        
        if result.get("sources"):
            print("\nSources:")
            for source in result["sources"]:
                print(f"- {source}")
    
    async def handle_exit(self):
        """Handle cleanup when exiting"""
        self.conversation_active = False
        print(f"\n{self.name}: Goodbye! Feel free to return anytime.")
        
    async def notify_document_added(self, document_path: str):
        """Notify user about new document detection"""
        print(f"\n{self.name}: I notice you've added '{Path(document_path).name}'.")
        print("I'm processing that now. Feel free to continue our conversation!") 