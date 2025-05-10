#!/usr/bin/env python
"""Test script for the Task Graph Generator implementation (Phase 1.3B).

This script tests the generation of task graphs from raw PDF data using Gemini API.
It takes the output of the PDF processor (Phase 1.3A) and uses it to generate
a structured task graph representing the bug reproduction steps.
"""

import os
import sys
import json
import logging
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Add the project root to Python path for imports when run directly
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.utils.logging_utils import setup_logging
from src.utils.json_utils import load_json
from src.ingestion.task_graph_generator import TaskGraphGenerator, generate_task_graph_from_raw_data

# Set up logging
log_dir = os.path.join(project_root, "logs/test")
os.makedirs(log_dir, exist_ok=True)
logger = setup_logging("task_graph_generator_test", log_dir, logging.INFO)

def find_raw_data_packages(directory: str) -> list:
    """Find raw data package JSON files in the directory."""
    raw_data_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower() == 'extraction_result.json':
                raw_data_files.append(os.path.join(root, file))
    return raw_data_files

def run_test(raw_data_path: str = None):
    """Run the Task Graph Generator test.
    
    Args:
        raw_data_path: Path to a raw data package JSON file. If None, will look for
            raw data packages in the test_outputs/pdf directory.
            
    Returns:
        True if the test passed, False otherwise.
    """
    logger.info("Starting Task Graph Generator test")
    
    # Create output directory
    output_dir = os.path.join(project_root, "data/test_outputs/task_graphs")
    os.makedirs(output_dir, exist_ok=True)
    
    # If no raw data package specified, look in test_outputs/pdf directory
    if not raw_data_path:
        test_outputs_dir = os.path.join(project_root, "data/test_outputs/pdf")
        if not os.path.exists(test_outputs_dir):
            logger.error("No test outputs directory found. Please run the PDF processor test first.")
            print("\n❌ FAILED: No PDF processor outputs found in data/test_outputs/pdf.")
            print("Please run the PDF processor test first to generate raw data packages.")
            return False
        
        raw_data_files = find_raw_data_packages(test_outputs_dir)
        if not raw_data_files:
            logger.error("No raw data package files found in test outputs directory.")
            print("\n❌ FAILED: No raw data package files found in data/test_outputs/pdf.")
            print("Please run the PDF processor test first to generate raw data packages.")
            return False
        
        raw_data_path = raw_data_files[0]
        logger.info(f"Found raw data package: {raw_data_path}")
    
    if not os.path.exists(raw_data_path):
        logger.error(f"Raw data package file does not exist: {raw_data_path}")
        print(f"\n❌ FAILED: Raw data package file does not exist: {raw_data_path}")
        return False
    
    try:
        # Check for Gemini API key
        if not os.environ.get("GEMINI_API_KEY"):
            logger.error("GEMINI_API_KEY environment variable not set")
            print("\n❌ FAILED: GEMINI_API_KEY environment variable not set.")
            print("Please set the GEMINI_API_KEY environment variable to your Google Generative AI API key.")
            return False
            
        # Load the raw data package
        logger.info(f"Loading raw data package: {raw_data_path}")
        raw_data_package = load_json(raw_data_path)
        
        # Create Task Graph Generator
        generator = TaskGraphGenerator(output_dir=str(output_dir))
        
        # Generate the task graph
        logger.info("Generating task graph...")
        task_graph = generator.generate_task_graph(raw_data_package)
        
        # Validate the task graph
        if not task_graph or not isinstance(task_graph, dict):
            logger.error("Task graph generation failed: Invalid output format")
            print("\n❌ FAILED: Task graph generation failed: Invalid output format")
            return False
            
        # Check if we have steps in any format
        has_steps = False
        
        # Check for standard task_graph format
        if "task_graph" in task_graph and "nodes" in task_graph["task_graph"] and task_graph["task_graph"]["nodes"]:
            has_steps = True
        
        # Check for direct steps format
        elif "steps" in task_graph and task_graph["steps"]:
            has_steps = True
            # Convert to standard format for display
            steps = task_graph["steps"]
            nodes = []
            for i, step in enumerate(steps):
                nodes.append({
                    "id": str(i+1),
                    "content": step if isinstance(step, str) else str(step),
                    "type": "action"
                })
            
            # Add task_graph structure
            task_graph["task_graph"] = {
                "nodes": nodes,
                "edges": []
            }
            
        # Check for extracted_steps format from pattern matching
        elif "extracted_steps" in task_graph and task_graph["extracted_steps"]:
            has_steps = True
            # Convert to standard format for display
            task_graph["task_graph"] = {
                "nodes": task_graph["extracted_steps"],
                "edges": []
            }
            
        if not has_steps:
            logger.error("Task graph generation failed: No steps found in any format")
            print("\n❌ FAILED: Task graph generation failed: No steps found in any format")
            return False
            
        # Display results
        node_count = len(task_graph["task_graph"]["nodes"])
        edge_count = len(task_graph["task_graph"]["edges"])
        confidence = task_graph.get("confidence_score", 0.0)
        
        print(f"\n✅ SUCCESS: Task graph generator test passed!")
        print(f"Generated task graph for: {raw_data_package.get('name', 'unknown')}")
        print(f"Output directory: {output_dir}")
        print(f"Nodes: {node_count}, Edges: {edge_count}")
        print(f"Confidence score: {confidence:.2f}")
        
        # Print a sample of the task graph nodes
        print("\nTask Graph Nodes Sample:")
        for i, node in enumerate(task_graph["task_graph"]["nodes"][:3]):  # Show only first 3 nodes
            content = node.get("content", "")
            if len(content) > 100:
                content = content[:100] + "..."
            print(f"  {i+1}. {content}")
        
        if node_count > 3:
            print(f"  ... and {node_count - 3} more nodes")
            
        # Check for missing information
        if "missing_information" in task_graph and task_graph["missing_information"]:
            print("\nMissing Information:")
            for item in task_graph["missing_information"][:3]:  # Show only first 3 items
                print(f"  - {item}")
            
            if len(task_graph["missing_information"]) > 3:
                print(f"  ... and {len(task_graph['missing_information']) - 3} more items")
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        
        print("\n❌ FAILED: Task graph generator test failed!")
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    import sys
    
    # Check if a raw data package path was provided as a command-line argument
    raw_data_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    # Run the test
    success = run_test(raw_data_path)
    sys.exit(0 if success else 1)
