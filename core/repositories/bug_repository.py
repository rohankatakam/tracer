"""
Bug Repository

This module provides repository classes for bug-related operations using SQLAlchemy ORM.
"""

from typing import List, Optional, Dict, Any
import json
from sqlalchemy.orm import Session
from sqlalchemy import text
from core.models.db import Bug
from core.repositories.base_repository import BaseRepository


class BugRepository(BaseRepository[Bug]):
    """Repository for Bug model operations."""
    
    def __init__(self, session: Session):
        """Initialize with a database session."""
        super().__init__(session, Bug)
    
    def get_bug_by_id(self, bug_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a bug by its ID using direct SQL to bypass SQLAlchemy's enum validation.
        
        Args:
            bug_id: ID of the bug to retrieve
            
        Returns:
            Bug dictionary if found, None otherwise
        """
        try:
            # Use direct SQL with text() to bypass SQLAlchemy's enum validation
            query = text("SELECT * FROM bugs WHERE bug_id = :bug_id")
            result = self.session.execute(query, {"bug_id": bug_id}).fetchone()
            
            if not result:
                return None
                
            # Convert result to dictionary
            bug_dict = dict(result._mapping)
            
            # Parse JSON string for extra_data if it exists
            if bug_dict.get("extra_data") and isinstance(bug_dict["extra_data"], str):
                try:
                    bug_dict["extra_data"] = json.loads(bug_dict["extra_data"])
                except json.JSONDecodeError:
                    bug_dict["extra_data"] = {}
            else:
                bug_dict["extra_data"] = {}
                
            return bug_dict
        except Exception as e:
            print(f"Error getting bug by id: {str(e)}")
            return None
    
    def get_all_bugs(self) -> List[Bug]:
        """
        Get all bugs.
        
        Returns:
            List of all bugs
        """
        return self.get_all()
    
    def create_bug(self, **kwargs) -> Bug:
        """
        Create a new bug with all provided fields.
        
        Args:
            **kwargs: All fields for the bug, including:
                title: Bug title
                description: Bug description
                reporter: Person reporting the bug
                severity: Bug severity level
                schema_type: Type of bug schema (BASE, MOZILLA, CHROMIUM, ORACLE)
                status: Bug status
                And any other schema-specific fields
            
        Returns:
            Created Bug instance
        """
        # Ensure title is provided (required field)
        if 'title' not in kwargs:
            raise ValueError("Bug title is required")
            
        # Create the bug with all provided fields
        bug = Bug(**kwargs)
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
        
    def create_bug_from_dict(self, bug_data: Dict[str, Any]) -> Optional[Bug]:
        """
        Create a new bug from a dictionary of attribute values.
        
        Args:
            bug_data: Dictionary of bug attribute names and values
            
        Returns:
            Created Bug instance
        """
        try:
            # Make sure required fields are present
            if 'title' not in bug_data:
                raise ValueError("Bug title is required")
            
            # Create the bug using the base repository's create_from_dict method
            bug = self.create_from_dict(bug_data)
            return bug
        except Exception as e:
            print(f"Error creating bug from dictionary: {str(e)}")
            return None
