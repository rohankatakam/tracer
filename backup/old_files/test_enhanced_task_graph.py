#!/usr/bin/env python3
"""
Test script for the enhanced TaskGraphGenerator with comprehensive bug data.

This script tests the enhanced TaskGraphGenerator implementation with the
test bug data that includes metadata, content, attachments, and comments.
"""

import os
import json
import logging
from pathlib import Path

from src.ingestion.task_graph_generator import TaskGraphGenerator

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_enhanced_task_graph_generator():
    """Test the enhanced TaskGraphGenerator with the test bug data."""
    # Load test data
    logger.info("Loading test bug data...")
    with open('test_bug_data.json', 'r') as f:
        bug_data = json.load(f)
    
    # Initialize task graph generator
    logger.info("Initializing TaskGraphGenerator...")
    output_dir = Path("data/test_output")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    generator = TaskGraphGenerator(
        output_dir=str(output_dir),
        log_level=logging.INFO
    )
    
    # Generate task graph
    logger.info("Generating task graph from bug data...")
    task_graph = generator.generate_task_graph(bug_data)
    
    # Log results
    nodes = task_graph.get("task_graph", {}).get("nodes", [])
    edges = task_graph.get("task_graph", {}).get("edges", [])
    logger.info(f"Task graph generated with {len(nodes)} nodes and {len(edges)} edges")
    
    # Print some key information from the task graph
    if nodes:
        logger.info("First few steps in the task graph:")
        for i, node in enumerate(nodes[:3]):
            logger.info(f"Step {i+1}: {node.get('content', '')[:100]}...")
    
    # Save task graph for review
    output_file = output_dir / "enhanced_task_graph_test_result.json"
    with open(output_file, 'w') as f:
        json.dump(task_graph, f, indent=2)
    
    logger.info(f"Task graph saved to: {output_file}")
    return task_graph

if __name__ == "__main__":
    logger.info("Starting test of enhanced TaskGraphGenerator...")
    try:
        task_graph = test_enhanced_task_graph_generator()
        logger.info("Test completed successfully")
    except Exception as e:
        logger.error(f"Error during test: {str(e)}", exc_info=True)
