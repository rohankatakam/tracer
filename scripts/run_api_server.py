#!/usr/bin/env python3
"""
Run API Server

This script launches the Bug Attachment Processing API server.
"""

import os
import sys
import argparse
import uvicorn
from pathlib import Path

# Add the project root to the path so we can import packages properly
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def main():
    parser = argparse.ArgumentParser(description='Run the Bug Attachment Processing API server')
    parser.add_argument('--host', '-H', type=str, default='127.0.0.1',
                        help='Host to bind the server to (default: 127.0.0.1)')
    parser.add_argument('--port', '-p', type=int, default=8000,
                        help='Port to bind the server to (default: 8000)')
    parser.add_argument('--reload', '-r', action='store_true',
                        help='Enable auto-reload on code changes')
    
    args = parser.parse_args()
    
    # Print startup message
    print(f"Starting Bug Attachment Processing API server at http://{args.host}:{args.port}")
    print(f"API Documentation will be available at http://{args.host}:{args.port}/docs")
    
    # Start the server
    uvicorn.run(
        "api.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )


if __name__ == "__main__":
    main()
