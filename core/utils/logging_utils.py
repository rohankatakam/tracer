"""
Logging Utilities for Bug Reproduction System

This module provides enhanced logging capabilities with features like:
- Log file rotation
- Multi-destination logging (console and file)
- Custom formatting
- Log level control
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Union

# Default log format
DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
DEFAULT_BACKUP_COUNT = 5

class EnhancedLogger:
    """Enhanced logger with file rotation and multi-destination support."""
    
    def __init__(self, 
                name: str, 
                log_dir: Optional[str] = None,
                log_file: Optional[str] = None,
                log_level: int = DEFAULT_LOG_LEVEL,
                log_format: str = DEFAULT_LOG_FORMAT,
                console: bool = True,
                max_bytes: int = DEFAULT_MAX_BYTES,
                backup_count: int = DEFAULT_BACKUP_COUNT):
        """Initialize the enhanced logger.
        
        Args:
            name: Logger name
            log_dir: Directory to store log files. If None, uses 'logs/'
            log_file: Log file name. If None, generates from name.
            log_level: Logging level
            log_format: Format string for log entries
            console: Whether to log to console
            max_bytes: Maximum log file size before rotation
            backup_count: Number of backup files to keep
        """
        self.name = name
        self.log_level = log_level
        
        # Set up logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)
        self.logger.propagate = False  # Don't propagate to root logger
        
        # Create formatter
        self.formatter = logging.Formatter(log_format)
        
        # Clear any existing handlers
        self.logger.handlers = []
        
        # Set up console handler if requested
        if console:
            self._add_console_handler()
        
        # Set up file handler if log_dir is provided
        if log_dir:
            if not log_file:
                log_file = f"{name.lower().replace(' ', '_')}.log"
            
            log_path = Path(log_dir) / log_file
            os.makedirs(log_dir, exist_ok=True)
            
            self._add_file_handler(log_path, max_bytes, backup_count)
    
    def _add_console_handler(self) -> None:
        """Add a console handler to the logger."""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(self.formatter)
        self.logger.addHandler(console_handler)
    
    def _add_file_handler(self, log_path: Path, max_bytes: int, backup_count: int) -> None:
        """Add a file handler with rotation to the logger.
        
        Args:
            log_path: Path to the log file
            max_bytes: Maximum size in bytes before rotation
            backup_count: Number of backup files to keep
        """
        file_handler = RotatingFileHandler(
            log_path, 
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setLevel(self.log_level)
        file_handler.setFormatter(self.formatter)
        self.logger.addHandler(file_handler)
    
    def get_logger(self) -> logging.Logger:
        """Get the configured logger.
        
        Returns:
            The configured logger instance
        """
        return self.logger


def setup_logging(name: str = "cua_system", 
                 log_dir: Optional[str] = None, 
                 log_level: int = DEFAULT_LOG_LEVEL) -> logging.Logger:
    """Set up application-wide logging.
    
    Args:
        name: Base name for the logger
        log_dir: Directory to store log files. If None, uses current directory.
        log_level: Logging level
        
    Returns:
        The configured root logger
    """
    # If log_dir is not specified, create a logs directory
    if not log_dir:
        timestamp = datetime.now().strftime("%Y%m%d")
        log_dir = f"logs/{timestamp}"
    
    # Create the logger
    enhanced_logger = EnhancedLogger(
        name=name,
        log_dir=log_dir,
        log_level=log_level,
        console=True,
        max_bytes=10 * 1024 * 1024,  # 10 MB
        backup_count=5
    )
    
    logger = enhanced_logger.get_logger()
    
    # Log initial message
    logger.info(f"Logging initialized with level {logging.getLevelName(log_level)}")
    logger.info(f"Log files will be stored in: {os.path.abspath(log_dir)}")
    
    return logger


def create_run_logger(run_id: str, base_dir: str = "data") -> logging.Logger:
    """Create a logger for a specific test run.
    
    Args:
        run_id: Unique identifier for the test run
        base_dir: Base directory for test data
        
    Returns:
        Configured logger instance
    """
    log_dir = f"{base_dir}/{run_id}/logs"
    return setup_logging(f"cua_run_{run_id}", log_dir)
