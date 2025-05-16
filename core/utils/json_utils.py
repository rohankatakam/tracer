"""
JSON Utilities for Bug Reproduction System

This module provides utilities for JSON serialization,
including custom encoders to handle non-serializable objects.
"""

import json
import dataclasses
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle non-serializable objects.
    
    This encoder handles:
    - Dataclasses
    - Pydantic models
    - Datetime objects
    - Objects with a to_dict() or dict() method
    """
    
    def default(self, obj: Any) -> Any:
        """Implement custom encoding for non-serializable objects.
        
        Args:
            obj: The object to encode
            
        Returns:
            A JSON-serializable version of the object
        """
        # Handle Anthropic Message objects
        if hasattr(obj, 'model') and hasattr(obj, 'type'):
            # This is likely an Anthropic API object
            # First try to convert by extracting attributes into a dict
            try:
                serializable_dict = {}
                for key, value in obj.__dict__.items():
                    if not key.startswith('_'):  # Skip private attributes
                        serializable_dict[key] = value
                return serializable_dict
            except:
                # Fall back to string representation
                return str(obj)
        
        # Handle dataclasses
        if dataclasses.is_dataclass(obj):
            return dataclasses.asdict(obj)
        
        # Handle datetime objects
        if isinstance(obj, datetime):
            return obj.isoformat()
        
        # Handle Pydantic models
        if hasattr(obj, 'model_dump') and callable(obj.model_dump):
            return obj.model_dump()
        
        # Handle objects with to_dict method
        if hasattr(obj, 'to_dict') and callable(obj.to_dict):
            return obj.to_dict()
        
        # Handle objects with dict method
        if hasattr(obj, 'dict') and callable(obj.dict):
            return obj.dict()
        
        # Fall back to string representation for other objects
        try:
            return str(obj)
        except:
            return f"<Object of type {type(obj).__name__} that cannot be serialized>"


def serialize_json(obj: Any, pretty: bool = True) -> str:
    """Serialize an object to a JSON string.
    
    Args:
        obj: The object to serialize
        pretty: Whether to pretty-print the JSON
        
    Returns:
        JSON string representation of the object
    """
    indent = 2 if pretty else None
    return json.dumps(obj, cls=CustomJSONEncoder, indent=indent)


def save_json(obj: Any, filepath: str, pretty: bool = True) -> None:
    """Save an object to a JSON file.
    
    Args:
        obj: The object to serialize
        filepath: Path to the output file
        pretty: Whether to pretty-print the JSON
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(obj, f, cls=CustomJSONEncoder, indent=2 if pretty else None)


def load_json(filepath: str) -> Any:
    """Load an object from a JSON file.
    
    Args:
        filepath: Path to the JSON file
        
    Returns:
        Deserialized object
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)
