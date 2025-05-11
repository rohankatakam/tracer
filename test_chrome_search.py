#!/usr/bin/env python3
"""
Test script for the Chrome search task graph execution

This script tests the Task Graph Execution Loop with a simple browser-based task graph.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

from src.main_controller import execute_task_graph

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_chrome_search():
    """Test the task graph execution with a Chrome browser search task."""
    # Load environment variables
    load_dotenv()
    
    # Ensure Anthropic API key is set
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        logger.error("ANTHROPIC_API_KEY environment variable not set")
        return False
    
    # Path to the simple Chrome task graph
    task_graph_path = "data/task_graphs/chrome_search_task_graph.json"
    
    # Check if the file exists
    if not Path(task_graph_path).exists():
        logger.error(f"Task graph file not found: {task_graph_path}")
        return False
    
    # Execute the task graph
    logger.info(f"Executing Chrome search task graph: {task_graph_path}")
    result = execute_task_graph(
        task_graph_path=task_graph_path,
        output_dir="data/chrome_search_test",
        log_level=logging.INFO
    )
    
    # Log results
    if result["success"]:
        logger.info("Chrome search task completed successfully")
    else:
        logger.warning(f"Chrome search task failed at step: {result.get('failure_step', 'unknown')}")
    
    logger.info(f"Results saved to: {result['output_dir']}")
    return result

if __name__ == "__main__":
    logger.info("Starting Chrome search task test...")
    try:
        result = test_chrome_search()
        if result:
            logger.info("Test completed")
            # Print a summary of the steps executed
            for step in result.get("steps", []):
                status = "✅" if step.get("success", False) else "❌"
                logger.info(f"{status} Step {step.get('step_id')}: {step.get('content', '')[:50]}...")
        else:
            logger.error("Test failed")
    except Exception as e:
        logger.error(f"Error during test: {str(e)}", exc_info=True)
