"""
GitHub Issue model for the SQLAlchemy ORM.

This module defines the GitHub-specific enums and extensions to the Bug model
to support importing and processing GitHub issues.
"""

import enum
from typing import List, Dict, Any, Optional
from sqlalchemy import Column, String, Enum, Boolean, ARRAY, JSON

# Import these for reference but don't create circular dependencies
from core.models.db.bug import Bug, BugSchemaType


class GitHubIssueState(enum.Enum):
    """GitHub issue states"""
    OPEN = "open"
    CLOSED = "closed"


class GitHubIssueLabelColor(enum.Enum):
    """Common GitHub label colors (not exhaustive)"""
    BUG = "d73a4a"       # Red
    FEATURE = "0075ca"   # Blue
    DOCS = "0075ca"      # Blue
    ENHANCEMENT = "a2eeef"  # Cyan
    HELP_WANTED = "008672"  # Green
    QUESTION = "d876e3"  # Purple


# No need to create a new table - we'll extend the Bug model with GitHub-specific fields
# These fields are already in the Bug table defined in bug.py:

"""
# The following fields should be added to Bug model in bug.py:

# GitHub issue specific fields
github_issue_number = Column(Integer)
github_repository = Column(String)  # format: "owner/repo"
github_issue_url = Column(String)
github_state = Column(Enum(GitHubIssueState))
github_labels = Column(JSON)  # Store as JSON array
github_milestone = Column(String)
github_assignees = Column(JSON)  # Store as JSON array of usernames
github_author = Column(String)
github_created_at = Column(DateTime)
github_updated_at = Column(DateTime)
github_closed_at = Column(DateTime)
github_closed_by = Column(String)
github_is_pull_request = Column(Boolean, default=False)
"""


# Helper functions for GitHub issues

def convert_github_issue_to_bug(github_issue_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert GitHub issue data to our Bug model format.
    
    Args:
        github_issue_data: Raw GitHub issue API response
        
    Returns:
        Dictionary with fields matching our Bug model
    """
    # Extract basic fields
    owner = github_issue_data.get("owner", "")
    repo = github_issue_data.get("repo", "")
    repository = f"{owner}/{repo}" if owner and repo else ""
    
    # Convert any image URLs found to attachments
    image_urls = github_issue_data.get("image_urls", [])
    description = github_issue_data.get("body", "")
    
    # Add links to images as references in description if they exist
    if image_urls:
        description += "\n\n**Attachments:**\n"
        for i, url in enumerate(image_urls):
            description += f"\n- [Image {i+1}]({url})"
    
    bug_data = {
        "title": github_issue_data.get("title", ""),
        "description": description,
        "reporter": github_issue_data.get("user", {}).get("login", ""),
        "schema_type": BugSchemaType.GITHUB.value,
        
        # GitHub specific fields
        "github_issue_number": github_issue_data.get("number"),
        "github_repository": repository,
        "github_issue_url": github_issue_data.get("html_url", ""),
        "github_state": github_issue_data.get("state", ""),
        "github_labels": [label.get("name") for label in github_issue_data.get("labels", [])],
        "github_milestone": github_issue_data.get("milestone", {}).get("title") if github_issue_data.get("milestone") else None,
        "github_assignees": [assignee.get("login") for assignee in github_issue_data.get("assignees", [])],
        "github_author": github_issue_data.get("user", {}).get("login", ""),
        "github_created_at": github_issue_data.get("created_at"),
        "github_updated_at": github_issue_data.get("updated_at"),
        "github_closed_at": github_issue_data.get("closed_at"),
        "github_closed_by": github_issue_data.get("closed_by", {}).get("login") if github_issue_data.get("closed_by") else None,
        "github_is_pull_request": "pull_request" in github_issue_data
    }
    
    # Set severity based on labels (optional enhancement)
    for label in github_issue_data.get("labels", []):
        label_name = label.get("name", "").lower()
        if "critical" in label_name or "blocker" in label_name:
            bug_data["severity"] = "critical"
            break
        elif "high" in label_name or "major" in label_name:
            bug_data["severity"] = "high"
            break
        elif "medium" in label_name or "normal" in label_name:
            bug_data["severity"] = "medium"
            break
        elif "low" in label_name or "minor" in label_name:
            bug_data["severity"] = "low"
            break
    
    # Default severity if not found in labels
    if "severity" not in bug_data:
        bug_data["severity"] = "medium"
    
    # Map GitHub issue state to our status field
    if github_issue_data.get("state") == "closed":
        bug_data["status"] = "CLOSED"
    else:
        bug_data["status"] = "NEW"
    
    return bug_data
