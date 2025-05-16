#!/usr/bin/env python3
"""
Logging utilities for Computer Use Agent.

This module provides enhanced logging capabilities for the Computer Use Agent,
including chat history preservation and structured logging.
"""

import os
import json
import logging
import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

class ChatHistoryLogger:
    """Logger for preserving chat history between agent and user/tools."""
    
    def __init__(self, log_dir: str, session_id: Optional[str] = None):
        """Initialize the chat history logger.
        
        Args:
            log_dir: Directory for storing chat logs
            session_id: Optional session identifier. If None, timestamp will be used
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.session_id = session_id or datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.chat_log_file = self.log_dir / f"chat_history_{self.session_id}.jsonl"
        self.logger = logging.getLogger(f"chat_history.{self.session_id}")
    
    def log_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Log a chat message.
        
        Args:
            role: Role of the message sender (e.g., "user", "assistant", "tool")
            content: Content of the message
            metadata: Optional metadata for the message
        """
        message = {
            "timestamp": datetime.datetime.now().isoformat(),
            "role": role,
            "content": content
        }
        
        if metadata:
            message["metadata"] = metadata
            
        with open(self.chat_log_file, "a") as f:
            f.write(json.dumps(message) + "\n")
        
        self.logger.debug(f"Logged {role} message: {content[:50]}...")
    
    def get_chat_history(self, max_messages: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get the chat history.
        
        Args:
            max_messages: Maximum number of messages to return (from most recent)
            
        Returns:
            List of chat messages
        """
        if not self.chat_log_file.exists():
            return []
            
        with open(self.chat_log_file, "r") as f:
            messages = [json.loads(line) for line in f]
        
        if max_messages is not None:
            messages = messages[-max_messages:]
            
        return messages


def configure_logging(
    log_dir: str,
    log_level: int = logging.INFO,
    format_str: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
) -> logging.Logger:
    """Configure logging for the application.
    
    Args:
        log_dir: Directory for storing logs
        log_level: Logging level
        format_str: Log message format
        
    Returns:
        Root logger
    """
    log_dir_path = Path(log_dir)
    log_dir_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir_path / f"cua_{timestamp}.log"
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=format_str,
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    return logger
