"""
ImageContent model for the SQLAlchemy ORM.

This module defines the ImageContent entity, which represents image files
and their metadata in the Bug Attachment Processing system.
"""

from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from config.database import Base
from core.models.db.base import attachment_image_association, pdf_page_image_association
import datetime
from uuid import uuid4


class ImageContent(Base):
    """SQLAlchemy model for image content and metadata."""
    __tablename__ = "image_contents"
    
    image_id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    file_path = Column(String)
    storage_location = Column(String)
    meta_data = Column(JSONB)  # Stores ImageMetadata as JSON
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
            meta_data=metadata_dict,
            ocr_text_id=py_model.ocr_text_id,
            ocr_confidence=py_model.ocr_confidence,
            processing_timestamp=py_model.processing_timestamp
        )
    
    def to_pydantic(self):
        """Convert to Pydantic model."""
        from core.models.attachment_schema import ImageContent as PydanticImageContent
        from core.models.attachment_schema import ImageMetadata
        
        # Create ImageMetadata from JSON
        metadata_obj = ImageMetadata(**self.meta_data)
        
        return PydanticImageContent(
            image_id=self.image_id,
            file_path=self.file_path,
            storage_location=self.storage_location,
            metadata=metadata_obj,
            ocr_text_id=self.ocr_text_id,
            ocr_confidence=self.ocr_confidence,
            processing_timestamp=self.processing_timestamp
        )
