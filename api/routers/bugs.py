"""
Bug Router

This module defines FastAPI endpoints for bug-related operations.
"""

from typing import List, Optional
import traceback
import logging
import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from uuid import uuid4
from core.models.db.bug import Bug as BugModel

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
    try:
        logger.info(f"Creating new bug with schema_type: {bug.schema_type}")
        
        # Extract all fields from the bug object
        bug_data = bug.model_dump(exclude_none=True)
        
        # Generate a UUID for the bug_id if not provided
        if 'bug_id' not in bug_data:
            bug_data['bug_id'] = str(uuid4())
            
        # Add timestamps if not provided
        if 'created_at' not in bug_data:
            bug_data['created_at'] = datetime.now()
        if 'updated_at' not in bug_data:
            bug_data['updated_at'] = datetime.now()
            
        # Handle JSON serialization for extra_data
        if 'extra_data' in bug_data and isinstance(bug_data['extra_data'], dict):
            bug_data['extra_data'] = json.dumps(bug_data['extra_data'])
        elif 'extra_data' not in bug_data or bug_data['extra_data'] is None:
            bug_data['extra_data'] = json.dumps({})
        
        # Build SQL query using named parameters
        columns = ', '.join(bug_data.keys())
        placeholders = ', '.join([f':{k}' for k in bug_data.keys()])
        
        # Use SQLAlchemy text() for raw SQL
        query = text(f"INSERT INTO bugs ({columns}) VALUES ({placeholders}) RETURNING *")
        
        # Execute the query and get the result
        result = db.execute(query, bug_data).fetchone()
        db.commit()
        
        # Convert result to dictionary using SQLAlchemy 2.0 approach
        bug_dict = dict(result._mapping)
        
        # Parse JSON string back to dictionary for extra_data
        if bug_dict.get("extra_data") and isinstance(bug_dict["extra_data"], str):
            try:
                bug_dict["extra_data"] = json.loads(bug_dict["extra_data"])
            except json.JSONDecodeError:
                bug_dict["extra_data"] = {}
        else:
            bug_dict["extra_data"] = {}
            
        # Add attachment count
        bug_dict["attachment_count"] = 0
            
        return bug_dict
    except Exception as e:
        logger.error(f"Error creating bug: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating bug: {str(e)}"
        )


@router.get("", response_model=List[Bug])
def get_all_bugs(db: Session = Depends(get_db_session)):
    """Get all bugs."""
    try:
        logger.info("Getting all bugs")
        
        # Use direct SQL with text() to bypass SQLAlchemy's enum validation
        bugs_raw = db.execute(text("SELECT * FROM bugs")).fetchall()
        
        # Process results to dictionaries
        result = []
        for bug_row in bugs_raw:
            # Convert Row to dict correctly in SQLAlchemy 2.0
            bug_dict = dict(bug_row._mapping)
            
            # Parse JSON string for extra_data if it exists
            if bug_dict.get("extra_data") and isinstance(bug_dict["extra_data"], str):
                try:
                    bug_dict["extra_data"] = json.loads(bug_dict["extra_data"])
                except json.JSONDecodeError:
                    bug_dict["extra_data"] = {}
            else:
                bug_dict["extra_data"] = {}
                
            # Add attachment count
            bug_dict["attachment_count"] = 0
            
            # Handle base schema type default values
            if bug_dict.get("schema_type") == "base" or bug_dict.get("schema_type") == "BASE":
                # Default values for base schema
                if not bug_dict.get("severity"):
                    bug_dict["severity"] = "MEDIUM"
                if not bug_dict.get("status"):
                    bug_dict["status"] = "NEW"
            
            result.append(bug_dict)
            
        logger.info(f"Found {len(result)} bugs")
        
        return result
    except Exception as e:
        logger.error(f"Error in get_all_bugs: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving bugs: {str(e)}"
        )


