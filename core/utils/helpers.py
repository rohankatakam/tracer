"""
Utility functions for the Computer Use Agent system.

This module provides helper functions used throughout the codebase.
"""

import logging
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("computer_use_agent")

def setup_logging(level: int = logging.INFO, log_file: Optional[str] = None):
    """Set up logging configuration.
    
    Args:
        level: Logging level (default: INFO)
        log_file: Optional path to log file
    """
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Configure root logger
    logging.basicConfig(level=level, format=log_format)
    
    # Configure file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(log_format))
        logging.getLogger().addHandler(file_handler)
    
    # Set third-party loggers to WARNING to reduce noise
    logging.getLogger("selenium").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    logger.info("Logging configured")

def ensure_dir_exists(directory_path: str) -> Path:
    """Ensure a directory exists, creating it if necessary.
    
    Args:
        directory_path: Path to directory
    
    Returns:
        Path: Path object for the directory
    """
    path = Path(directory_path)
    path.mkdir(parents=True, exist_ok=True)
    return path

def save_json_file(data: Any, file_path: str, indent: int = 2):
    """Save data to a JSON file.
    
    Args:
        data: Data to save
        file_path: Path to save the file
        indent: JSON indentation level
    """
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=indent)
    except Exception as e:
        logger.error(f"Error saving JSON to {file_path}: {e}")

def load_json_file(file_path: str) -> Dict[str, Any]:
    """Load data from a JSON file.
    
    Args:
        file_path: Path to the JSON file
    
    Returns:
        Dict: Loaded JSON data
    """
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading JSON from {file_path}: {e}")
        return {}

def validate_api_key(api_key: str = None) -> bool:
    """Validate that the Anthropic API key is set and valid.
    
    Args:
        api_key: API key to validate. If None, gets from environment.
        
    Returns:
        bool: True if API key is set and valid, False otherwise
    """
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    if not api_key:
        logger.error("ANTHROPIC_API_KEY environment variable is not set")
        return False
        
    # Check for valid format - this is a simple check
    if not api_key.startswith('sk-ant-'):
        logger.error("ANTHROPIC_API_KEY appears to be invalid format")
        return False
        
    return True
