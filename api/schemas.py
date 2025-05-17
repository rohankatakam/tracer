"""
Pydantic models for API request/response validation.

This module defines Pydantic schemas for the Bug Attachment Processing API.
These models are used for request validation and response serialization.
"""

from typing import List, Optional, Dict, Any, Union, Literal
from datetime import datetime
from pydantic import BaseModel, Field, model_validator
from uuid import uuid4
from enum import Enum
from core.models.attachment_schema import AttachmentType, AttachmentProcessingStatus
from core.models.db.bug import (
    BugSchemaType, BugStatus, BaseSeverity, BaseStatus,
    MozillaSeverity, MozillaPriority, MozillaStatus, MozillaResolution,
    ChromiumPriority, ChromiumType, ChromiumStatus
)


# Common base class for all bug schemas
class BugBase(BaseModel):
    """Base Pydantic model for common bug data."""
    title: str
    description: Optional[str] = None
    reporter: Optional[str] = None
    product: Optional[str] = None
    component: Optional[str] = None
    version: Optional[str] = None
    platform: Optional[str] = None
    operating_system: Optional[str] = None
    schema_type: BugSchemaType = Field(default=BugSchemaType.BASE)
    
    # Additional data for flexible extensions
    extra_data: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = {
        "use_enum_values": True
    }

# Base bug schema
class BaseBugSchema(BugBase):
    """Base bug schema type with standard severity and status."""
    severity: Optional[BaseSeverity] = None
    status: Optional[BaseStatus] = Field(default=BaseStatus.NEW)
    
    model_config = {
        "use_enum_values": True
    }

# Mozilla/Bugzilla bug schema
class MozillaBugSchema(BugBase):
    """Mozilla/Bugzilla specific bug schema."""
    mozilla_severity: Optional[MozillaSeverity] = None
    mozilla_priority: Optional[MozillaPriority] = None
    mozilla_status: Optional[MozillaStatus] = None
    mozilla_resolution: Optional[MozillaResolution] = None
    mozilla_version: Optional[str] = None
    mozilla_component: Optional[str] = None
    mozilla_keywords: Optional[str] = None
    
    model_config = {
        "use_enum_values": True
    }

# Chromium bug schema
class ChromiumBugSchema(BugBase):
    """Chromium specific bug schema."""
    chromium_priority: Optional[ChromiumPriority] = None
    chromium_type: Optional[ChromiumType] = None
    chromium_status: Optional[ChromiumStatus] = None
    chromium_component: Optional[str] = None
    chromium_owner: Optional[str] = None
    chromium_cc: Optional[str] = None
    chromium_labels: Optional[str] = None
    
    model_config = {
        "use_enum_values": True
    }

# Oracle bug schema
class OracleBugSchema(BugBase):
    """Oracle specific bug schema."""
    oracle_status_code: Optional[int] = None
    oracle_status_description: Optional[str] = None
    oracle_severity: Optional[str] = None
    oracle_priority: Optional[str] = None
    oracle_close_reason: Optional[str] = None
    oracle_environment: Optional[str] = None
    
    model_config = {
        "use_enum_values": True
    }

