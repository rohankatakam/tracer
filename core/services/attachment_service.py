"""
Attachment Service

This module provides a service layer for working with attachments and their content.
It replaces the pickle-based attachment_db.py with a SQLAlchemy ORM-based implementation
while maintaining a compatible API.
"""

import logging
from typing import List, Optional, Dict, Any
from contextlib import contextmanager
from uuid import uuid4

from core.database.engine import db_session
from core.repositories import (
    AttachmentRepository,
    TextContentRepository,
    ImageContentRepository,
    PDFContentRepository,
    VideoContentRepository
)
from core.models.attachment_schema import (
    BugAttachment, 
    TextContent, 
    ImageContent, 
    PDFContent, 
    VideoContent, 
    AttachmentDatabase,
    AttachmentProcessingStatus
)

# Set up logging
logger = logging.getLogger("attachment_service")


# Attachment functions
def store_attachment(attachment: BugAttachment) -> bool:
    """
    Store an attachment in the database.
    
    Args:
        attachment: The attachment to store
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with db_session() as session:
            repo = AttachmentRepository(session)
            repo.store_pydantic_attachment(attachment)
            
            # Process any related content that needs to be stored
            if attachment.content.text_content_ids:
                text_repo = TextContentRepository(session)
                for text_id in attachment.content.text_content_ids:
                    text_content = get_text_content(text_id)
                    if text_content:
                        db_text = text_repo.get_text_content_by_id(text_id)
                        if not db_text:
                            text_repo.create(text_repo.model_cls.from_pydantic(text_content))
            
            if attachment.content.image_content_ids:
                image_repo = ImageContentRepository(session)
                for image_id in attachment.content.image_content_ids:
                    image_content = get_image_content(image_id)
                    if image_content:
                        db_image = image_repo.get_image_content_by_id(image_id)
                        if not db_image:
                            image_repo.create(image_repo.model_cls.from_pydantic(image_content))
            
            if attachment.content.pdf_content_id:
                pdf_repo = PDFContentRepository(session)
                pdf_content = get_pdf_content(attachment.content.pdf_content_id)
                if pdf_content:
                    db_pdf = pdf_repo.get_pdf_content_by_id(attachment.content.pdf_content_id)
                    if not db_pdf:
                        pdf_repo.create(pdf_repo.model_cls.from_pydantic(pdf_content))
            
            if attachment.content.video_content_id:
                video_repo = VideoContentRepository(session)
                video_content = get_video_content(attachment.content.video_content_id)
                if video_content:
                    db_video = video_repo.get_video_content_by_id(attachment.content.video_content_id)
                    if not db_video:
                        video_repo.create(video_repo.model_cls.from_pydantic(video_content))
                
        return True
    except Exception as e:
        logger.error(f"Error storing attachment: {str(e)}")
        return False


def get_attachment(attachment_id: str) -> Optional[BugAttachment]:
    """
    Get an attachment from the database.
    
    Args:
        attachment_id: ID of the attachment to get
        
    Returns:
        The attachment if found, None otherwise
    """
    try:
        with db_session() as session:
            repo = AttachmentRepository(session)
            attachment = repo.get_attachment_by_id(attachment_id)
            if attachment:
                return repo.to_pydantic_model(attachment)
        return None
    except Exception as e:
        logger.error(f"Error getting attachment: {str(e)}")
        return None


def get_attachments_by_bug_id(bug_id: str) -> List[BugAttachment]:
    """
    Get all attachments for a bug.
    
    Args:
        bug_id: ID of the bug
        
    Returns:
        List of attachments for the bug
    """
    try:
        with db_session() as session:
            repo = AttachmentRepository(session)
            attachments = repo.get_attachments_by_bug_id(bug_id)
            return [repo.to_pydantic_model(attachment) for attachment in attachments]
    except Exception as e:
        logger.error(f"Error getting attachments by bug ID: {str(e)}")
        return []


# Text content functions
def store_text_content(text_content: TextContent) -> bool:
    """
    Store text content in the database.
    
    Args:
        text_content: The text content to store
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with db_session() as session:
            repo = TextContentRepository(session)
            db_text = repo.get_text_content_by_id(text_content.text_id)
            
            if db_text:
                # Update existing
                for key, value in text_content.dict().items():
                    if key != "text_id" and hasattr(db_text, key):
                        setattr(db_text, key, value)
                repo.update(db_text)
            else:
                # Create new
                repo.create(repo.model_cls.from_pydantic(text_content))
                
        return True
    except Exception as e:
        logger.error(f"Error storing text content: {str(e)}")
        return False


