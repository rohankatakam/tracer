"""
GitHub Integration Service

This service provides functions for interacting with the GitHub API,
particularly for fetching issues and importing them into our bug database.
"""

import os
import re
import logging
import requests
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from sqlalchemy.orm import Session
from core.repositories.bug_repository import BugRepository
from core.repositories.comment_repository import CommentRepository
from core.models.db.github_issue import convert_github_issue_to_bug
from core.models.db.bug import BugSchemaType

# Set up logging
logger = logging.getLogger(__name__)

class GitHubService:
    """Service for interacting with GitHub API."""
    
    # Regular expression to find image URLs in markdown content
    IMAGE_PATTERN = r'!\[.*?\]\((https?://\S+?)\)'
    
    def __init__(self, session: Session, token: Optional[str] = None):
        """Initialize with database session and optional token.
        
        Args:
            session: SQLAlchemy database session
            token: GitHub API token (optional for public repos, required for private repos)
        """
        self.session = session
        self.bug_repo = BugRepository(session)
        self.comment_repo = CommentRepository(session)
        
        # Use provided token or get from env var if available
        self.github_token = token if token is not None else os.environ.get("GITHUB_TOKEN", "")
        
        # GitHub API base URL
        self.api_base_url = "https://api.github.com"
    
    def get_headers(self) -> Dict[str, str]:
        """Get headers for GitHub API requests."""
        headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Add authorization if token is available
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"
            
        return headers
    
    def parse_github_issue_url(self, url: str) -> Tuple[Optional[str], Optional[str], Optional[int]]:
        """
        Parse a GitHub issue URL to extract owner, repo, and issue number.
        
        Args:
            url: GitHub issue URL
            
        Returns:
            Tuple of (owner, repo, issue_number)
        """
        # Match formats like:
        # https://github.com/owner/repo/issues/123
        # https://github.com/owner/repo/pull/123
        pattern = r"github\.com/([^/]+)/([^/]+)/(?:issues|pull)/(\d+)"
        match = re.search(pattern, url)
        
        if match:
            owner = match.group(1)
            repo = match.group(2)
            issue_number = int(match.group(3))
            return owner, repo, issue_number
        
        return None, None, None
    
    def get_issue_by_url(self, issue_url: str) -> Optional[Dict[str, Any]]:
        """
        Get issue data from GitHub by URL.
        
        Args:
            issue_url: GitHub issue URL
            
        Returns:
            Issue data if found, None otherwise
        """
        owner, repo, issue_number = self.parse_github_issue_url(issue_url)
        
        if not (owner and repo and issue_number):
            logger.error(f"Invalid GitHub issue URL: {issue_url}")
            return None
        
        return self.get_issue(owner, repo, issue_number)
    
    def get_issue(self, owner: str, repo: str, issue_number: int) -> Optional[Dict[str, Any]]:
        """
        Get issue data from GitHub API.
        
        Args:
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number
            
        Returns:
            Issue data if found, None otherwise
        """
        url = f"{self.api_base_url}/repos/{owner}/{repo}/issues/{issue_number}"
        
        try:
            # Make request to GitHub API
            headers = self.get_headers()
            response = requests.get(url, headers=headers)
            
            # Check for rate limiting
            remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
            if remaining < 5:
                reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                reset_datetime = datetime.fromtimestamp(reset_time)
                current_time = datetime.now()
                minutes_to_reset = (reset_datetime - current_time).total_seconds() / 60
                
                logger.warning(f"GitHub API rate limit low: {remaining} requests remaining. "
                               f"Resets in {minutes_to_reset:.1f} minutes.")
            
            # Handle response codes
            if response.status_code == 404:
                logger.error(f"GitHub issue not found: {owner}/{repo}#{issue_number}")
                return None
            elif response.status_code == 403 and 'X-RateLimit-Remaining' in response.headers and \
                    int(response.headers['X-RateLimit-Remaining']) == 0:
                logger.error(f"GitHub API rate limit exceeded. Resets at {reset_datetime}")
                return None
                
            response.raise_for_status()
            
            issue_data = response.json()
            
            # Add owner/repo to the issue data
            issue_data["owner"] = owner
            issue_data["repo"] = repo
            
            # Get comments if available
            comments_url = issue_data.get("comments_url")
            if comments_url and issue_data.get("comments", 0) > 0:
                comments_response = requests.get(comments_url, headers=headers)
                if comments_response.status_code == 200:
                    issue_data["comments_data"] = comments_response.json()
                else:
                    logger.warning(f"Failed to fetch comments for {owner}/{repo}#{issue_number}. "
                                   f"Status: {comments_response.status_code}")
                    issue_data["comments_data"] = []
            else:
                issue_data["comments_data"] = []
            
            # Check for attachments (images) in the issue body and comments
            self._extract_image_urls(issue_data)
            
            return issue_data
        except requests.RequestException as e:
            logger.error(f"Error fetching GitHub issue {owner}/{repo}#{issue_number}: {str(e)}")
            return None
    
    def _extract_image_urls(self, issue_data: Dict[str, Any]) -> None:
        """
        Extract image URLs from the issue body and comments.
        Adds 'image_urls' key to the issue data.
        
        Args:
            issue_data: GitHub issue data
        """
        image_urls = []
        
        # Check body for images
        body = issue_data.get('body', '')
        if body:
            urls = re.findall(self.IMAGE_PATTERN, body)
            image_urls.extend(urls)
        
        # Check comments for images
        for comment in issue_data.get('comments_data', []):
            comment_body = comment.get('body', '')
            if comment_body:
                urls = re.findall(self.IMAGE_PATTERN, comment_body)
                image_urls.extend(urls)
        
        # Add to issue data
        issue_data['image_urls'] = image_urls
    
    def convert_issue_comments_to_bug_comments(
        self, issue_data: Dict[str, Any], bug_id: str
    ) -> List[Dict[str, Any]]:
        """
        Convert GitHub issue comments to our bug comments format.
        
        Args:
            issue_data: GitHub issue data
            bug_id: ID of the bug in our system
            
        Returns:
            List of comment data dictionaries
        """
        comments = []
        
        # First add the initial issue body as a comment from the author
        if issue_data.get("body"):
            comments.append({
                "bug_id": bug_id,
                "author": issue_data.get("user", {}).get("login", ""),
                "text": issue_data.get("body", ""),
                "timestamp": issue_data.get("created_at"),
                "is_private": False
            })
        
        # Add any additional comments
        for comment in issue_data.get("comments_data", []):
            comments.append({
                "bug_id": bug_id,
                "author": comment.get("user", {}).get("login", ""),
                "text": comment.get("body", ""),
                "timestamp": comment.get("created_at"),
                "is_private": False
            })
        
        return comments
    
    def import_github_issue(self, issue_url: str) -> Optional[Dict[str, Any]]:
        """
        Import a GitHub issue into our bug database.
        
        Args:
            issue_url: GitHub issue URL
            
        Returns:
            The imported bug data if successful, None otherwise
        """
        # Get issue data from GitHub
        issue_data = self.get_issue_by_url(issue_url)
        
        if not issue_data:
            return None
        
        # Convert to our bug format
        bug_data = convert_github_issue_to_bug(issue_data)
        
        # Create bug in the database
        bug = self.bug_repo.create_bug_from_dict(bug_data)
        
        if not bug:
            return None
        
        # Create comments
        comments_data = self.convert_issue_comments_to_bug_comments(issue_data, bug.bug_id)
        for comment_data in comments_data:
            self.comment_repo.create_comment_from_dict(comment_data)
        
        # Return the created bug data
        return bug.to_dict()
