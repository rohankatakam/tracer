#!/usr/bin/env python3
"""
Test script for GitHub issue import functionality.

This script tests importing GitHub issues via URL to check
compatibility and verify API access works without authentication.
"""

import sys
import os
from pprint import pprint
import json

# Add the parent directory to the Python path so we can import from core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from core.services.github_service import GitHubService
from config.database import SessionLocal

# Issues to test
TEST_ISSUES = [
    "https://github.com/kaito-project/kaito/issues/932",
    "https://github.com/kaito-project/kaito/issues/928",
    "https://github.com/boostercloud/booster/issues/1463"
]

def test_github_issue_fetch(issue_url: str) -> None:
    """Test fetching a GitHub issue without importing it."""
    print(f"\n==== Testing Fetch: {issue_url} ====")
    
    # Initialize service without token to test unauthenticated access
    github_service = GitHubService(session=None, token=None)
    
    # Fetch the issue
    issue_data = github_service.get_issue_by_url(issue_url)
    
    if not issue_data:
        print("❌ Failed to fetch issue data")
        return
    
    print("✅ Successfully fetched issue data")
    
    # Print basic information
    print(f"Title: {issue_data.get('title')}")
    print(f"Author: {issue_data.get('user', {}).get('login')}")
    print(f"State: {issue_data.get('state')}")
    
    # Check for image attachments
    image_urls = issue_data.get('image_urls', [])
    if image_urls:
        print(f"Found {len(image_urls)} images:")
        for url in image_urls:
            print(f"  - {url}")
    else:
        print("No image attachments found")
    
    # Check comments
    comments = issue_data.get('comments_data', [])
    print(f"Found {len(comments)} comments")
    
    return issue_data

def test_github_issue_import(issue_url: str) -> None:
    """Test importing a GitHub issue into our database."""
    print(f"\n==== Testing Import: {issue_url} ====")
    
    # Get a database session
    db_session = SessionLocal()
    
    # Initialize with session
    github_service = GitHubService(session=db_session, token=None)
    
    try:
        # Import the issue
        bug_data = github_service.import_github_issue(issue_url)
        
        if not bug_data:
            print("❌ Failed to import issue")
            return
        
        print("✅ Successfully imported issue")
        print(f"Bug ID: {bug_data.get('bug_id')}")
        print(f"Title: {bug_data.get('title')}")
        
        # Check what GitHub fields were populated
        github_fields = [
            'github_issue_number', 'github_repository', 'github_issue_url', 
            'github_state', 'github_labels', 'github_milestone', 
            'github_assignees', 'github_author', 'github_created_at',
            'github_updated_at', 'github_closed_at', 'github_closed_by',
            'github_is_pull_request'
        ]
        
        print("\nGitHub fields populated:")
        for field in github_fields:
            value = bug_data.get(field)
            if value:
                status = "✅"
                if isinstance(value, list) and len(value) > 0:
                    value_str = f"{len(value)} items"
                else:
                    value_str = str(value)[:50] + ("..." if len(str(value)) > 50 else "")
            else:
                status = "❌"
                value_str = "None"
            
            print(f"{status} {field}: {value_str}")
        
        return bug_data
    
    finally:
        # Close the session
        db_session.close()

def main():
    """Main function to run tests."""
    print("=== Testing GitHub Issue Import ===")
    print("Note: Running without authentication token")
    
    # Test fetch only first
    results = {}
    for issue_url in TEST_ISSUES:
        issue_data = test_github_issue_fetch(issue_url)
        if issue_data:
            # Convert to serializable format for the report
            serializable_data = {k: str(v) if isinstance(v, (dict, list)) and k != 'image_urls' else v 
                              for k, v in issue_data.items() 
                              if k not in ['comments_data']}
            results[issue_url] = serializable_data
    
    # Save fetch results to a report file
    with open("github_fetch_report.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\n\n=== Import Tests ===")
    print("Testing actual database imports...")
    
    import_results = {}
    for issue_url in TEST_ISSUES:
        bug_data = test_github_issue_import(issue_url)
        if bug_data:
            # Just store essential fields
            import_results[issue_url] = {
                "bug_id": bug_data.get("bug_id"),
                "title": bug_data.get("title"),
                "github_issue_number": bug_data.get("github_issue_number"),
                "github_repository": bug_data.get("github_repository"),
                "import_success": True
            }
        else:
            import_results[issue_url] = {
                "import_success": False
            }
    
    # Save import results
    with open("github_import_report.json", "w") as f:
        json.dump(import_results, f, indent=2)
    
    print("\nDone! Reports saved to github_fetch_report.json and github_import_report.json")

if __name__ == "__main__":
    main()
