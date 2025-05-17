"""
Bug Router

This module defines FastAPI endpoints for bug-related operations.
"""

from typing import List, Optional
import traceback
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from core.repositories.bug_repository import BugRepository
from core.repositories.attachment_repository import AttachmentRepository
from core.repositories.comment_repository import CommentRepository
from api.schemas import Bug, BugCreate, BugUpdate, Comment, CommentCreate, CommentUpdate
from api.dependencies import get_db_session

router = APIRouter(prefix="/bugs", tags=["bugs"])


@router.post("", response_model=Bug, status_code=status.HTTP_201_CREATED)
def create_bug(bug: BugCreate, db: Session = Depends(get_db_session)):
    """Create a new bug."""
    repo = BugRepository(db)
    db_bug = repo.create_bug(
        title=bug.title,
        description=bug.description,
        reporter=bug.reporter,
        severity=bug.severity
    )
    # Add attachment count to the response
    setattr(db_bug, "attachment_count", 0)
    return db_bug


@router.get("", response_model=List[Bug])
def get_all_bugs(db: Session = Depends(get_db_session)):
    """Get all bugs."""
    repo = BugRepository(db)
    bugs = repo.get_all_bugs()
    
    # Add attachment count to each bug
    attachment_repo = AttachmentRepository(db)
    for bug in bugs:
        attachments = attachment_repo.get_attachments_by_bug_id(bug.bug_id)
        setattr(bug, "attachment_count", len(attachments))
    
    return bugs


@router.get("/{bug_id}", response_model=Bug)
def get_bug(bug_id: str, db: Session = Depends(get_db_session)):
    """Get a specific bug by ID."""
    repo = BugRepository(db)
    bug = repo.get_bug_by_id(bug_id)
    if not bug:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bug with ID {bug_id} not found"
        )
    
    # Add attachment count to the response
    attachment_repo = AttachmentRepository(db)
    attachments = attachment_repo.get_attachments_by_bug_id(bug_id)
    setattr(bug, "attachment_count", len(attachments))
    
    return bug


@router.put("/{bug_id}", response_model=Bug)
def update_bug(bug_id: str, bug_update: BugUpdate, db: Session = Depends(get_db_session)):
    """Update a bug."""
    repo = BugRepository(db)
    existing_bug = repo.get_bug_by_id(bug_id)
    if not existing_bug:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bug with ID {bug_id} not found"
        )
    
    # Filter out None values from bug_update
    update_data = {k: v for k, v in bug_update.model_dump().items() if v is not None}
    
    if not update_data:
        # No updates needed
        # Add attachment count to the response
        attachment_repo = AttachmentRepository(db)
        attachments = attachment_repo.get_attachments_by_bug_id(bug_id)
        setattr(existing_bug, "attachment_count", len(attachments))
        return existing_bug
    
    updated_bug = repo.update_by_id(bug_id, update_data)
    
    # Add attachment count to the response
    attachment_repo = AttachmentRepository(db)
    attachments = attachment_repo.get_attachments_by_bug_id(bug_id)
    setattr(updated_bug, "attachment_count", len(attachments))
    
    return updated_bug


@router.delete("/{bug_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bug(bug_id: str, db: Session = Depends(get_db_session)):
    """Delete a bug."""
    repo = BugRepository(db)
    existing_bug = repo.get_bug_by_id(bug_id)
    if not existing_bug:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bug with ID {bug_id} not found"
        )
    
    repo.delete_by_id(bug_id)
    return None


# Comments endpoints
@router.get("/{bug_id}/comments", response_model=List[Comment])
def get_bug_comments(bug_id: str, db: Session = Depends(get_db_session)):
    """Get all comments for a specific bug."""
    try:
        logger.info(f"Fetching comments for bug ID: {bug_id}")
        bug_repo = BugRepository(db)
        comment_repo = CommentRepository(db)
        
        # Check if bug exists
        bug = bug_repo.get_bug_by_id(bug_id)
        if not bug:
            logger.warning(f"Bug with ID {bug_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bug with ID {bug_id} not found"
            )
        
        # Get all comments for the bug
        logger.info(f"Getting comments for bug ID: {bug_id}")
        comments = comment_repo.get_comments_by_bug_id(bug_id)
        
        # Debug output - see what we're returning
        logger.info(f"Found {len(comments)} comments for bug ID: {bug_id}")
        for i, comment in enumerate(comments):
            logger.info(f"Comment {i+1}: id={comment.comment_id}, author={comment.author}")
            try:
                # Check if attachment_ids is accessible
                attachment_count = len(comment.attachment_ids) if comment.attachment_ids else 0
                logger.info(f"  - Has {attachment_count} attachment references")
            except Exception as e:
                logger.error(f"Error accessing attachment_ids: {str(e)}")
        
        return comments
    except Exception as e:
        logger.error(f"Error in get_bug_comments: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/{bug_id}/comments", response_model=Comment, status_code=status.HTTP_201_CREATED)
def create_bug_comment(bug_id: str, comment: CommentCreate, db: Session = Depends(get_db_session)):
    """Create a new comment for a specific bug."""
    bug_repo = BugRepository(db)
    comment_repo = CommentRepository(db)
    
    # Check if bug exists
    bug = bug_repo.get_bug_by_id(bug_id)
    if not bug:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bug with ID {bug_id} not found"
        )
    
    # If attachment_ids are provided, check if they all exist
    if comment.attachment_ids:
        attachment_repo = AttachmentRepository(db)
        for attachment_id in comment.attachment_ids:
            attachment = attachment_repo.get_attachment_by_id(attachment_id)
            if not attachment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Attachment with ID {attachment_id} not found"
                )
    
    # Create the comment
    db_comment = comment_repo.create_comment(
        bug_id=bug_id,
        author=comment.author,
        text=comment.text,
        is_private=comment.is_private,
        attachment_ids=comment.attachment_ids
    )
    
    return db_comment


@router.put("/comments/{comment_id}", response_model=Comment)
def update_comment(comment_id: str, comment_update: CommentUpdate, db: Session = Depends(get_db_session)):
    """Update a specific comment."""
    comment_repo = CommentRepository(db)
    
    # Check if comment exists
    existing_comment = comment_repo.get_comment_by_id(comment_id)
    if not existing_comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comment with ID {comment_id} not found"
        )
    
    # If attachment_ids are provided, check if they all exist
    if comment_update.attachment_ids:
        attachment_repo = AttachmentRepository(db)
        for attachment_id in comment_update.attachment_ids:
            attachment = attachment_repo.get_attachment_by_id(attachment_id)
            if not attachment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Attachment with ID {attachment_id} not found"
                )
    
    # Update the comment
    updated_comment = comment_repo.update_comment(
        comment_id=comment_id,
        text=comment_update.text,
        is_private=comment_update.is_private,
        attachment_ids=comment_update.attachment_ids
    )
    
    return updated_comment


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(comment_id: str, db: Session = Depends(get_db_session)):
    """Delete a specific comment."""
    comment_repo = CommentRepository(db)
    
    # Check if comment exists
    existing_comment = comment_repo.get_comment_by_id(comment_id)
    if not existing_comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comment with ID {comment_id} not found"
        )
    
    # Delete the comment
    comment_repo.delete_comment(comment_id)
    return None
