#!/usr/bin/env python3
"""
Command line interface for the extraction tools.
This allows for CLI-based access to the web page extraction functionality.
"""

import os
import sys
import argparse
from pathlib import Path

from .extract_wiki_content import extract_wiki_content

def main():
    """Main entry point for the extraction CLI."""
    parser = argparse.ArgumentParser(description="Web content extraction tool")
    
    # Add subparsers for different extraction types
    subparsers = parser.add_subparsers(dest="command", help="Extraction commands")
    
    # Wikipedia extraction parser
    wiki_parser = subparsers.add_parser("wiki", help="Extract content from Wikipedia")
    wiki_parser.add_argument("--url", "-u", help="URL of the Wikipedia page to extract content from")
    wiki_parser.add_argument("--output", "-o", help="Output file path", 
                            default=os.path.join("data", "outputs", "wiki_content.json"))
    
    # Parse arguments
    args = parser.parse_args()
    
    # Exit if no command specified
    if args.command is None:
        parser.print_help()
        return 1
    
    # Handle wiki extraction
    if args.command == "wiki":
        # Create directory if it doesn't exist
        output_dir = os.path.dirname(args.output)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # Perform extraction
        success = extract_wiki_content(args.output)
        if success:
            print(f"Content successfully extracted to {args.output}")
            return 0
        else:
            print("Failed to extract content")
            return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
