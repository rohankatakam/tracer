#!/usr/bin/env python3
"""
Test script for Gemini bug reproduction graph generator.

This script tests the reorganized Gemini bug reproduction generator by processing
a sample GitHub issue JSON file.
"""

import os
import sys
import json
from pathlib import Path

# Import the generator from our new structure
from core.gemini.bug_reproduction.generator import generate_bug_reproduction_graph

def test_gemini_bug_reproduction():
    """
    Test the Gemini bug reproduction graph generator with a sample GitHub issue.
    """
    # Locate test files
    base_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    
    # Sample GitHub issue file (pick an existing one from the data/ directory)
    github_issue_file = base_dir / "data" / "github_issue_1101_full.json"
    
    # Schema, system instruction, and prompt template files
    schema_file = base_dir / "core" / "gemini" / "schemas" / "bug_reproduction_graph_schema_v3.json"
    system_instruction_file = base_dir / "core" / "gemini" / "templates" / "system_instructions" / "system_instruction_bug_graph_v2.md"
    prompt_template_file = base_dir / "core" / "gemini" / "templates" / "prompt_templates" / "chat_prompt_template_bug_graph_v2.md"
    
    # Output file
    output_file = base_dir / "test_output_bug_graph.json"
    
    # Check if files exist
    for file_path in [github_issue_file, schema_file, system_instruction_file, prompt_template_file]:
        if not file_path.exists():
            print(f"Error: Required file not found: {file_path}")
            print(f"Please ensure all required files are in their expected locations.")
            return False
    
    print(f"Testing Gemini bug reproduction graph generation with:")
    print(f"  GitHub issue: {github_issue_file}")
    print(f"  Schema: {schema_file}")
    print(f"  System instruction: {system_instruction_file}")
    print(f"  Prompt template: {prompt_template_file}")
    print(f"  Output will be saved to: {output_file}")
    
    try:
        # Choose a model - Gemini 1.5 Flash is good for testing as it's faster and cheaper
        model_name = "models/gemini-1.5-flash"
        
        # Call the generator
        result = generate_bug_reproduction_graph(
            github_issue_file=str(github_issue_file),
            schema_file=str(schema_file),
            system_instruction_file=str(system_instruction_file), 
            prompt_template_file=str(prompt_template_file),
            output_file=str(output_file),
            model_name=model_name
        )
        
        if "error" in result:
            print(f"Test failed: {result['error']}")
            return False
            
        print("Test completed successfully!")
        return True
        
    except Exception as e:
        print(f"Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting Gemini bug reproduction graph generator test...")
    success = test_gemini_bug_reproduction()
    sys.exit(0 if success else 1)
