#!/usr/bin/env python3
"""
Task Graph Generation Script

This script runs the task graph generation process on bug data inputs.
It uses Google's Gemini 2.5 Pro to generate structured task graphs from bug reports.
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path

# Add the project root to the path to allow importing from modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.generation.working_task_graph_generator import TaskGraphGenerator
from utils.logging_utils import configure_logging

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate task graphs from bug data using Gemini API"
    )
    
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to the input bug data JSON file"
    )
    
    parser.add_argument(
        "--output-dir", "-o",
        default=os.path.join("output", "task_graphs"),
        help="Directory to save generated task graphs"
    )
    
    parser.add_argument(
        "--model", "-m",
        default="gemini-2.5-flash-preview-04-17",
        help="Gemini model to use for generation"
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
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Check for Gemini API key
    if not os.getenv("GEMINI_API_KEY"):
        logger.error("GEMINI_API_KEY environment variable not set")
        logger.info("Please set the GEMINI_API_KEY environment variable to your Google Generative AI API key")
        sys.exit(1)
    
    # Load bug data
    logger.info(f"Loading bug data from: {input_path}")
    try:
        with open(input_path, 'r') as f:
            bug_data = json.load(f)
    except Exception as e:
        logger.error(f"Error loading bug data: {e}")
        sys.exit(1)
    
    # Initialize task graph generator
    try:
        generator = TaskGraphGenerator(
            output_dir=str(output_dir),
            model_name=args.model,
            log_level=log_level
        )
    except Exception as e:
        logger.error(f"Error initializing task graph generator: {e}")
        sys.exit(1)
    
    # Generate task graph
    try:
        logger.info("Generating task graph...")
        task_graph = generator.generate_task_graph(bug_data)
        
        # Get bug ID from the data
        bug_id = bug_data.get('bug_metadata', {}).get('bug_id', 'unknown')
        output_path = output_dir / f"{bug_id}_task_graph.json"
        
        logger.info(f"Task graph generation successful")
        logger.info(f"Output file: {output_path}")
    except Exception as e:
        logger.error(f"Error generating task graph: {e}")
        sys.exit(1)
        
    logger.info("Task graph generation completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())