def get_text_content(text_id: str) -> Optional[TextContent]:
    """
    Get text content from the database.
    
    Args:
        text_id: ID of the text content to get
        
    Returns:
        The text content if found, None otherwise
    """
    try:
        with db_session() as session:
            repo = TextContentRepository(session)
            text_content = repo.get_text_content_by_id(text_id)
            if text_content:
                return text_content.to_pydantic()
        return None
    except Exception as e:
        logger.error(f"Error getting text content: {str(e)}")
        return None


# Image content functions
def store_image_content(image_content: ImageContent) -> bool:
    """
    Store image content in the database.
    
    Args:
        image_content: The image content to store
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with db_session() as session:
            repo = ImageContentRepository(session)
            db_image = repo.get_image_content_by_id(image_content.image_id)
            
            if db_image:
                # Update existing
                metadata_dict = image_content.metadata.dict() if hasattr(image_content.metadata, "dict") else image_content.metadata
                
                db_image.file_path = image_content.file_path
                db_image.storage_location = image_content.storage_location
                db_image.meta_data = metadata_dict
                db_image.ocr_text_id = image_content.ocr_text_id
                db_image.ocr_confidence = image_content.ocr_confidence
                db_image.processing_timestamp = image_content.processing_timestamp
                
                repo.update(db_image)
            else:
                # Create new
                repo.create(repo.model_cls.from_pydantic(image_content))
                
        return True
    except Exception as e:
        logger.error(f"Error storing image content: {str(e)}")
        return False


def get_image_content(image_id: str) -> Optional[ImageContent]:
    """
    Get image content from the database.
    
    Args:
        image_id: ID of the image content to get
        
    Returns:
        The image content if found, None otherwise
    """
    try:
        with db_session() as session:
            repo = ImageContentRepository(session)
            image_content = repo.get_image_content_by_id(image_id)
            if image_content:
                return image_content.to_pydantic()
        return None
    except Exception as e:
        logger.error(f"Error getting image content: {str(e)}")
        return None


# PDF content functions
def store_pdf_content(pdf_content: PDFContent) -> bool:
    """
    Store PDF content in the database.
    
    Args:
        pdf_content: The PDF content to store
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with db_session() as session:
            repo = PDFContentRepository(session)
            db_pdf = repo.get_pdf_content_by_id(pdf_content.pdf_id)
            
            if db_pdf:
                # Update is more complex due to nested objects (pages)
                # This is a simplified approach
                db_pdf.file_path = pdf_content.file_path
                db_pdf.storage_location = pdf_content.storage_location
                db_pdf.title = pdf_content.title
                db_pdf.author = pdf_content.author
                db_pdf.creation_date = pdf_content.creation_date
                db_pdf.modification_date = pdf_content.modification_date
                db_pdf.num_pages = pdf_content.num_pages
                db_pdf.processing_timestamp = pdf_content.processing_timestamp
                
                repo.update(db_pdf)
            else:
                # For new PDFs, we need to create the PDFContent first,
                # then create the pages and associate them
                # This is complex and would need additional repositories and transactions
                # A simplified approach would be to convert using the from_pydantic method
                
                # Create PDF Content
                pdf_model = repo.model_cls.from_pydantic(pdf_content)
                pdf_model = repo.create(pdf_model)
                
                # For a complete implementation, we'd need to handle pages, texts, and images
        
        return True
    except Exception as e:
        logger.error(f"Error storing PDF content: {str(e)}")
        return False


