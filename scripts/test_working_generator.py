#!/usr/bin/env python3
"""
Test script for the new working task graph generator.
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

from core.generation.working_task_graph_generator import TaskGraphGenerator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_working_generator")

def main():
    """Main function to test the working task graph generator."""
    # Create output directory
    output_dir = Path(os.path.join(project_root, "output", "task_graphs"))
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load test bug data
    test_data_path = Path(os.path.join(project_root, "test_bug_data.json"))
    if not test_data_path.exists():
        logger.error(f"Test data file not found: {test_data_path}")
        return 1
    
    logger.info(f"Loading test data from: {test_data_path}")
    with open(test_data_path, 'r') as f:
        bug_data = json.load(f)
    
    # Initialize the task graph generator with the model from the working example
    logger.info("Initializing TaskGraphGenerator with the working model")
    generator = TaskGraphGenerator(
        model_name="gemini-2.5-flash-preview-04-17",
        output_dir=str(output_dir),
        log_level=logging.INFO
    )
    
    # Generate the task graph
    logger.info("Generating task graph with the working implementation...")
    task_graph = generator.generate_task_graph(bug_data)
    
    # Print summary of the generated task graph
    logger.info("Task graph generation complete")
    logger.info(f"Name: {task_graph.get('name', 'unknown')}")
    logger.info(f"Description: {task_graph.get('description', 'unknown')}")
    
    node_count = len(task_graph.get('task_graph', {}).get('nodes', []))
    edge_count = len(task_graph.get('task_graph', {}).get('edges', []))
    logger.info(f"Node count: {node_count}")
    logger.info(f"Edge count: {edge_count}")
    
    # Check for errors
    if "error" in task_graph:
        logger.error(f"Task graph generation encountered an error: {task_graph['error']}")
        return 1
    
    logger.info("Test completed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
