"""
Attachment Repository

This module provides repository classes for attachment-related operations using SQLAlchemy ORM.
It replaces the pickle-based implementation with proper database persistence.
"""

from typing import List, Optional, Dict, Any, Union
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime
import os
from api.schemas import Attachment as PydanticAttachment

from core.models.db import Attachment, TextContent, ImageContent, PDFContent, VideoContent
from core.repositories.base_repository import BaseRepository
from core.models.attachment_schema import BugAttachment as PydanticBugAttachment
from core.models.attachment_schema import AttachmentContent, AttachmentType, AttachmentProcessingStatus


class AttachmentRepository(BaseRepository[Attachment]):
    """Repository for Attachment model operations."""
    
    def __init__(self, session: Session):
        """Initialize with a database session."""
        super().__init__(session, Attachment)
    
    def get_attachment_by_id(self, attachment_id: str) -> Optional[Attachment]:
        """
        Get an attachment by its ID.
        
        Args:
            attachment_id: ID of the attachment to retrieve
            
        Returns:
            Attachment instance if found, None otherwise
        """
        return self.get_by_id(attachment_id)
    
    def get_attachments_by_bug_id(self, bug_id: str) -> List[Attachment]:
        """
        Get all attachments for a specific bug.
        
        Args:
            bug_id: ID of the bug
            
        Returns:
            List of attachments for the bug
        """
        return self.get_by_filter(bug_id=bug_id)
    
    def create_attachment(self, 
                         bug_id: str, 
                         filename: str, 
                         file_extension: str, 
                         file_type: Union[str, AttachmentType], 
                         file_size: int,
                         file_path: str = None,
                         description: str = None,
                         uploader: str = None) -> Attachment:
        """
        Create a new attachment.
        
        Args:
            bug_id: ID of the bug this attachment belongs to
            filename: Original filename
            file_extension: File extension
            file_type: Type of the attachment
            file_size: Size in bytes
            file_path: Path to the file
            description: Attachment description
            uploader: Person who uploaded the attachment
            
        Returns:
            Created Attachment instance
        """
        # Convert AttachmentType enum to string if necessary
        if isinstance(file_type, AttachmentType):
            file_type = str(file_type.value)
            
        attachment = Attachment(
            bug_id=bug_id,
            filename=filename,
            file_extension=file_extension,
            file_type=file_type,
            file_size=file_size,
            file_path=file_path,
            description=description,
            uploader=uploader,
            upload_timestamp=datetime.now(),
            processing_status="pending"
        )
        return self.create(attachment)
    
    def update_processing_status(self, 
                               attachment_id: str, 
                               status: Union[str, AttachmentProcessingStatus],
                               error_message: str = None) -> Optional[Attachment]:
        """
        Update an attachment's processing status.
        
        Args:
            attachment_id: ID of the attachment
            status: New status
            error_message: Error message if status is 'failed'
            
        Returns:
            Updated Attachment instance if found, None otherwise
        """
        # Convert AttachmentProcessingStatus enum to string if necessary
        if isinstance(status, AttachmentProcessingStatus):
            status = str(status.value)
            
        update_data = {
            "processing_status": status,
            "last_processed_timestamp": datetime.now()
        }
        
        if error_message:
            update_data["processing_error"] = error_message
            
        return self.update_by_id(attachment_id, update_data)
    
    def store_pydantic_attachment(self, attachment: PydanticBugAttachment) -> Attachment:
        """
        Store a Pydantic BugAttachment model in the database.
        
        Args:
            attachment: Pydantic BugAttachment instance
            
        Returns:
            SQLAlchemy Attachment instance
        """
        # Convert Pydantic model to SQLAlchemy model
        db_attachment = Attachment.from_pydantic(attachment)
        
        # Save to database
        return self.create(db_attachment)
    
    def to_pydantic_model(self, attachment: Attachment) -> PydanticAttachment:
        """
        Convert a SQLAlchemy Attachment to a Pydantic Attachment model for API response.
        
        Args:
            attachment: SQLAlchemy Attachment instance
            
        Returns:
            Pydantic Attachment instance with all required fields
        """
        # Determine content type based on file extension
        content_type = "application/octet-stream"
        if attachment.file_extension:
            if attachment.file_extension.lower() in ['jpg', 'jpeg']:
                content_type = "image/jpeg"
            elif attachment.file_extension.lower() == 'png':
                content_type = "image/png"
            elif attachment.file_extension.lower() == 'pdf':
                content_type = "application/pdf"
            elif attachment.file_extension.lower() == 'txt':
                content_type = "text/plain"
            elif attachment.file_extension.lower() == 'mp4':
                content_type = "video/mp4"
            else:
                content_type = f"application/{attachment.file_extension.lower()}"
        
        # Create a Pydantic model with all required fields
        return PydanticAttachment(
            attachment_id=attachment.attachment_id,
            bug_id=attachment.bug_id,
            filename=attachment.filename,
            content_type=content_type,
            size=attachment.file_size,
            created_at=attachment.upload_timestamp,
            content_id=None,  # Optional field
            attachment_type=attachment.file_type,
            processing_status=attachment.processing_status
        )
        

