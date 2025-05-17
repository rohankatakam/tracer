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
    import base64
    from pathlib import Path
    
    attachment_repo = AttachmentRepository(db)
    attachment = attachment_repo.get_attachment_by_id(attachment_id)
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attachment with ID {attachment_id} not found"
        )
    
    # Make sure the file exists
    if not os.path.exists(attachment.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attachment file not found on disk"
        )
        
    # Handle image files (png, jpg, jpeg) directly
    if attachment.file_type in [
        str(AttachmentType.IMAGE_PNG.value),
        str(AttachmentType.IMAGE_JPG.value),
        str(AttachmentType.IMAGE_JPEG.value)
    ]:
        try:
            with open(attachment.file_path, "rb") as img_file:
                base64_content = base64.b64encode(img_file.read()).decode('utf-8')
                return {
                    "content_type": f"image/{attachment.file_extension}",
                    "base64_content": base64_content,
                    "filename": attachment.filename,
                    "file_size": attachment.file_size
                }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error reading image file: {str(e)}"
            )
    
    # Text file handling        
    elif attachment.file_type == str(AttachmentType.TEXT.value):
        try:
            with open(attachment.file_path, "r") as text_file:
                text_content = text_file.read()
                return {
                    "content_type": "text/plain",
                    "text_content": text_content,
                    "filename": attachment.filename,
                    "file_size": attachment.file_size
                }
        except Exception as e:
            # If we can't read as text, try processed content if available
            if attachment.text_contents and len(attachment.text_contents) > 0:
                text_content = attachment.text_contents[0]
                return {
                    "content_type": "text/plain",
                    "text_content": text_content.content,
                    "metadata": {
                        "language": text_content.language,
                        "encoding": text_content.encoding,
                        "extraction_method": text_content.extraction_method
                    }
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error reading text file: {str(e)}"
                )
    
    # PDF handling
    elif attachment.file_type == str(AttachmentType.PDF.value) or attachment.file_extension == 'pdf':
        try:
            # If we have processed PDF content, return that
            if attachment.pdf_content:
                return {
                    "content_type": "application/pdf",
                    "pages": [
                        {"page_number": page.page_number, "text": page.text}
                        for page in attachment.pdf_content.pages
                    ],
                    "filename": attachment.filename,
                    "file_size": attachment.file_size
                }
            # Otherwise return the raw PDF file
            else:
                with open(attachment.file_path, "rb") as pdf_file:
                    base64_content = base64.b64encode(pdf_file.read()).decode('utf-8')
                    return {
                        "content_type": "application/pdf",
                        "base64_content": base64_content,
                        "filename": attachment.filename,
                        "file_size": attachment.file_size
                    }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error reading PDF file: {str(e)}"
            )
            
    # Video handling
    elif attachment.file_type == str(AttachmentType.VIDEO.value):
        if attachment.video_content:
            return {
                "content_type": "video/mp4",
                "file_path": attachment.file_path,
                "metadata": attachment.video_content.meta_data,
                "frame_count": len(attachment.video_content.frames),
                "filename": attachment.filename,
                "file_size": attachment.file_size
            }
        else:
            # Return basic info if no processed content
            return {
                "content_type": "video/mp4",
                "message": "Video processing not available",
                "filename": attachment.filename,
                "file_size": attachment.file_size
            }
    
    # Default to returning basic file info for other types
    return {
        "content_type": f"application/{attachment.file_extension}",
        "message": "Content preview not available for this file type",
        "filename": attachment.filename,
        "file_size": attachment.file_size,
        "file_type": attachment.file_type
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
