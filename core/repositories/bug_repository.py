"""
Bug Repository

This module provides repository classes for bug-related operations using SQLAlchemy ORM.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from core.models.db import Bug
from core.repositories.base_repository import BaseRepository


class BugRepository(BaseRepository[Bug]):
    """Repository for Bug model operations."""
    
    def __init__(self, session: Session):
        """Initialize with a database session."""
        super().__init__(session, Bug)
    
    def get_bug_by_id(self, bug_id: str) -> Optional[Bug]:
        """
        Get a bug by its ID.
        
        Args:
            bug_id: ID of the bug to retrieve
            
        Returns:
            Bug instance if found, None otherwise
        """
        return self.get_by_id(bug_id)
    
    def get_all_bugs(self) -> List[Bug]:
        """
        Get all bugs.
        
        Returns:
            List of all bugs
        """
        return self.get_all()
    
    def create_bug(self, title: str, description: str = None, 
                  reporter: str = None, severity: str = None) -> Bug:
        """
        Create a new bug.
        
        Args:
            title: Bug title
            description: Bug description
            reporter: Person reporting the bug
            severity: Bug severity level
            
        Returns:
            Created Bug instance
        """
        bug = Bug(
            title=title,
            description=description,
            reporter=reporter,
            severity=severity
        )
        return self.create(bug)
    
    def update_bug_status(self, bug_id: str, status: str) -> Optional[Bug]:
        """
        Update a bug's status.
        
        Args:
            bug_id: ID of the bug to update
            status: New status
            
        Returns:
            Updated Bug instance if found, None otherwise
        """
        return self.update_by_id(bug_id, {"status": status})
