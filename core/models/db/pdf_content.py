"""
PDFContent model for the SQLAlchemy ORM.

This module defines the PDFContent entity, which represents PDF files
and their extracted content in the Bug Attachment Processing system.
"""

from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.orm import relationship
from config.database import Base
import datetime
from uuid import uuid4


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