class TextContentRepository(BaseRepository[TextContent]):
    """Repository for TextContent model operations."""
    
    def __init__(self, session: Session):
        """Initialize with a database session."""
        super().__init__(session, TextContent)
    
    def get_text_content_by_id(self, text_id: str) -> Optional[TextContent]:
        """
        Get text content by its ID.
        
        Args:
            text_id: ID of the text content
            
        Returns:
            TextContent instance if found, None otherwise
        """
        return self.get_by_id(text_id)
    
    def create_text_content(self, 
                           content: str,
                           language: str = None,
                           encoding: str = None,
                           extraction_method: str = "direct") -> TextContent:
        """
        Create new text content.
        
        Args:
            content: The text content
            language: Detected language
            encoding: Text encoding
            extraction_method: Method used to extract the text
            
        Returns:
            Created TextContent instance
        """
        text_content = TextContent(
            content=content,
            language=language,
            encoding=encoding,
            extraction_method=extraction_method,
            processing_timestamp=datetime.now()
        )
        return self.create(text_content)


class ImageContentRepository(BaseRepository[ImageContent]):
    """Repository for ImageContent model operations."""
    
    def __init__(self, session: Session):
        """Initialize with a database session."""
        super().__init__(session, ImageContent)
    
    def get_image_content_by_id(self, image_id: str) -> Optional[ImageContent]:
        """
        Get image content by its ID.
        
        Args:
            image_id: ID of the image content
            
        Returns:
            ImageContent instance if found, None otherwise
        """
        return self.get_by_id(image_id)
    
    def create_image_content(self, 
                            metadata: Dict[str, Any],
                            file_path: str = None,
                            storage_location: str = None,
                            ocr_text_id: str = None,
                            ocr_confidence: float = None) -> ImageContent:
        """
        Create new image content.
        
        Args:
            metadata: Image metadata (width, height, format, etc.)
            file_path: Path to the image file
            storage_location: Storage location type
            ocr_text_id: ID of associated OCR text content
            ocr_confidence: OCR confidence score
            
        Returns:
            Created ImageContent instance
        """
        image_content = ImageContent(
            file_path=file_path,
            storage_location=storage_location,
            meta_data=metadata,
            ocr_text_id=ocr_text_id,
            ocr_confidence=ocr_confidence,
            processing_timestamp=datetime.now()
        )
        return self.create(image_content)


class PDFContentRepository(BaseRepository[PDFContent]):
    """Repository for PDFContent model operations."""
    
    def __init__(self, session: Session):
        """Initialize with a database session."""
        super().__init__(session, PDFContent)
    
    def get_pdf_content_by_id(self, pdf_id: str) -> Optional[PDFContent]:
        """
        Get PDF content by its ID.
        
        Args:
            pdf_id: ID of the PDF content
            
        Returns:
            PDFContent instance if found, None otherwise
        """
        return self.get_by_id(pdf_id)


class VideoContentRepository(BaseRepository[VideoContent]):
    """Repository for VideoContent model operations."""
    
    def __init__(self, session: Session):
        """Initialize with a database session."""
        super().__init__(session, VideoContent)
    
    def get_video_content_by_id(self, video_id: str) -> Optional[VideoContent]:
        """
        Get video content by its ID.
        
        Args:
            video_id: ID of the video content
            
        Returns:
            VideoContent instance if found, None otherwise
        """
        return self.get_by_id(video_id)
