#!/usr/bin/env python3
"""
Computer Use Agent Runner Script

This script runs the Anthropic Computer Use Agent with a provided task graph.
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path

# Add the project root to the path to allow importing from modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.execution.task_graph_executor import TaskGraphExecutor
from core.taskgraph.task_graph import TaskGraph
from utils.logging_utils import configure_logging
from utils.helpers import validate_api_key

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run Computer Use Agent with a task graph"
    )
    
    parser.add_argument(
        "--task-graph", "-t",
        required=True,
        help="Path to the task graph JSON file"
    )
    
    parser.add_argument(
        "--output-dir", "-o",
        default=os.path.join("output", "executions"),
        help="Directory to save execution outputs"
    )
    
    parser.add_argument(
        "--model", "-m",
        default="claude-3-7-sonnet-20250219",
        help="Anthropic model to use"
    )
    
    parser.add_argument(
        "--thinking-budget", "-b",
        type=int,
        default=1024,
        help="Token budget for thinking steps (for 3.7 models)"
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
        log_dir=os.path.join("output", "logs"),
        log_level=log_level
    )
    
    # Validate input file
    task_graph_path = Path(args.task_graph)
    if not task_graph_path.exists():
        logger.error(f"Task graph file not found: {task_graph_path}")
        sys.exit(1)
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Check for Anthropic API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or not validate_api_key(api_key):
        logger.error("Valid ANTHROPIC_API_KEY environment variable not found")
        logger.info("Please set the ANTHROPIC_API_KEY environment variable to your Anthropic API key")
        sys.exit(1)
    
    # Load task graph
    logger.info(f"Loading task graph from: {task_graph_path}")
    try:
        with open(task_graph_path, 'r') as f:
            task_graph_data = json.load(f)
        
        # Create TaskGraph object
        task_graph = TaskGraph(task_graph_data)
    except Exception as e:
        logger.error(f"Error loading task graph: {e}")
        sys.exit(1)
    
    # Initialize task graph executor
    try:
        executor = TaskGraphExecutor(
            output_dir=str(output_dir),
            model=args.model,
            thinking_budget=args.thinking_budget,
            log_level=log_level
        )
    except Exception as e:
        logger.error(f"Error initializing task graph executor: {e}")
        sys.exit(1)
    
    # Execute task graph
    try:
        logger.info("Executing task graph...")
        result = executor.execute_task_graph(task_graph)
        
        # Save execution results
        output_path = output_dir / "execution_result.json"
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Task graph execution completed")
        logger.info(f"Results saved to: {output_path}")
        
        # Log execution metrics
        success = result.get("success", False)
        logger.info(f"Execution status: {'Success' if success else 'Failure'}")
        if not success and "failure_node" in result:
            logger.error(f"Execution failed at node: {result['failure_node'].get('id')}")
    except Exception as e:
        logger.error(f"Error executing task graph: {e}")
        sys.exit(1)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
