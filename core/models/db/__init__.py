"""
Database models for the Bug Attachment Processing system.

This package provides SQLAlchemy ORM models for persisting bug data and attachments
in a PostgreSQL database, while maintaining compatibility with the Pydantic models
for API interactions and validation.
"""

# Import all models to make them available as db.ModelName
from core.models.db.bug import Bug
from core.models.db.attachment import Attachment
from core.models.db.text_content import TextContent
from core.models.db.image_content import ImageContent
from core.models.db.pdf_page import PDFPage
from core.models.db.pdf_content import PDFContent
from core.models.db.video_frame import VideoFrame
from core.models.db.video_content import VideoContent

# Import association tables
from core.models.db.base import (
    attachment_text_association,
    attachment_image_association,
    pdf_page_text_association,
    pdf_page_image_association
)

# Re-export all models for easy importing
__all__ = [
    'Bug',
    'Attachment',
    'TextContent', 
    'ImageContent',
    'PDFPage',
    'PDFContent',
    'VideoFrame',
    'VideoContent',
    'attachment_text_association',
    'attachment_image_association',
    'pdf_page_text_association',
    'pdf_page_image_association'
]
