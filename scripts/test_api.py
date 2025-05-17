#!/usr/bin/env python3
"""
Test API Client

This script tests the Bug Attachment Processing API by making various requests to it.
"""

import os
import sys
import argparse
import requests
import json
from pathlib import Path
from datetime import datetime
from pprint import pprint

# Add the project root to the path so we can import packages properly
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_api(base_url):
    """Test the API by making various requests and printing responses."""
    print(f"Testing API at {base_url}")
    
    # Test the root endpoint
    print("\n=== Testing root endpoint ===")
    response = requests.get(f"{base_url}/")
    print(f"Status: {response.status_code}")
    pprint(response.json())
    
    # Test the health check endpoint
    print("\n=== Testing health check endpoint ===")
    response = requests.get(f"{base_url}/health")
    print(f"Status: {response.status_code}")
    pprint(response.json())
    
    # Create a new bug
    print("\n=== Creating a new bug ===")
    bug_data = {
        "title": "Test Bug",
        "description": "This is a test bug created via the API",
        "reporter": "API Test Script",
        "severity": "MEDIUM"
    }
    response = requests.post(f"{base_url}/bugs", json=bug_data)
    print(f"Status: {response.status_code}")
    bug = response.json()
    pprint(bug)
    bug_id = bug.get("bug_id")
    
    if not bug_id:
        print("Failed to get bug ID, aborting further tests")
        return
    
    # Get the bug by ID
    print(f"\n=== Getting bug {bug_id} ===")
    response = requests.get(f"{base_url}/bugs/{bug_id}")
    print(f"Status: {response.status_code}")
    pprint(response.json())
    
    # Update the bug
    print(f"\n=== Updating bug {bug_id} ===")
    update_data = {
        "status": "IN_PROGRESS",
        "severity": "HIGH"
    }
    response = requests.put(f"{base_url}/bugs/{bug_id}", json=update_data)
    print(f"Status: {response.status_code}")
    pprint(response.json())
    
    # Get all bugs
    print("\n=== Getting all bugs ===")
    response = requests.get(f"{base_url}/bugs")
    print(f"Status: {response.status_code}")
    bugs = response.json()
    print(f"Found {len(bugs)} bugs")
    for b in bugs:
        print(f"- {b.get('bug_id')}: {b.get('title')} (Status: {b.get('status')})")
    
    # Test file upload endpoint (simulate with a text file)
    print(f"\n=== Uploading attachment to bug {bug_id} ===")
    test_file_path = Path(project_root) / "temp_test_file.txt"
    with open(test_file_path, "w") as f:
        f.write("This is a test file for API upload testing.\n")
        f.write(f"Created at {datetime.now().isoformat()}")
    
    try:
        files = {"file": open(test_file_path, "rb")}
        data = {"description": "Test attachment", "uploader": "API Test Script"}
        response = requests.post(f"{base_url}/bugs/{bug_id}/attachments", files=files, data=data)
        print(f"Status: {response.status_code}")
        attachment = response.json()
        pprint(attachment)
        attachment_id = attachment.get("attachment_id")
        
        if attachment_id:
            # Get attachment by ID
            print(f"\n=== Getting attachment {attachment_id} ===")
            response = requests.get(f"{base_url}/attachments/{attachment_id}")
            print(f"Status: {response.status_code}")
            pprint(response.json())
            
            # Get attachment content
            print(f"\n=== Getting attachment content for {attachment_id} ===")
            response = requests.get(f"{base_url}/attachments/{attachment_id}/content")
            print(f"Status: {response.status_code}")
            pprint(response.json())
            
        # Get all attachments for the bug
        print(f"\n=== Getting all attachments for bug {bug_id} ===")
        response = requests.get(f"{base_url}/bugs/{bug_id}/attachments")
        print(f"Status: {response.status_code}")
        attachments = response.json()
        print(f"Found {len(attachments)} attachments")
        for a in attachments:
            print(f"- {a.get('attachment_id')}: {a.get('filename')} ({a.get('file_type')})")
    finally:
        # Clean up test file
        if os.path.exists(test_file_path):
            os.remove(test_file_path)
    
    print("\n=== API Test Complete ===")


def main():
    parser = argparse.ArgumentParser(description='Test the Bug Attachment Processing API')
    parser.add_argument('--host', type=str, default='127.0.0.1',
                        help='API host (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=8000,
                        help='API port (default: 8000)')
    
    args = parser.parse_args()
    base_url = f"http://{args.host}:{args.port}"
    
    try:
        test_api(base_url)
    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to API at {base_url}")
        print("Make sure the API server is running (use run_api_server.py)")
        sys.exit(1)
    except Exception as e:
        print(f"Error during API testing: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