# Schema for creating a new bug
class BugCreate(BaseModel):
    """Schema for creating a new bug that supports different schema types."""
    # Common fields for all bug types
    title: str
    description: Optional[str] = None
    reporter: Optional[str] = None
    product: Optional[str] = None
    component: Optional[str] = None
    version: Optional[str] = None
    platform: Optional[str] = None
    operating_system: Optional[str] = None
    schema_type: BugSchemaType = Field(default=BugSchemaType.BASE)
    
    # Base type fields
    severity: Optional[BaseSeverity] = None
    status: Optional[BaseStatus] = None
    
    # Mozilla/Bugzilla specific fields
    mozilla_severity: Optional[MozillaSeverity] = None
    mozilla_priority: Optional[MozillaPriority] = None
    mozilla_status: Optional[MozillaStatus] = None
    mozilla_resolution: Optional[MozillaResolution] = None
    mozilla_version: Optional[str] = None
    mozilla_component: Optional[str] = None
    mozilla_keywords: Optional[str] = None
    
    # Chromium specific fields
    chromium_priority: Optional[ChromiumPriority] = None
    chromium_type: Optional[ChromiumType] = None
    chromium_status: Optional[ChromiumStatus] = None
    chromium_component: Optional[str] = None
    chromium_owner: Optional[str] = None
    chromium_cc: Optional[str] = None
    chromium_labels: Optional[str] = None
    
    # Oracle specific fields
    oracle_status_code: Optional[int] = None
    oracle_status_description: Optional[str] = None
    oracle_severity: Optional[str] = None
    oracle_priority: Optional[str] = None
    oracle_close_reason: Optional[str] = None
    oracle_environment: Optional[str] = None
    
    # Additional data for flexible extensions
    extra_data: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = {
        "use_enum_values": True
    }
        
    @model_validator(mode='after')
    def validate_schema_specific_fields(self):
        """Validate that the appropriate fields are set based on schema_type."""
        schema_type = self.schema_type
        
        # Set default status based on schema type if not provided
        if schema_type == BugSchemaType.BASE and not self.status:
            self.status = BaseStatus.NEW.value
        elif schema_type == BugSchemaType.MOZILLA and not self.mozilla_status:
            self.mozilla_status = MozillaStatus.NEW.value
        elif schema_type == BugSchemaType.CHROMIUM and not self.chromium_status:
            self.chromium_status = ChromiumStatus.UNTRIAGED.value
            
        return self


class BugUpdate(BaseModel):
    """Schema for updating a bug that supports different schema types."""
    # Common fields for all bug types
    title: Optional[str] = None
    description: Optional[str] = None
    reporter: Optional[str] = None
    product: Optional[str] = None
    component: Optional[str] = None
    version: Optional[str] = None
    platform: Optional[str] = None
    operating_system: Optional[str] = None
    
    # Base type fields
    severity: Optional[BaseSeverity] = None
    status: Optional[BaseStatus] = None
    
    # Mozilla/Bugzilla specific fields
    mozilla_severity: Optional[MozillaSeverity] = None
    mozilla_priority: Optional[MozillaPriority] = None
    mozilla_status: Optional[MozillaStatus] = None
    mozilla_resolution: Optional[MozillaResolution] = None
    mozilla_version: Optional[str] = None
    mozilla_component: Optional[str] = None
    mozilla_keywords: Optional[str] = None
    
    # Chromium specific fields
    chromium_priority: Optional[ChromiumPriority] = None
    chromium_type: Optional[ChromiumType] = None
    chromium_status: Optional[ChromiumStatus] = None
    chromium_component: Optional[str] = None
    chromium_owner: Optional[str] = None
    chromium_cc: Optional[str] = None
    chromium_labels: Optional[str] = None
    
    # Oracle specific fields
    oracle_status_code: Optional[int] = None
    oracle_status_description: Optional[str] = None
    oracle_severity: Optional[str] = None
    oracle_priority: Optional[str] = None
    oracle_close_reason: Optional[str] = None
    oracle_environment: Optional[str] = None
    
    # Additional data for flexible extensions
    extra_data: Optional[Dict[str, Any]] = None
    
    model_config = {
        "use_enum_values": True
    }


class Attachment(BaseModel):
    """Schema for attachment metadata."""
    attachment_id: str
    bug_id: str
    filename: str
    content_type: str
    size: int
    created_at: datetime
    content_id: Optional[str] = None
    attachment_type: Optional[AttachmentType] = None
    processing_status: Optional[AttachmentProcessingStatus] = None
    
    model_config = {
        "from_attributes": True
    }


class TextContent(BaseModel):
    """Schema for text content extracted from attachments."""
    content_id: str
    text: str
    language: Optional[str] = None
    
    model_config = {
        "from_attributes": True
    }


class ImageContent(BaseModel):
    """Schema for image content extracted from attachments."""
    content_id: str
    width: int
    height: int
    format: str
    has_text: bool = False
    extracted_text: Optional[str] = None
    text_confidence: Optional[float] = None
    ocr_language: Optional[str] = None
    
    model_config = {
        "from_attributes": True
    }


class PDFPage(BaseModel):
    """Schema for a page within a PDF document."""
    page_number: int
    text: Optional[str] = None
    has_images: bool = False
    image_count: int = 0
    page_width: Optional[int] = None
    page_height: Optional[int] = None
    

