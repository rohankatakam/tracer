#!/usr/bin/env python3
"""
Schema converter for Gemini API integration.
This module adapts JSON schemas to match Gemini's expectations (primarily by converting types to uppercase).
"""

import json
import os
import sys
from pathlib import Path

def convert_to_gemini_schema(schema_obj):
    """
    Convert a JSON schema object to a format compatible with the Gemini API.
    Primary conversion: Change type values from lowercase to uppercase.
    
    Args:
        schema_obj: The JSON schema object
        
    Returns:
        A modified schema object suitable for Gemini API
    """
    if not isinstance(schema_obj, dict):
        return schema_obj
    
    result = {}
    for key, value in schema_obj.items():
        if key == "type" and isinstance(value, str):
            result[key] = value.upper()
        elif key == "properties" and isinstance(value, dict):
            result[key] = {k: convert_to_gemini_schema(v) for k, v in value.items()}
        elif key == "items" and isinstance(value, dict):
            result[key] = convert_to_gemini_schema(value)
        else:
            result[key] = value
    
    return result

def convert_schema_file(input_file, output_file=None):
    """
    Convert a JSON schema file to a Gemini-compatible schema file.
    
    Args:
        input_file: Path to the input JSON schema file
        output_file: Optional path to write the converted schema
        
    Returns:
        The converted schema object
    """
    with open(input_file, 'r') as f:
        schema = json.load(f)
    
    gemini_schema = convert_to_gemini_schema(schema)
    
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(gemini_schema, f, indent=2)
        print(f"Converted schema saved to {output_file}")
    
    return gemini_schema

def main():
    if len(sys.argv) < 2:
        print("Usage: python schema_converter.py <input_schema_file> [output_file]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    convert_schema_file(input_file, output_file)

if __name__ == "__main__":
    main()
