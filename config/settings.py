#!/usr/bin/env python3
"""
Configuration settings for Computer Use Agent.

This module contains global configuration settings for the Computer Use Agent,
including paths, model settings, and execution parameters.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Base paths
BASE_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# API settings
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

# Model settings
DEFAULT_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-7-sonnet-20250219")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4096"))
THINKING_BUDGET = int(os.getenv("THINKING_BUDGET", "1024"))

# Task Graph settings
DEFAULT_TASK_GRAPH_PATH = os.getenv("TASK_GRAPH_PATH", str(BASE_DIR / "task_graph.json"))

# Computer Use Agent settings
DISPLAY_WIDTH = int(os.getenv("DISPLAY_WIDTH", "1280"))
DISPLAY_HEIGHT = int(os.getenv("DISPLAY_HEIGHT", "800"))
DISPLAY_NUMBER = os.getenv("DISPLAY_NUMBER")  # This might be None if not set

# Execution settings
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "10"))
REQUEST_DELAY = float(os.getenv("REQUEST_DELAY", "3.0"))