def get_pdf_content(pdf_id: str) -> Optional[PDFContent]:
    """
    Get PDF content from the database.
    
    Args:
        pdf_id: ID of the PDF content to get
        
    Returns:
        The PDF content if found, None otherwise
    """
    try:
        with db_session() as session:
            repo = PDFContentRepository(session)
            pdf_content = repo.get_pdf_content_by_id(pdf_id)
            if pdf_content:
                return pdf_content.to_pydantic()
        return None
    except Exception as e:
        logger.error(f"Error getting PDF content: {str(e)}")
        return None


# Video content functions
def store_video_content(video_content: VideoContent) -> bool:
    """
    Store video content in the database.
    
    Args:
        video_content: The video content to store
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with db_session() as session:
            repo = VideoContentRepository(session)
            db_video = repo.get_video_content_by_id(video_content.video_id)
            
            if db_video:
                # Update existing (simplified)
                db_video.file_path = video_content.file_path
                db_video.storage_location = video_content.storage_location
                db_video.duration = video_content.duration
                db_video.width = video_content.width
                db_video.height = video_content.height
                db_video.format = video_content.format
                db_video.codec = video_content.codec
                db_video.fps = video_content.fps
                db_video.audio_text_id = video_content.audio_text_id
                db_video.processing_timestamp = video_content.processing_timestamp
                
                repo.update(db_video)
            else:
                # Create new (simplified, doesn't handle frames)
                video_model = repo.model_cls.from_pydantic(video_content)
                repo.create(video_model)
                
        return True
    except Exception as e:
        logger.error(f"Error storing video content: {str(e)}")
        return False


def get_video_content(video_id: str) -> Optional[VideoContent]:
    """
    Get video content from the database.
    
    Args:
        video_id: ID of the video content to get
        
    Returns:
        The video content if found, None otherwise
    """
    try:
        with db_session() as session:
            repo = VideoContentRepository(session)
            video_content = repo.get_video_content_by_id(video_id)
            if video_content:
                return video_content.to_pydantic()
        return None
    except Exception as e:
        logger.error(f"Error getting video content: {str(e)}")
        return None


# Attachment database functions
def get_attachment_database() -> AttachmentDatabase:
    """
    Get the complete attachment database.
    
    Returns:
        The attachment database with all attachments and content
    """
    try:
        with db_session() as session:
            # Get all data using repositories
            attachment_repo = AttachmentRepository(session)
            text_repo = TextContentRepository(session)
            image_repo = ImageContentRepository(session)
            pdf_repo = PDFContentRepository(session)
            video_repo = VideoContentRepository(session)
            
            # Convert SQLAlchemy models to Pydantic models and organize by ID
            attachments = {
                a.attachment_id: attachment_repo.to_pydantic_model(a) 
                for a in attachment_repo.get_all()
            }
            
            text_contents = {
                t.text_id: t.to_pydantic() 
                for t in text_repo.get_all()
            }
            
            image_contents = {
                i.image_id: i.to_pydantic() 
                for i in image_repo.get_all()
            }
            
            pdf_contents = {
                p.pdf_id: p.to_pydantic() 
                for p in pdf_repo.get_all()
            }
            
            video_contents = {
                v.video_id: v.to_pydantic() 
                for v in video_repo.get_all()
            }
            
            # Create and return the attachment database
            return AttachmentDatabase(
                attachments=attachments,
                text_contents=text_contents,
                image_contents=image_contents,
                pdf_contents=pdf_contents,
                video_contents=video_contents
            )
            
    except Exception as e:
        logger.error(f"Error getting attachment database: {str(e)}")
        return AttachmentDatabase()
