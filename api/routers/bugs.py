"""
Bug Router

This module defines FastAPI endpoints for bug-related operations.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.repositories.bug_repository import BugRepository
from core.repositories.attachment_repository import AttachmentRepository
from api.schemas import Bug, BugCreate, BugUpdate
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
