"""
Comment Repository

This module provides repository classes for comment-related operations using SQLAlchemy ORM.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from core.models.db.comment import Comment
from core.models.db.attachment import Attachment
from core.repositories.base_repository import BaseRepository


class CommentRepository(BaseRepository[Comment]):
    """Repository for Comment model operations."""
    
    def __init__(self, session: Session):
        """Initialize with a database session."""
        super().__init__(session, Comment)
    
    def get_comment_by_id(self, comment_id: str) -> Optional[Comment]:
        """
        Get a comment by its ID.
        
        Args:
            comment_id: ID of the comment to retrieve
            
        Returns:
            Comment instance if found, None otherwise
        """
        return self.get_by_id(comment_id)
    
    def get_comments_by_bug_id(self, bug_id: str) -> List[Comment]:
        """
        Get all comments for a specific bug.
        
        Args:
            bug_id: ID of the bug to get comments for
            
        Returns:
            List of comments for the specified bug
        """
        return self.session.query(self.model_cls).filter(self.model_cls.bug_id == bug_id).all()
    
    def create_comment(self, bug_id: str, author: str, text: str, 
                      is_private: bool = False, attachment_ids: List[str] = None) -> Comment:
        """
        Create a new comment.
        
        Args:
            bug_id: ID of the bug this comment belongs to
            author: Name of the comment author
            text: Content of the comment
            is_private: Whether the comment is private
            attachment_ids: List of attachment IDs referenced in the comment
            
        Returns:
            Created Comment instance
        """
        comment = Comment(
            bug_id=bug_id,
            author=author,
            text=text,
            is_private=is_private
        )
        
        # Create the comment first to get its ID
        created_comment = self.create(comment)
        
        # Add attachment references if provided
        if attachment_ids and created_comment:
            attachments = self._get_attachments_by_ids(attachment_ids)
            created_comment.referenced_attachments = attachments
            self.session.commit()
            
        return created_comment
    
    def delete_comment(self, comment_id: str) -> bool:
        """
        Delete a comment.
        
        Args:
            comment_id: ID of the comment to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        return self.delete_by_id(comment_id)
    
    def _get_attachments_by_ids(self, attachment_ids: List[str]) -> List[Attachment]:
        """
        Get Attachment objects from their IDs.
        
        Args:
            attachment_ids: List of attachment IDs to fetch
            
        Returns:
            List of Attachment objects
        """
        if not attachment_ids:
            return []
            
        return self.session.query(Attachment).filter(Attachment.attachment_id.in_(attachment_ids)).all()
    
    def update_comment(self, comment_id: str, text: str = None, 
                      is_private: bool = None, attachment_ids: List[str] = None) -> Optional[Comment]:
        """
        Update a comment.
        
        Args:
            comment_id: ID of the comment to update
            text: New content for the comment
            is_private: New privacy setting
            attachment_ids: New list of attachment IDs
            
        Returns:
            Updated Comment instance if found, None otherwise
        """
        update_data = {}
        if text is not None:
            update_data["text"] = text
        if is_private is not None:
            update_data["is_private"] = is_private
            
        comment = self.update_by_id(comment_id, update_data)
        
        # Update attachment references if provided
        if comment and attachment_ids is not None:
            attachments = self._get_attachments_by_ids(attachment_ids)
            comment.referenced_attachments = attachments
            self.session.commit()
            
        return comment