class PDFContent(BaseModel):
    """Schema for PDF content extracted from attachments."""
    content_id: str
    page_count: int
    has_text: bool = False
    pages: List[PDFPage] = []
    
    model_config = {
        "from_attributes": True
    }


class VideoFrame(BaseModel):
    """Schema for a frame within a video."""
    timestamp: float  # Timestamp in seconds
    has_text: bool = False
    extracted_text: Optional[str] = None
    text_confidence: Optional[float] = None
    

class VideoContent(BaseModel):
    """Schema for video content extracted from attachments."""
    content_id: str
    duration: float  # Duration in seconds
    width: int
    height: int
    format: str
    has_audio: bool = False
    key_frames: List[VideoFrame] = []
    
    model_config = {
        "from_attributes": True
    }


class Comment(BaseModel):
    """Schema for bug comments."""
    comment_id: str
    bug_id: str
    author: str
    text: str
    timestamp: datetime
    is_private: bool = False
    attachment_ids: List[str] = []
    
    model_config = {
        "from_attributes": True
    }


class CommentCreate(BaseModel):
    """Schema for creating a new comment."""
    author: str
    text: str
    is_private: bool = False
    attachment_ids: List[str] = []
    

class CommentUpdate(BaseModel):
    """Schema for updating an existing comment."""
    text: Optional[str] = None
    is_private: Optional[bool] = None
    

class AttachmentCreate(BaseModel):
    """Schema for creating a new attachment (metadata only)."""
    filename: str
    content_type: str
    size: int
    

class AttachmentUpdate(BaseModel):
    """Schema for updating an existing attachment."""
    filename: Optional[str] = None
    content_type: Optional[str] = None
    

class AttachmentProcessingUpdate(BaseModel):
    """Schema for updating attachment processing status and metadata."""
    attachment_type: Optional[AttachmentType] = None
    processing_status: Optional[AttachmentProcessingStatus] = None
    content_id: Optional[str] = None
    processing_error: Optional[str] = None


class Bug(BaseModel):
    """Complete bug model with all fields and schema-specific attributes."""
    # Common fields for all bug types
    bug_id: str
    title: str
    description: Optional[str] = None
    reporter: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    product: Optional[str] = None
    component: Optional[str] = None
    version: Optional[str] = None
    platform: Optional[str] = None
    operating_system: Optional[str] = None
    schema_type: str
    attachment_count: Optional[int] = 0
    
    # Base type fields
    severity: Optional[str] = None
    status: Optional[str] = None
    
    # Mozilla/Bugzilla specific fields
    mozilla_severity: Optional[str] = None
    mozilla_priority: Optional[str] = None
    mozilla_status: Optional[str] = None
    mozilla_resolution: Optional[str] = None
    mozilla_version: Optional[str] = None
    mozilla_component: Optional[str] = None
    mozilla_keywords: Optional[str] = None
    
    # Chromium specific fields
    chromium_priority: Optional[str] = None
    chromium_type: Optional[str] = None
    chromium_status: Optional[str] = None
    chromium_component: Optional[str] = None
    chromium_owner: Optional[str] = None
    chromium_cc: Optional[str] = None
    chromium_labels: Optional[str] = None
    
    # Oracle specific fields
    oracle_status_code: Optional[int] = None
    oracle_status_description: Optional[str] = None
    oracle_severity: Optional[str] = None
    oracle_priority: Optional[str] = None
    oracle_close_reason: Optional[str] = None
    oracle_environment: Optional[str] = None
    
    # Additional data
    extra_data: Dict[str, Any] = Field(default_factory=dict)

    # Combined model configuration
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "bug_id": "550e8400-e29b-41d4-a716-446655440000",
                    "title": "Application crashes when large file is loaded",
                    "description": "When loading files >100MB, the application crashes with an out of memory error",
                    "reporter": "Jane Doe",
                    "created_at": "2025-05-16T10:00:00",
                    "updated_at": "2025-05-16T11:30:00",
                    "schema_type": "base",
                    "severity": "high",
                    "status": "IN_PROGRESS",
                    "product": "FileProcessor",
                    "component": "FileLoader",
                    "version": "1.2.3"
                }
            ]
        }
    }
