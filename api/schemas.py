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


class CommentBase(BaseModel):
    """Base Pydantic model for comment data."""
    author: str
    text: str
    is_private: Optional[bool] = False
    attachment_ids: List[str] = Field(default_factory=list, description="IDs of attachments referenced in this comment")


class CommentCreate(CommentBase):
    """Schema for creating a new comment."""
    pass


class CommentUpdate(BaseModel):
    """Schema for updating a comment."""
    text: Optional[str] = None
    is_private: Optional[bool] = None
    attachment_ids: Optional[List[str]] = None


class Comment(CommentBase):
    """Complete comment model with all fields."""
    comment_id: str
    bug_id: str
    timestamp: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {"example": {
            "comment_id": "550e8400-e29b-41d4-a716-446655440000",
            "bug_id": "550e8400-e29b-41d4-a716-446655440001",
            "author": "Jane Doe",
            "text": "This is a comment on the bug.",
            "timestamp": "2023-01-01T12:00:00",
            "is_private": False,
            "attachment_ids": ["550e8400-e29b-41d4-a716-446655440002"]
        }}
        
    @classmethod
    def from_orm(cls, obj):
        # Check if there's a to_dict method and use it for custom serialization
        if hasattr(obj, 'to_dict') and callable(obj.to_dict):
            return cls(**obj.to_dict())
        return super().from_orm(obj)
