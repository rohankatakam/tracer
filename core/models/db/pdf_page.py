"""
PDFPage model for the SQLAlchemy ORM.

This module defines the PDFPage entity, which represents a single page
within a PDF document in the Bug Attachment Processing system.
"""

from sqlalchemy import Column, String, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from config.database import Base
from core.models.db.base import pdf_page_text_association, pdf_page_image_association
from uuid import uuid4


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
