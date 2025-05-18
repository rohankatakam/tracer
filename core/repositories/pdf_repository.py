"""
PDF Repository Module

This module provides repository classes for working with PDF content and pages in the database.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session, joinedload
from uuid import UUID, uuid4

from core.models.db_models import PDFContent, PDFPage, TextContent, ImageContent
from core.repositories.base_repository import BaseRepository


class PDFPageRepository(BaseRepository[PDFPage]):
    """Repository for managing PDFPage entities."""
    
    def __init__(self, session: Session):
        """Initialize the repository with a database session."""
        super().__init__(session, PDFPage)
    
    def get_pages_by_pdf_id(self, pdf_id: str) -> List[PDFPage]:
        """
        Get all pages for a given PDF content ID.
        
        Args:
            pdf_id: The ID of the PDF content
            
        Returns:
            List of PDFPage objects
        """
        return self.session.query(PDFPage).filter(PDFPage.pdf_id == pdf_id).all()
    
    def get_text_contents_for_page(self, page_id: str) -> List[TextContent]:
        """
        Get all text contents associated with a PDF page.
        
        Args:
            page_id: The ID of the PDF page
            
        Returns:
            List of TextContent objects
        """
        # Get the page
        page = self.session.query(PDFPage).filter(PDFPage.page_id == page_id).first()
        if not page:
            return []
            
        # Return the associated text contents
        return page.texts if hasattr(page, 'texts') else []
    
    def get_image_contents_for_page(self, page_id: str) -> List[ImageContent]:
        """
        Get all image contents associated with a PDF page.
        
        Args:
            page_id: The ID of the PDF page
            
        Returns:
            List of ImageContent objects
        """
        # Get the page
        page = self.session.query(PDFPage).filter(PDFPage.page_id == page_id).first()
        if not page:
            return []
            
        # Return the associated image contents
        return page.images if hasattr(page, 'images') else []
    
    def add_text_to_page(self, page_id: str, text_id: str) -> bool:
        """
        Associate a text content with a PDF page.
        
        Args:
            page_id: The ID of the PDF page
            text_id: The ID of the text content
            
        Returns:
            True if successful, False otherwise
        """
        page = self.session.query(PDFPage).filter(PDFPage.page_id == page_id).first()
        text = self.session.query(TextContent).filter(TextContent.text_id == text_id).first()
        
        if not page or not text:
            return False
            
        if text not in page.texts:
            page.texts.append(text)
            page.has_text = True
            self.session.commit()
        
        return True
    
    def add_image_to_page(self, page_id: str, image_id: str) -> bool:
        """
        Associate an image content with a PDF page.
        
        Args:
            page_id: The ID of the PDF page
            image_id: The ID of the image content
            
        Returns:
            True if successful, False otherwise
        """
        page = self.session.query(PDFPage).filter(PDFPage.page_id == page_id).first()
        image = self.session.query(ImageContent).filter(ImageContent.image_id == image_id).first()
        
        if not page or not image:
            return False
            
        if image not in page.images:
            page.images.append(image)
            page.has_images = True
            self.session.commit()
        
        return True
