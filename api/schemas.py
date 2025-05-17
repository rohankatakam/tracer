"""
Pydantic models for API request/response validation.

This module defines Pydantic schemas for the Bug Attachment Processing API.
These models are used for request validation and response serialization.
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import uuid4
from core.models.attachment_schema import AttachmentType, AttachmentProcessingStatus


class BugBase(BaseModel):
    """Base Pydantic model for bug data."""
    title: str
    description: Optional[str] = None
    reporter: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = "NEW"


class BugCreate(BugBase):
    """Schema for creating a new bug."""
    pass


class BugUpdate(BaseModel):
    """Schema for updating a bug."""
    title: Optional[str] = None
    description: Optional[str] = None
    reporter: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None


class AttachmentContent(BaseModel):
    """Attachment content references."""
    text_content_ids: List[str] = Field(default_factory=list)
    image_content_ids: List[str] = Field(default_factory=list)
    pdf_content_id: Optional[str] = None
    video_content_id: Optional[str] = None


class AttachmentBase(BaseModel):
    """Base Pydantic model for attachment data."""
    filename: str
    file_extension: str
    file_type: AttachmentType
    file_size: int
    description: Optional[str] = None
    uploader: Optional[str] = None


class AttachmentCreate(AttachmentBase):
    """Schema for creating a new attachment."""
    pass


class AttachmentUpdate(BaseModel):
    """Schema for updating an attachment."""
    description: Optional[str] = None
    processing_status: Optional[AttachmentProcessingStatus] = None
    processing_error: Optional[str] = None


class Bug(BugBase):
    """Complete bug model with all fields."""
    bug_id: str
    created_at: datetime
    updated_at: datetime
    attachment_count: Optional[int] = 0

    class Config:
        from_attributes = True


class Attachment(AttachmentBase):
    """Complete attachment model with all fields."""
    attachment_id: str
    bug_id: str
    upload_timestamp: datetime
    processing_status: AttachmentProcessingStatus
    processing_error: Optional[str] = None
    last_processed_timestamp: Optional[datetime] = None
    content: AttachmentContent = Field(default_factory=AttachmentContent)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


class TextContent(BaseModel):
    """Text content model."""
    text_id: str
    content: str
    language: Optional[str] = None
    encoding: Optional[str] = None
    extraction_method: str
    processing_timestamp: datetime

    class Config:
        from_attributes = True


class ImageContent(BaseModel):
    """Image content model."""
    image_id: str
    file_path: Optional[str] = None
    storage_location: Optional[str] = None
    meta_data: Dict[str, Any] = Field(default_factory=dict)
    ocr_text_id: Optional[str] = None
    ocr_confidence: Optional[float] = None
    processing_timestamp: datetime

    class Config:
        from_attributes = True
