#!/usr/bin/env python3
"""
Test script for generating task graphs from bug data.

This script tests the task graph generation functionality using the test_bug_data.json
file and the TaskGraphGenerator class.
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add the project root to the path to allow importing from modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the TaskGraphGenerator
from core.generation.working_task_graph_generator import TaskGraphGenerator
from utils.logging_utils import configure_logging
from utils.helpers import validate_api_key, load_json, save_json_file

def main():
    """Main entry point."""
    # Configure logging
    logger = configure_logging(
        log_dir=os.path.join("output", "logs"),
        log_level=logging.INFO
    )
    
    # Define paths
    project_root = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    test_data_path = project_root / "test_bug_data.json"
    output_dir = project_root / "output" / "task_graphs"
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Testing task graph generation with: {test_data_path}")
    
    # Check if test data exists
    if not test_data_path.exists():
        logger.error(f"Test data file not found: {test_data_path}")
        sys.exit(1)
    
    # Load test data
    try:
        with open(str(test_data_path), 'r') as f:
            bug_data = json.load(f)
        logger.info(f"Loaded test data for bug ID: {bug_data.get('bug_metadata', {}).get('bug_id', 'unknown')}")
    except Exception as e:
        logger.error(f"Error loading test data: {e}")
        sys.exit(1)
    
    # Check for Gemini API key
    if not os.getenv("GEMINI_API_KEY"):
        logger.error("GEMINI_API_KEY environment variable not set. Cannot proceed.")
        logger.info("Please set the GEMINI_API_KEY environment variable to your Google Generative AI API key.")
        sys.exit(1)
    
    # Initialize the task graph generator
    try:
        generator = TaskGraphGenerator(
            output_dir=str(output_dir),
            model_name="gemini-2.5-flash-preview-04-17",
            log_level=logging.INFO
        )
        logger.info("Initialized TaskGraphGenerator")
    except Exception as e:
        logger.error(f"Error initializing TaskGraphGenerator: {e}")
        sys.exit(1)
    
    # Generate the task graph
    try:
        logger.info("Generating task graph...")
        task_graph = generator.generate_task_graph(bug_data)
        
        # Save the task graph to a file
        bug_id = bug_data.get('bug_metadata', {}).get('bug_id', 'unknown')
        output_path = output_dir / f"{bug_id}_task_graph.json"
        save_json_file(task_graph, str(output_path))
        
        logger.info(f"Task graph generation successful. Saved to: {output_path}")
        logger.info(f"Task graph contains {len(task_graph.get('task_graph', {}).get('nodes', []))} nodes")
        
    except Exception as e:
        logger.error(f"Error generating task graph: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
