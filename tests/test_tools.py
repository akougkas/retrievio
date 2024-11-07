import pytest
from pathlib import Path
import json
from src.tools.io_tools import io_fs
from src.agents.base_agent import RetrievIOAgent

def test_io_fs_tool():
    # Create a temporary test file
    test_content = "Test content"
    test_file = Path("test_file.txt")
    
    try:
        # Test write
        io_fs("write", test_file, test_content)
        assert test_file.exists()
        
        # Test read
        content = io_fs("read", test_file)
        assert content == test_content
        
        # Test list
        files = io_fs("list", test_file.parent)
        assert test_file.name in [f.name for f in files]
        
        # Test exists
        assert io_fs("exists", test_file) is True
        
    finally:
        # Cleanup
        test_file.unlink(missing_ok=True)

def test_agent_tool_usage():
    class TestAgent(RetrievIOAgent):
        def __init__(self):
            super().__init__(
                name="Test Agent",
                role="test",
                instructions="Test tool usage",
                tools=[io_fs]
            )
        
        def test_tool(self, content: str) -> bool:
            test_file = Path("test_output.txt")
            try:
                # Use tool through agent
                response = self.process(
                    f"Write '{content}' to {test_file} and then read it back."
                )
                
                # Verify file was written
                assert test_file.exists()
                
                # Read and verify content
                read_content = io_fs("read", test_file)
                return read_content == content
                
            finally:
                test_file.unlink(missing_ok=True)
    
    agent = TestAgent()
    assert agent.test_tool("Test content") is True

def test_tool_error_handling():
    # Test invalid operation
    with pytest.raises(ValueError):
        io_fs("invalid_op", "test.txt")
    
    # Test reading non-existent file
    content = io_fs("read", "nonexistent.txt")
    assert content is None 