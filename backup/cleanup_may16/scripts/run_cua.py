#!/usr/bin/env python3
"""
Computer Use Agent Main Runner

This script serves as the main entry point for running the Computer Use Agent
with task graphs. It uses the refactored code structure and provides a clean CLI.
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path

# Add the project root to the path to allow importing from modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# After restructuring, adjust imports to match new structure
from config import settings
from core.agent.anthropic_client import AnthropicClient
from core.taskgraph.task_graph_executor import TaskGraphExecutor
from core.taskgraph.task_graph import TaskGraph
from core.utils.logging_utils import configure_logging
from core.utils.helpers import validate_api_key, load_json_file

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run Computer Use Agent with Task Graphs")
    
    parser.add_argument(
        "--task-graph", "-t",
        type=str,
        default=settings.DEFAULT_TASK_GRAPH_PATH,
        help="Path to task graph JSON file"
    )
    
    parser.add_argument(
        "--model", "-m",
        type=str,
        default=settings.DEFAULT_MODEL,
        help="Anthropic model to use"
    )
    
    parser.add_argument(
        "--output-dir", "-o",
        type=str,
        default=str(settings.OUTPUT_DIR),
        help="Directory for execution outputs"
    )
    
    parser.add_argument(
        "--thinking-budget", "-t",
        type=int,
        default=settings.THINKING_BUDGET,
        help="Token budget for thinking steps"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()

def main():
    """Main entry point."""
    args = parse_args()
    
    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = configure_logging(
        log_dir=os.path.join(args.output_dir, "logs"),
        log_level=log_level
    )
    
    # Validate API key
    if not validate_api_key(settings.ANTHROPIC_API_KEY):
        logger.error("Invalid Anthropic API key. Please check your .env file.")
        sys.exit(1)
    
    # Load task graph
    try:
        task_graph_data = load_json_file(args.task_graph)
        task_graph = TaskGraph(task_graph_data)
    except Exception as e:
        logger.error(f"Error loading task graph: {e}")
        sys.exit(1)
    
    # Initialize task graph executor
    executor = TaskGraphExecutor(
        output_dir=args.output_dir,
        model=args.model,
        thinking_budget=args.thinking_budget,
        log_level=log_level
    )
    
    # Execute task graph
    try:
        logger.info(f"Executing task graph: {args.task_graph}")
        result = executor.execute_task_graph(task_graph)
        
        # Save results
        result_path = os.path.join(args.output_dir, "task_graph_result.json")
        with open(result_path, "w") as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Task graph execution completed. Results saved to {result_path}")
    except Exception as e:
        logger.error(f"Error executing task graph: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
