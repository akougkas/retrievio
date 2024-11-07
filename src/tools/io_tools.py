from pathlib import Path
from typing import Union, List
import json
import shutil

def io_fs(operation: str, path: Union[str, Path], content: str = None) -> Union[str, List[Path], None]:
    """File system operations tool for agents"""
    path = Path(path)
    
    operations = {
        'read': lambda: path.read_text() if path.exists() else None,
        'write': lambda: path.write_text(content),
        'list': lambda: list(path.glob('*')),
        'exists': lambda: path.exists(),
        'move': lambda: shutil.move(str(path), content)  # content is destination path
    }
    
    if operation not in operations:
        raise ValueError(f"Unsupported operation: {operation}")
        
    return operations[operation]()

def transfer_to(data: dict, destination_agent: str) -> bool:
    """Transfer data between agents"""
    # Simple implementation - will be enhanced in later phases
    try:
        # Convert data to JSON for transfer
        json_data = json.dumps(data)
        print(f"Transferring data to {destination_agent}: {json_data[:100]}...")
        return True
    except Exception as e:
        print(f"Transfer error: {str(e)}")
        return False 