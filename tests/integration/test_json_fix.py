#!/usr/bin/env python
"""
Test script to verify that the JSON serialization fixes work correctly.
This script runs a small test using the main components of our system
to ensure that the custom JSON encoder properly handles Anthropic API objects.
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add the project root to Python path for imports when run directly
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.utils.logging_utils import setup_logging
from src.utils.json_utils import save_json
from src.main_controller import ComputerUseController
from src.test_framework.test_runner import TestRunner

# Set up logging
log_dir = os.path.join(project_root, "logs/test")
os.makedirs(log_dir, exist_ok=True)
logger = setup_logging("json_fix_test", log_dir, logging.INFO)

def create_simple_test_case():
    """Create a simple test case for testing."""
    return {
        "name": "json_serialization_test",
        "description": "Test case to verify JSON serialization",
        "steps": [
            {
                "name": "Simple text prompt",
                "prompt": "Hello, please describe what you can do with Computer Use Actions",
                "validation": {
                    "type": "text_content", 
                    "params": {"text": "action"}
                }
            }
        ]
    }

def run_test():
    """Run the test to verify JSON serialization fixes."""
    logger.info("Starting JSON serialization test")
    
    # Create a test directory
    test_dir = os.path.join(project_root, "data/test_outputs/json_fix_test")
    os.makedirs(test_dir, exist_ok=True)
    
    # Create a test case
    test_case = create_simple_test_case()
    
    # Save the test case
    test_case_path = test_dir / "test_case.json"
    save_json(test_case, str(test_case_path))
    logger.info(f"Saved test case to {test_case_path}")
    
    # Create a test runner
    runner = TestRunner(output_dir=str(test_dir), log_level=logging.INFO)
    
    try:
        # Run the test case
        logger.info("Running test case...")
        results = runner.run_test_case(test_case)
        
        # Save the results - this is where we previously had issues
        results_path = test_dir / "results.json"
        save_json(results, str(results_path))
        logger.info(f"Successfully saved results to {results_path}")
        
        print("\n✅ SUCCESS: JSON serialization test passed!")
        print(f"Results saved to: {results_path}")
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        
        print("\n❌ FAILED: JSON serialization test failed!")
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)
