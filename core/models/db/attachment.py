"""
Attachment model for the SQLAlchemy ORM.

This module defines the Attachment entity, which represents files attached to bugs
in the Bug Attachment Processing system, along with their processing status and content references.
"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from config.database import Base
from core.models.db.base import attachment_text_association, attachment_image_association
import datetime
from uuid import uuid4


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
    meta_data = Column(JSONB, default={})
    
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
            meta_data=metadata_dict,
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
            metadata=self.meta_data
        )
