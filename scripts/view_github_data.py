#!/usr/bin/env python3
"""
Simple script to view raw GitHub API response data for a specific issue.
"""

import sys
import os
import json
from pprint import pprint

# Add the parent directory to the Python path so we can import from core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.services.github_service import GitHubService

def main():
    # Create a GitHub service instance without a session (only for viewing data)
    github_service = GitHubService(session=None, token=None)
    
    # Check if issue URL was provided as command-line argument
    if len(sys.argv) > 1:
        issue_url = sys.argv[1]
    else:
        issue_url = "https://github.com/kaito-project/kaito/issues/928"  # Default
    
    print(f"Fetching data for: {issue_url}")
    
    # Get the raw issue data
    issue_data = github_service.get_issue_by_url(issue_url)
    
    if issue_data:
        print("\n=== GitHub API Raw Response ===\n")
        
        # Save complete data to file
        issue_number = issue_url.split("/")[-1]
        output_file = f"github_issue_{issue_number}_full.json"
        with open(output_file, "w") as f:
            # Create a copy of the data with the complete structure
            complete_data = issue_data.copy()
            # Convert objects to serializeable format
            json.dump(complete_data, f, indent=2, default=str)
        
        print(f"Complete data saved to {output_file}")
        
        # Print summary on console
        comments_data = issue_data.get('comments_data', [])
        print(f"Issue: {issue_data.get('title')}")
        print(f"Number: {issue_data.get('number')}")
        print(f"State: {issue_data.get('state')}")
        print(f"Comments: {len(comments_data)}")
        print(f"Created: {issue_data.get('created_at')}")
        print(f"Author: {issue_data.get('user', {}).get('login')}")
    else:
        print("Failed to fetch GitHub issue data")

if __name__ == "__main__":
    main()