@router.get("/{bug_id}", response_model=Bug)
def get_bug(bug_id: str, db: Session = Depends(get_db_session)):
    """Get a specific bug by ID."""
    try:
        logger.info(f"Getting bug with ID: {bug_id}")
        repo = BugRepository(db)
        bug = repo.get_bug_by_id(bug_id)
        if not bug:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bug with ID {bug_id} not found"
            )
        
        # Our bug is already a dictionary from get_bug_by_id
        bug_dict = bug
        
        # Add attachment count to the response
        attachment_repo = AttachmentRepository(db)
        attachments = attachment_repo.get_attachments_by_bug_id(bug_id)
        bug_dict["attachment_count"] = len(attachments)
        
        # Ensure extra_data is a dictionary
        if bug_dict.get("extra_data") is None or not isinstance(bug_dict["extra_data"], dict):
            # Check if extra_data is a string that can be parsed as JSON
            if isinstance(bug_dict.get("extra_data"), str):
                try:
                    bug_dict["extra_data"] = json.loads(bug_dict["extra_data"])
                except json.JSONDecodeError:
                    bug_dict["extra_data"] = {}
            else:
                bug_dict["extra_data"] = {}
        
        return bug_dict
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error in get_bug: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving bug: {str(e)}"
        )


@router.put("/{bug_id}", response_model=Bug)
def update_bug(bug_id: str, bug_update: BugUpdate, db: Session = Depends(get_db_session)):
    """Update a bug."""
    try:
        logger.info(f"Updating bug with ID: {bug_id}")
        repo = BugRepository(db)
        existing_bug_dict = repo.get_bug_by_id(bug_id)
        if not existing_bug_dict:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bug with ID {bug_id} not found"
            )
        
        # Filter out None values from bug_update
        update_data = {k: v for k, v in bug_update.model_dump().items() if v is not None}
        
        if not update_data:
            # No updates needed, use existing bug dictionary
            bug_dict = existing_bug_dict
            # Add attachment count to the response
            attachment_repo = AttachmentRepository(db)
            attachments = attachment_repo.get_attachments_by_bug_id(bug_id)
            bug_dict["attachment_count"] = len(attachments)
            
            # Ensure extra_data is a dictionary
            if bug_dict.get("extra_data") is None or not isinstance(bug_dict["extra_data"], dict):
                # Check if extra_data is a string that can be parsed as JSON
                if isinstance(bug_dict.get("extra_data"), str):
                    try:
                        bug_dict["extra_data"] = json.loads(bug_dict["extra_data"])
                    except json.JSONDecodeError:
                        bug_dict["extra_data"] = {}
                else:
                    bug_dict["extra_data"] = {}
                
            return bug_dict
        
        # Update in the database using direct SQL to bypass enum validation
        query = text(f"UPDATE bugs SET {', '.join([f'{k} = :{k}' for k in update_data.keys()])} WHERE bug_id = :bug_id RETURNING *")
        params = {**update_data, "bug_id": bug_id}
        result = db.execute(query, params).fetchone()
        db.commit()
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bug with ID {bug_id} not found after update"
            )
        
        # Convert result to dictionary
        bug_dict = dict(result._mapping)
        
        # Add attachment count to the response
        attachment_repo = AttachmentRepository(db)
        attachments = attachment_repo.get_attachments_by_bug_id(bug_id)
        bug_dict["attachment_count"] = len(attachments)
        
        # Ensure extra_data is a dictionary
        if bug_dict.get("extra_data") is None or not isinstance(bug_dict["extra_data"], dict):
            # Check if extra_data is a string that can be parsed as JSON
            if isinstance(bug_dict.get("extra_data"), str):
                try:
                    bug_dict["extra_data"] = json.loads(bug_dict["extra_data"])
                except json.JSONDecodeError:
                    bug_dict["extra_data"] = {}
            else:
                bug_dict["extra_data"] = {}
            
        return bug_dict
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error in update_bug: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating bug: {str(e)}"
        )


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
