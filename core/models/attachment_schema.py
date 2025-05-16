"""
Bug Attachment Schema and Models

This module defines Pydantic models for handling different types of bug attachments:
- Text files (.txt)
- Images (.jpg, .jpeg, .png)
- PDFs (.pdf)
- Videos (.mp4)

It provides a standardized way to represent attachments and their processed content,
supporting the attachment processing pipeline shown in the system architecture.
"""

from typing import List, Dict, Any, Optional, Union, Literal
from enum import Enum
from datetime import datetime
from pathlib import Path
import uuid
from pydantic import BaseModel, Field, validator, root_validator


class AttachmentType(str, Enum):
    """Types of attachments supported by the system."""
    TEXT = "txt"
    IMAGE_JPG = "jpg"
    IMAGE_JPEG = "jpeg"
    IMAGE_PNG = "png"
    PDF = "pdf"
    VIDEO = "mp4"


class AttachmentProcessingStatus(str, Enum):
    """Processing status for attachments."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TextContent(BaseModel):
    """Model for text content extracted from attachments."""
    text_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the text content")
    content: str = Field("", description="The extracted text content")
    language: Optional[str] = Field(None, description="Detected language of the text")
    encoding: Optional[str] = Field(None, description="Text encoding")
    extraction_method: str = Field("direct", description="Method used to extract the text (direct, ocr, etc.)")
    processing_timestamp: datetime = Field(default_factory=datetime.now, description="When the text was processed")
    
    class Config:
        schema_extra = {
            "example": {
                "text_id": "a1b2c3d4-e5f6-g7h8-i9j0",
                "content": "This is a sample text extracted from an attachment.",
                "language": "en",
                "encoding": "UTF-8",
                "extraction_method": "direct",
                "processing_timestamp": "2025-05-16T01:00:00"
            }
        }


class ImageMetadata(BaseModel):
    """Model for image metadata."""
    width: int = Field(..., description="Width of the image in pixels")
    height: int = Field(..., description="Height of the image in pixels")
    format: str = Field(..., description="Format of the image (e.g., JPEG, PNG)")
    color_mode: Optional[str] = Field(None, description="Color mode of the image (e.g., RGB, CMYK)")
    dpi: Optional[int] = Field(None, description="Dots per inch")
    bits_per_pixel: Optional[int] = Field(None, description="Bits per pixel")
    
    class Config:
        schema_extra = {
            "example": {
                "width": 1920,
                "height": 1080,
                "format": "JPEG",
                "color_mode": "RGB",
                "dpi": 72,
                "bits_per_pixel": 24
            }
        }


class ImageContent(BaseModel):
    """Model for image content and metadata."""
    image_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the image content")
    file_path: Optional[str] = Field(None, description="Path to the stored image file")
    storage_location: Optional[str] = Field(None, description="Storage location identifier (DB, file system, etc.)")
    metadata: ImageMetadata = Field(..., description="Metadata about the image")
    ocr_text_id: Optional[str] = Field(None, description="Reference to OCR text extracted from this image")
    ocr_confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score of OCR (0.0 to 1.0)")
    processing_timestamp: datetime = Field(default_factory=datetime.now, description="When the image was processed")
    
    class Config:
        schema_extra = {
            "example": {
                "image_id": "b2c3d4e5-f6g7-h8i9-j0k1",
                "file_path": "/data/images/screenshot_20250516.jpg",
                "storage_location": "file_system",
                "metadata": {
                    "width": 1920,
                    "height": 1080,
                    "format": "JPEG",
                    "color_mode": "RGB",
                    "dpi": 72,
                    "bits_per_pixel": 24
                },
                "ocr_text_id": "c3d4e5f6-g7h8-i9j0-k1l2",
                "ocr_confidence": 0.85,
                "processing_timestamp": "2025-05-16T01:05:00"
            }
        }


class PDFPageContent(BaseModel):
    """Model for the content of a single PDF page."""
    page_number: int = Field(..., description="Page number (0-indexed)")
    text_id: Optional[str] = Field(None, description="Reference to text extracted from this page")
    image_ids: List[str] = Field(default_factory=list, description="References to images extracted from this page")
    has_text: bool = Field(False, description="Whether the page contains text")
    has_images: bool = Field(False, description="Whether the page contains images")
    
    class Config:
        schema_extra = {
            "example": {
                "page_number": 0,
                "text_id": "d4e5f6g7-h8i9-j0k1-l2m3",
                "image_ids": ["e5f6g7h8-i9j0-k1l2-m3n4"],
                "has_text": True,
                "has_images": True
            }
        }


class PDFContent(BaseModel):
    """Model for PDF content and metadata."""
    pdf_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the PDF content")
    file_path: Optional[str] = Field(None, description="Path to the stored PDF file")
    storage_location: Optional[str] = Field(None, description="Storage location identifier (DB, file system, etc.)")
    title: Optional[str] = Field(None, description="Title of the PDF")
    author: Optional[str] = Field(None, description="Author of the PDF")
    creation_date: Optional[datetime] = Field(None, description="Creation date of the PDF")
    modification_date: Optional[datetime] = Field(None, description="Last modification date of the PDF")
    num_pages: int = Field(..., description="Number of pages in the PDF")
    pages: List[PDFPageContent] = Field(default_factory=list, description="Content of each page in the PDF")
    processing_timestamp: datetime = Field(default_factory=datetime.now, description="When the PDF was processed")
    
    class Config:
        schema_extra = {
            "example": {
                "pdf_id": "f6g7h8i9-j0k1-l2m3-n4o5",
                "file_path": "/data/pdfs/bug_report_20250516.pdf",
                "storage_location": "file_system",
                "title": "Bug Report",
                "author": "John Doe",
                "creation_date": "2025-05-15T10:00:00",
                "modification_date": "2025-05-15T14:30:00",
                "num_pages": 3,
                "pages": [
                    {
                        "page_number": 0,
                        "text_id": "g7h8i9j0-k1l2-m3n4-o5p6",
                        "image_ids": ["h8i9j0k1-l2m3-n4o5-p6q7"],
                        "has_text": True,
                        "has_images": True
                    }
                ],
                "processing_timestamp": "2025-05-16T01:10:00"
            }
        }


class VideoFrame(BaseModel):
    """Model for a single video frame."""
    frame_number: int = Field(..., description="Frame number (0-indexed)")
    timestamp: float = Field(..., description="Timestamp in seconds")
    image_id: Optional[str] = Field(None, description="Reference to image of this frame")
    
    class Config:
        schema_extra = {
            "example": {
                "frame_number": 150,
                "timestamp": 5.0,
                "image_id": "i9j0k1l2-m3n4-o5p6-q7r8"
            }
        }


class VideoContent(BaseModel):
    """Model for video content and metadata."""
    video_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the video content")
    file_path: Optional[str] = Field(None, description="Path to the stored video file")
    storage_location: Optional[str] = Field(None, description="Storage location identifier (DB, file system, etc.)")
    duration: float = Field(..., description="Duration of the video in seconds")
    width: int = Field(..., description="Width of the video in pixels")
    height: int = Field(..., description="Height of the video in pixels")
    format: str = Field(..., description="Format of the video (e.g., MP4, MOV)")
    codec: Optional[str] = Field(None, description="Video codec used")
    fps: float = Field(..., description="Frames per second")
    extracted_frames: List[VideoFrame] = Field(default_factory=list, description="Extracted key frames")
    audio_text_id: Optional[str] = Field(None, description="Reference to text transcribed from audio")
    processing_timestamp: datetime = Field(default_factory=datetime.now, description="When the video was processed")
    
    class Config:
        schema_extra = {
            "example": {
                "video_id": "j0k1l2m3-n4o5-p6q7-r8s9",
                "file_path": "/data/videos/bug_demo_20250516.mp4",
                "storage_location": "file_system",
                "duration": 45.5,
                "width": 1280,
                "height": 720,
                "format": "MP4",
                "codec": "H.264",
                "fps": 30.0,
                "extracted_frames": [
                    {
                        "frame_number": 0,
                        "timestamp": 0.0,
                        "image_id": "k1l2m3n4-o5p6-q7r8-s9t0"
                    },
                    {
                        "frame_number": 150,
                        "timestamp": 5.0,
                        "image_id": "l2m3n4o5-p6q7-r8s9-t0u1"
                    }
                ],
                "audio_text_id": "m3n4o5p6-q7r8-s9t0-u1v2",
                "processing_timestamp": "2025-05-16T01:15:00"
            }
        }


class AttachmentContent(BaseModel):
    """Generic model for attachment content, with references to specific content models."""
    text_content_ids: List[str] = Field(default_factory=list, description="References to text content")
    image_content_ids: List[str] = Field(default_factory=list, description="References to image content")
    pdf_content_id: Optional[str] = Field(None, description="Reference to PDF content")
    video_content_id: Optional[str] = Field(None, description="Reference to video content")
    
    class Config:
        schema_extra = {
            "example": {
                "text_content_ids": ["a1b2c3d4-e5f6-g7h8-i9j0"],
                "image_content_ids": ["b2c3d4e5-f6g7-h8i9-j0k1"],
                "pdf_content_id": "f6g7h8i9-j0k1-l2m3-n4o5",
                "video_content_id": None
            }
        }


class BugAttachment(BaseModel):
    """Model for a bug attachment with its processing information and content references."""
    attachment_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the attachment")
    bug_id: str = Field(..., description="ID of the bug this attachment belongs to")
    filename: str = Field(..., description="Original filename of the attachment")
    file_extension: str = Field(..., description="File extension of the attachment")
    file_type: AttachmentType = Field(..., description="Type of the attachment")
    file_size: int = Field(..., description="Size of the attachment in bytes")
    file_path: Optional[str] = Field(None, description="Path to the original file")
    upload_timestamp: datetime = Field(default_factory=datetime.now, description="When the attachment was uploaded")
    uploader: Optional[str] = Field(None, description="Who uploaded the attachment")
    description: Optional[str] = Field(None, description="Description of the attachment")
    processing_status: AttachmentProcessingStatus = Field(default=AttachmentProcessingStatus.PENDING, description="Status of processing")
    processing_error: Optional[str] = Field(None, description="Error message if processing failed")
    last_processed_timestamp: Optional[datetime] = Field(None, description="When the attachment was last processed")
    content: AttachmentContent = Field(default_factory=AttachmentContent, description="References to processed content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata about the attachment")
    
    @validator('file_extension')
    def validate_file_extension(cls, v):
        """Validate that the file extension is one of the supported types."""
        if v.lower().lstrip('.') not in [e.value for e in AttachmentType]:
            raise ValueError(f"Unsupported file extension: {v}")
        return v.lower().lstrip('.')
    
    @validator('file_type', pre=True)
    def set_file_type_from_extension(cls, v, values):
        """Set the file type based on the file extension if not provided."""
        if v is None and 'file_extension' in values:
            ext = values['file_extension'].lower().lstrip('.')
            try:
                return AttachmentType(ext)
            except ValueError:
                raise ValueError(f"Unsupported file type extension: {ext}")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "attachment_id": "n4o5p6q7-r8s9-t0u1-v2w3",
                "bug_id": "BUG-1234",
                "filename": "screenshot.jpg",
                "file_extension": "jpg",
                "file_type": "jpg",
                "file_size": 125000,
                "file_path": "/uploads/bugs/BUG-1234/screenshot.jpg",
                "upload_timestamp": "2025-05-16T00:30:00",
                "uploader": "john.doe@example.com",
                "description": "Screenshot showing the error message",
                "processing_status": "completed",
                "last_processed_timestamp": "2025-05-16T00:35:00",
                "content": {
                    "text_content_ids": ["o5p6q7r8-s9t0-u1v2-w3x4"],
                    "image_content_ids": ["p6q7r8s9-t0u1-v2w3-x4y5"],
                    "pdf_content_id": None,
                    "video_content_id": None
                },
                "metadata": {
                    "ocr_enabled": True,
                    "screenshot_of": "Error Dialog",
                    "os": "Windows 11"
                }
            }
        }


class AttachmentDatabase(BaseModel):
    """Model representing the attachment database structure."""
    attachments: Dict[str, BugAttachment] = Field(default_factory=dict, description="Mapping of attachment_id to BugAttachment")
    text_contents: Dict[str, TextContent] = Field(default_factory=dict, description="Mapping of text_id to TextContent")
    image_contents: Dict[str, ImageContent] = Field(default_factory=dict, description="Mapping of image_id to ImageContent")
    pdf_contents: Dict[str, PDFContent] = Field(default_factory=dict, description="Mapping of pdf_id to PDFContent")
    video_contents: Dict[str, VideoContent] = Field(default_factory=dict, description="Mapping of video_id to VideoContent")
    
    class Config:
        schema_extra = {
            "example": {
                "attachments": {
                    "n4o5p6q7-r8s9-t0u1-v2w3": {
                        "attachment_id": "n4o5p6q7-r8s9-t0u1-v2w3",
                        "bug_id": "BUG-1234",
                        "filename": "screenshot.jpg",
                        "file_extension": "jpg",
                        "file_type": "jpg",
                        "file_size": 125000
                    }
                },
                "text_contents": {
                    "o5p6q7r8-s9t0-u1v2-w3x4": {
                        "text_id": "o5p6q7r8-s9t0-u1v2-w3x4",
                        "content": "Error Message: Connection refused"
                    }
                },
                "image_contents": {
                    "p6q7r8s9-t0u1-v2w3-x4y5": {
                        "image_id": "p6q7r8s9-t0u1-v2w3-x4y5",
                        "metadata": {
                            "width": 1920,
                            "height": 1080,
                            "format": "JPEG"
                        }
                    }
                }
            }
        }
