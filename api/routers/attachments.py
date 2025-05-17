"""
Attachment Router

This module defines FastAPI endpoints for attachment-related operations.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
import os
import shutil
from datetime import datetime

from core.repositories.bug_repository import BugRepository
from core.repositories.attachment_repository import AttachmentRepository, TextContentRepository, ImageContentRepository
from api.schemas import Attachment, AttachmentCreate, AttachmentUpdate, TextContent
from api.dependencies import get_db_session
from core.models.attachment_schema import AttachmentType

router = APIRouter(tags=["attachments"])


@router.post("/bugs/{bug_id}/attachments", response_model=Attachment, status_code=status.HTTP_201_CREATED)
async def create_attachment(
    bug_id: str, 
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    uploader: Optional[str] = Form(None),
    db: Session = Depends(get_db_session)
):
    """Upload a new attachment for a bug."""
    # Check if bug exists
    bug_repo = BugRepository(db)
    bug = bug_repo.get_bug_by_id(bug_id)
    if not bug:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bug with ID {bug_id} not found"
        )
    
    # Extract file info
    filename = file.filename
    file_size = 0
    
    # Determine file extension and type
    file_extension = os.path.splitext(filename)[1].lower().lstrip(".")
    
    # Default to TEXT for unknown types
    file_type = AttachmentType.TEXT
    
    # Map common extensions to appropriate types
    if file_extension in ["jpg"]:
        file_type = AttachmentType.IMAGE_JPG
    elif file_extension in ["jpeg"]:
        file_type = AttachmentType.IMAGE_JPEG
    elif file_extension in ["png"]:
        file_type = AttachmentType.IMAGE_PNG
    elif file_extension in ["pdf"]:
        file_type = AttachmentType.PDF
    elif file_extension in ["mp4"]:
        file_type = AttachmentType.VIDEO
    elif file_extension in ["txt"]:
        file_type = AttachmentType.TEXT
    
    # Create the upload directory if it doesn't exist
    upload_dir = os.path.join(os.getcwd(), 'data', 'attachments')
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save the file
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    sanitized_filename = f"{timestamp}_{os.path.basename(filename)}"
    file_path = os.path.join(upload_dir, sanitized_filename)
    
    with open(file_path, "wb") as buffer:
        # Read the file in chunks to handle large files efficiently
        chunk_size = 1024 * 1024  # 1MB chunks
        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break
            buffer.write(chunk)
            file_size += len(chunk)
    
    # Create attachment record in database
    attachment_repo = AttachmentRepository(db)
    db_attachment = attachment_repo.create_attachment(
        bug_id=bug_id,
        filename=filename,
        file_extension=file_extension,
        file_type=file_type,
        file_size=file_size,
        file_path=file_path,
        description=description,
        uploader=uploader
    )
    
    # Convert to Pydantic model for response
    return attachment_repo.to_pydantic_model(db_attachment)


@router.get("/bugs/{bug_id}/attachments", response_model=List[Attachment])
def get_bug_attachments(bug_id: str, db: Session = Depends(get_db_session)):
    """Get all attachments for a specific bug."""
    # Check if bug exists
    bug_repo = BugRepository(db)
    bug = bug_repo.get_bug_by_id(bug_id)
    if not bug:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bug with ID {bug_id} not found"
        )
    
    # Get attachments
    attachment_repo = AttachmentRepository(db)
    attachments = attachment_repo.get_attachments_by_bug_id(bug_id)
    
    # Convert to Pydantic models
    return [attachment_repo.to_pydantic_model(attachment) for attachment in attachments]


@router.get("/attachments/{attachment_id}", response_model=Attachment)
def get_attachment(attachment_id: str, db: Session = Depends(get_db_session)):
    """Get a specific attachment by ID."""
    attachment_repo = AttachmentRepository(db)
    attachment = attachment_repo.get_attachment_by_id(attachment_id)
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attachment with ID {attachment_id} not found"
        )
    
    return attachment_repo.to_pydantic_model(attachment)


@router.get("/attachments/{attachment_id}/content")
async def get_attachment_content(attachment_id: str, db: Session = Depends(get_db_session)):
    """Get the content of a specific attachment."""
    attachment_repo = AttachmentRepository(db)
    attachment = attachment_repo.get_attachment_by_id(attachment_id)
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attachment with ID {attachment_id} not found"
        )
    
    # Different handling based on attachment type
    if attachment.file_type == str(AttachmentType.TEXT.value):
        if attachment.text_contents and len(attachment.text_contents) > 0:
            text_content = attachment.text_contents[0]
            return {
                "type": "text",
                "content": text_content.content,
                "metadata": {
                    "language": text_content.language,
                    "encoding": text_content.encoding,
                    "extraction_method": text_content.extraction_method
                }
            }
    elif attachment.file_type == str(AttachmentType.IMAGE.value):
        if attachment.image_contents and len(attachment.image_contents) > 0:
            image_content = attachment.image_contents[0]
            return {
                "type": "image",
                "file_path": image_content.file_path,
                "metadata": image_content.meta_data
            }
    elif attachment.file_type == str(AttachmentType.PDF.value):
        if attachment.pdf_content:
            return {
                "type": "pdf",
                "file_path": attachment.file_path,
                "pages": [
                    {"page_number": page.page_number, "text": page.text}
                    for page in attachment.pdf_content.pages
                ]
            }
    elif attachment.file_type == str(AttachmentType.VIDEO.value):
        if attachment.video_content:
            return {
                "type": "video",
                "file_path": attachment.file_path,
                "metadata": attachment.video_content.meta_data,
                "frame_count": len(attachment.video_content.frames)
            }
    
    # Default to returning basic file info
    return {
        "type": attachment.file_type,
        "file_path": attachment.file_path,
        "file_size": attachment.file_size
    }


@router.put("/attachments/{attachment_id}", response_model=Attachment)
def update_attachment(
    attachment_id: str, 
    attachment_update: AttachmentUpdate, 
    db: Session = Depends(get_db_session)
):
    """Update an attachment."""
    attachment_repo = AttachmentRepository(db)
    existing_attachment = attachment_repo.get_attachment_by_id(attachment_id)
    if not existing_attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attachment with ID {attachment_id} not found"
        )
    
    # Filter out None values from attachment_update
    update_data = {k: v for k, v in attachment_update.model_dump().items() if v is not None}
    
    if not update_data:
        # No updates needed
        return attachment_repo.to_pydantic_model(existing_attachment)
    
    # Convert enum values to strings if present
    if 'processing_status' in update_data and update_data['processing_status'] is not None:
        update_data['processing_status'] = str(update_data['processing_status'].value)
    
    updated_attachment = attachment_repo.update_by_id(attachment_id, update_data)
    return attachment_repo.to_pydantic_model(updated_attachment)
