"""
TextContent model for the SQLAlchemy ORM.

This module defines the TextContent entity, which represents text extracted
from various sources like files, OCR, or transcriptions.
"""

from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
from config.database import Base
from core.models.db.base import attachment_text_association, pdf_page_text_association
import datetime
from uuid import uuid4


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
    attachments = relationship("Attachment", secondary=attachment_text_association, 
                             back_populates="text_contents")
    pdf_pages = relationship("PDFPage", secondary=pdf_page_text_association, 
                           back_populates="texts")
    
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
