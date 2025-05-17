"""
Database Models for Bug Attachment Processing

This module defines SQLAlchemy models for the bug attachment processing pipeline:
- Bug: Core bug entity
- Attachment: Files attached to bugs
- TextContent: Extracted text from attachments
- ImageContent: Image files and metadata
- PDFContent: PDF files and extracted content
- VideoContent: Video files and extracted frames

These models map to PostgreSQL tables while maintaining compatibility with the
Pydantic models defined in attachment_schema.py.
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON, Table
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB, UUID
from config.database import Base
import datetime
from uuid import uuid4
import json
from typing import Dict, Any, List, Optional

# Association tables for many-to-many relationships
attachment_text_association = Table(
    'attachment_text_association', Base.metadata,
    Column('attachment_id', String, ForeignKey('attachments.attachment_id')),
    Column('text_id', String, ForeignKey('text_contents.text_id'))
)

attachment_image_association = Table(
    'attachment_image_association', Base.metadata,
    Column('attachment_id', String, ForeignKey('attachments.attachment_id')),
    Column('image_id', String, ForeignKey('image_contents.image_id'))
)

pdf_page_text_association = Table(
    'pdf_page_text_association', Base.metadata,
    Column('pdf_page_id', String, ForeignKey('pdf_pages.page_id')),
    Column('text_id', String, ForeignKey('text_contents.text_id'))
)

pdf_page_image_association = Table(
    'pdf_page_image_association', Base.metadata,
    Column('pdf_page_id', String, ForeignKey('pdf_pages.page_id')),
    Column('image_id', String, ForeignKey('image_contents.image_id'))
)


class Bug(Base):
    """SQLAlchemy model for a bug."""
    __tablename__ = "bugs"
    
    bug_id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    title = Column(String, nullable=False)
    description = Column(String)
    reporter = Column(String)
    severity = Column(String)
    status = Column(String, default="NEW")
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    
    # Relationships
    attachments = relationship("Attachment", back_populates="bug", cascade="all, delete-orphan")


class TextContent(Base):
    """SQLAlchemy model for text content extracted from attachments."""
    __tablename__ = "text_contents"
    
    text_id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    content = Column(String, default="")
    language = Column(String)
    encoding = Column(String)
    extraction_method = Column(String, default="direct")
    processing_timestamp = Column(DateTime, default=datetime.datetime.now)
    
    # Relationships - attachments that reference this text content
    attachments = relationship("Attachment", secondary=attachment_text_association, back_populates="text_contents")
    pdf_pages = relationship("PDFPage", secondary=pdf_page_text_association, back_populates="texts")
    
    @classmethod
    def from_pydantic(cls, py_model):
        """Create SQLAlchemy model from Pydantic model."""
        from core.models.attachment_schema import TextContent as PydanticTextContent
        
        if not isinstance(py_model, PydanticTextContent):
            raise TypeError(f"Expected PydanticTextContent, got {type(py_model)}")
            
        return cls(
            text_id=py_model.text_id,
            content=py_model.content,
            language=py_model.language,
            encoding=py_model.encoding,
            extraction_method=py_model.extraction_method,
            processing_timestamp=py_model.processing_timestamp
        )
    
    def to_pydantic(self):
        """Convert to Pydantic model."""
        from core.models.attachment_schema import TextContent as PydanticTextContent
        
        return PydanticTextContent(
            text_id=self.text_id,
            content=self.content,
            language=self.language,
            encoding=self.encoding,
            extraction_method=self.extraction_method,
            processing_timestamp=self.processing_timestamp
        )


class ImageContent(Base):
    """SQLAlchemy model for image content and metadata."""
    __tablename__ = "image_contents"
    
    image_id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    file_path = Column(String)
    storage_location = Column(String)
    metadata = Column(JSONB)  # Stores ImageMetadata as JSON
    ocr_text_id = Column(String, ForeignKey("text_contents.text_id"))
    ocr_confidence = Column(Float)
    processing_timestamp = Column(DateTime, default=datetime.datetime.now)
    
    # Relationships
    ocr_text = relationship("TextContent")
    attachments = relationship("Attachment", secondary=attachment_image_association, back_populates="image_contents")
    pdf_pages = relationship("PDFPage", secondary=pdf_page_image_association, back_populates="images")
    
    @classmethod
    def from_pydantic(cls, py_model):
        """Create SQLAlchemy model from Pydantic model."""
        from core.models.attachment_schema import ImageContent as PydanticImageContent
        
        if not isinstance(py_model, PydanticImageContent):
            raise TypeError(f"Expected PydanticImageContent, got {type(py_model)}")
            
        # Convert metadata to dictionary
        metadata_dict = py_model.metadata.dict() if hasattr(py_model.metadata, "dict") else py_model.metadata
            
        return cls(
            image_id=py_model.image_id,
            file_path=py_model.file_path,
            storage_location=py_model.storage_location,
            metadata=metadata_dict,
            ocr_text_id=py_model.ocr_text_id,
            ocr_confidence=py_model.ocr_confidence,
            processing_timestamp=py_model.processing_timestamp
        )
    
    def to_pydantic(self):
        """Convert to Pydantic model."""
        from core.models.attachment_schema import ImageContent as PydanticImageContent
        from core.models.attachment_schema import ImageMetadata
        
        # Create ImageMetadata from JSON
        metadata_obj = ImageMetadata(**self.metadata)
        
        return PydanticImageContent(
            image_id=self.image_id,
            file_path=self.file_path,
            storage_location=self.storage_location,
            metadata=metadata_obj,
            ocr_text_id=self.ocr_text_id,
            ocr_confidence=self.ocr_confidence,
            processing_timestamp=self.processing_timestamp
        )


class PDFPage(Base):
    """SQLAlchemy model for a PDF page."""
    __tablename__ = "pdf_pages"
    
    page_id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    pdf_id = Column(String, ForeignKey("pdf_contents.pdf_id"))
    page_number = Column(Integer, nullable=False)
    has_text = Column(Boolean, default=False)
    has_images = Column(Boolean, default=False)
    
    # Relationships
    pdf = relationship("PDFContent", back_populates="pages")
    texts = relationship("TextContent", secondary=pdf_page_text_association, back_populates="pdf_pages")
    images = relationship("ImageContent", secondary=pdf_page_image_association, back_populates="pdf_pages")
    
    @classmethod
    def from_pydantic(cls, py_model, pdf_id):
        """Create SQLAlchemy model from Pydantic model."""
        from core.models.attachment_schema import PDFPageContent as PydanticPDFPage
        
        if not isinstance(py_model, PydanticPDFPage):
            raise TypeError(f"Expected PydanticPDFPage, got {type(py_model)}")
            
        return cls(
            page_id=str(uuid4()),  # Generate new ID for the page
            pdf_id=pdf_id,
            page_number=py_model.page_number,
            has_text=py_model.has_text,
            has_images=py_model.has_images
        )
    
    def to_pydantic(self):
        """Convert to Pydantic model."""
        from core.models.attachment_schema import PDFPageContent as PydanticPDFPage
        
        return PydanticPDFPage(
            page_number=self.page_number,
            text_id=self.texts[0].text_id if self.texts else None,
            image_ids=[img.image_id for img in self.images],
            has_text=self.has_text,
            has_images=self.has_images
        )


class PDFContent(Base):
    """SQLAlchemy model for PDF content and metadata."""
    __tablename__ = "pdf_contents"
    
    pdf_id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    file_path = Column(String)
    storage_location = Column(String)
    title = Column(String)
    author = Column(String)
    creation_date = Column(DateTime)
    modification_date = Column(DateTime)
    num_pages = Column(Integer, nullable=False)
    processing_timestamp = Column(DateTime, default=datetime.datetime.now)
    
    # Relationships
    pages = relationship("PDFPage", back_populates="pdf", cascade="all, delete-orphan")
    attachments = relationship("Attachment", back_populates="pdf_content")
    
    @classmethod
    def from_pydantic(cls, py_model):
        """Create SQLAlchemy model from Pydantic model."""
        from core.models.attachment_schema import PDFContent as PydanticPDFContent
        
        if not isinstance(py_model, PydanticPDFContent):
            raise TypeError(f"Expected PydanticPDFContent, got {type(py_model)}")
            
        # Create the PDFContent instance
        pdf_content = cls(
            pdf_id=py_model.pdf_id,
            file_path=py_model.file_path,
            storage_location=py_model.storage_location,
            title=py_model.title,
            author=py_model.author,
            creation_date=py_model.creation_date,
            modification_date=py_model.modification_date,
            num_pages=py_model.num_pages,
            processing_timestamp=py_model.processing_timestamp
        )
        
        # We'll handle the pages relationship separately
        return pdf_content
    
    def to_pydantic(self):
        """Convert to Pydantic model."""
        from core.models.attachment_schema import PDFContent as PydanticPDFContent
        
        # Convert pages to Pydantic models
        pydantic_pages = [page.to_pydantic() for page in self.pages]
        
        return PydanticPDFContent(
            pdf_id=self.pdf_id,
            file_path=self.file_path,
            storage_location=self.storage_location,
            title=self.title,
            author=self.author,
            creation_date=self.creation_date,
            modification_date=self.modification_date,
            num_pages=self.num_pages,
            pages=pydantic_pages,
            processing_timestamp=self.processing_timestamp
        )


class VideoFrame(Base):
    """SQLAlchemy model for a video frame."""
    __tablename__ = "video_frames"
    
    frame_id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    video_id = Column(String, ForeignKey("video_contents.video_id"))
    frame_number = Column(Integer, nullable=False)
    timestamp = Column(Float, nullable=False)
    image_id = Column(String, ForeignKey("image_contents.image_id"))
    
    # Relationships
    video = relationship("VideoContent", back_populates="frames")
    image = relationship("ImageContent")
    
    @classmethod
    def from_pydantic(cls, py_model, video_id):
        """Create SQLAlchemy model from Pydantic model."""
        from core.models.attachment_schema import VideoFrame as PydanticVideoFrame
        
        if not isinstance(py_model, PydanticVideoFrame):
            raise TypeError(f"Expected PydanticVideoFrame, got {type(py_model)}")
            
        return cls(
            frame_id=str(uuid4()),  # Generate new ID for the frame
            video_id=video_id,
            frame_number=py_model.frame_number,
            timestamp=py_model.timestamp,
            image_id=py_model.image_id
        )
    
    def to_pydantic(self):
        """Convert to Pydantic model."""
        from core.models.attachment_schema import VideoFrame as PydanticVideoFrame
        
        return PydanticVideoFrame(
            frame_number=self.frame_number,
            timestamp=self.timestamp,
            image_id=self.image_id
        )


class VideoContent(Base):
    """SQLAlchemy model for video content and metadata."""
    __tablename__ = "video_contents"
    
    video_id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    file_path = Column(String)
    storage_location = Column(String)
    duration = Column(Float, nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    format = Column(String, nullable=False)
    codec = Column(String)
    fps = Column(Float, nullable=False)
    audio_text_id = Column(String, ForeignKey("text_contents.text_id"))
    processing_timestamp = Column(DateTime, default=datetime.datetime.now)
    
    # Relationships
    audio_text = relationship("TextContent")
    frames = relationship("VideoFrame", back_populates="video", cascade="all, delete-orphan")
    attachments = relationship("Attachment", back_populates="video_content")
    
    @classmethod
    def from_pydantic(cls, py_model):
        """Create SQLAlchemy model from Pydantic model."""
        from core.models.attachment_schema import VideoContent as PydanticVideoContent
        
        if not isinstance(py_model, PydanticVideoContent):
            raise TypeError(f"Expected PydanticVideoContent, got {type(py_model)}")
            
        # Create the VideoContent instance
        video_content = cls(
            video_id=py_model.video_id,
            file_path=py_model.file_path,
            storage_location=py_model.storage_location,
            duration=py_model.duration,
            width=py_model.width,
            height=py_model.height,
            format=py_model.format,
            codec=py_model.codec,
            fps=py_model.fps,
            audio_text_id=py_model.audio_text_id,
            processing_timestamp=py_model.processing_timestamp
        )
        
        # We'll handle the frames relationship separately
        return video_content
    
    def to_pydantic(self):
        """Convert to Pydantic model."""
        from core.models.attachment_schema import VideoContent as PydanticVideoContent
        
        # Convert frames to Pydantic models
        pydantic_frames = [frame.to_pydantic() for frame in self.frames]
        
        return PydanticVideoContent(
            video_id=self.video_id,
            file_path=self.file_path,
            storage_location=self.storage_location,
            duration=self.duration,
            width=self.width,
            height=self.height,
            format=self.format,
            codec=self.codec,
            fps=self.fps,
            extracted_frames=pydantic_frames,
            audio_text_id=self.audio_text_id,
            processing_timestamp=self.processing_timestamp
        )


class Attachment(Base):
    """SQLAlchemy model for a bug attachment."""
    __tablename__ = "attachments"
    
    attachment_id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    bug_id = Column(String, ForeignKey("bugs.bug_id"), nullable=False)
    filename = Column(String, nullable=False)
    file_extension = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    file_path = Column(String)
    upload_timestamp = Column(DateTime, default=datetime.datetime.now)
    uploader = Column(String)
    description = Column(String)
    processing_status = Column(String, default="pending")
    processing_error = Column(String)
    last_processed_timestamp = Column(DateTime)
    metadata = Column(JSONB, default={})
    
    # References to content
    pdf_content_id = Column(String, ForeignKey("pdf_contents.pdf_id"))
    video_content_id = Column(String, ForeignKey("video_contents.video_id"))
    
    # Relationships
    bug = relationship("Bug", back_populates="attachments")
    text_contents = relationship("TextContent", secondary=attachment_text_association, back_populates="attachments")
    image_contents = relationship("ImageContent", secondary=attachment_image_association, back_populates="attachments")
    pdf_content = relationship("PDFContent", back_populates="attachments")
    video_content = relationship("VideoContent", back_populates="attachments")
    
    @classmethod
    def from_pydantic(cls, py_model):
        """Create SQLAlchemy model from Pydantic model."""
        from core.models.attachment_schema import BugAttachment as PydanticAttachment
        
        if not isinstance(py_model, PydanticAttachment):
            raise TypeError(f"Expected PydanticAttachment, got {type(py_model)}")
            
        # Convert metadata to dictionary if needed
        metadata_dict = py_model.metadata
        
        return cls(
            attachment_id=py_model.attachment_id,
            bug_id=py_model.bug_id,
            filename=py_model.filename,
            file_extension=py_model.file_extension,
            file_type=str(py_model.file_type),
            file_size=py_model.file_size,
            file_path=py_model.file_path,
            upload_timestamp=py_model.upload_timestamp,
            uploader=py_model.uploader,
            description=py_model.description,
            processing_status=str(py_model.processing_status),
            processing_error=py_model.processing_error,
            last_processed_timestamp=py_model.last_processed_timestamp,
            metadata=metadata_dict,
            pdf_content_id=py_model.content.pdf_content_id,
            video_content_id=py_model.content.video_content_id
        )
    
    def to_pydantic(self):
        """Convert to Pydantic model."""
        from core.models.attachment_schema import BugAttachment, AttachmentContent, AttachmentType, AttachmentProcessingStatus
        
        # Create AttachmentContent
        content = AttachmentContent(
            text_content_ids=[text.text_id for text in self.text_contents],
            image_content_ids=[image.image_id for image in self.image_contents],
            pdf_content_id=self.pdf_content_id,
            video_content_id=self.video_content_id
        )
        
        return BugAttachment(
            attachment_id=self.attachment_id,
            bug_id=self.bug_id,
            filename=self.filename,
            file_extension=self.file_extension,
            file_type=AttachmentType(self.file_type),
            file_size=self.file_size,
            file_path=self.file_path,
            upload_timestamp=self.upload_timestamp,
            uploader=self.uploader,
            description=self.description,
            processing_status=AttachmentProcessingStatus(self.processing_status),
            processing_error=self.processing_error,
            last_processed_timestamp=self.last_processed_timestamp,
            content=content,
            metadata=self.metadata
        )
