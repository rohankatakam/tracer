"""
Attachment Processor Service

This service handles the automatic processing of uploaded attachments.
It integrates our enhanced attachment processors with the database and API.
"""

import os
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from core.repositories.attachment_repository import (
    AttachmentRepository, 
    TextContentRepository,
    ImageContentRepository, 
    PDFContentRepository
)
from core.ingestion.text_processor import process_text_file
from core.ingestion.image_processor import process_image_file
from core.ingestion.pdf_processor import process_pdf_file
from core.models.attachment_schema import AttachmentType, AttachmentProcessingStatus

# Set up logging
logger = logging.getLogger(__name__)


class AttachmentProcessorService:
    """Service for automatic processing of uploaded attachments."""
    
    def __init__(self, session: Session):
        """Initialize with a database session."""
        self.session = session
        self.attachment_repo = AttachmentRepository(session)
        self.text_repo = TextContentRepository(session)
        self.image_repo = ImageContentRepository(session)
        self.pdf_repo = PDFContentRepository(session)
        
        # Create output directory if it doesn't exist
        self.output_dir = os.path.join(os.getcwd(), 'data', 'processed_attachments')
        os.makedirs(self.output_dir, exist_ok=True)
    
    def process_attachment(self, attachment_id: str) -> Dict[str, Any]:
        """
        Process an attachment based on its type.
        
        Args:
            attachment_id: ID of the attachment to process
            
        Returns:
            Dict containing results of the processing
        """
        # Get the attachment from the database
        attachment = self.attachment_repo.get_attachment_by_id(attachment_id)
        if not attachment:
            logger.error(f"Attachment with ID {attachment_id} not found")
            return {"status": "error", "message": f"Attachment not found"}
        
        logger.info(f"Processing attachment: {attachment.filename} (ID: {attachment.attachment_id}, Type: {attachment.file_type})")
        
        # Update status to processing
        self.attachment_repo.update_processing_status(
            attachment_id=str(attachment.attachment_id),
            status=AttachmentProcessingStatus.PROCESSING
        )
        
        results = {}
        try:
            # Process based on file type
            file_type = attachment.file_type
            file_path = attachment.file_path
            
            # Set up type-specific output directory
            type_dir = os.path.join(self.output_dir, file_type.lower())
            os.makedirs(type_dir, exist_ok=True)
            
            if file_type == str(AttachmentType.TEXT.value) or attachment.file_extension.lower() == 'txt':
                # Process text file
                text_results = self._process_text(file_path, attachment_id)
                results.update(text_results)
                
            elif file_type in [str(AttachmentType.IMAGE_PNG.value), str(AttachmentType.IMAGE_JPG.value), 
                               str(AttachmentType.IMAGE_JPEG.value)] or \
                 attachment.file_extension.lower() in ['png', 'jpg', 'jpeg']:
                # Process image file
                image_results = self._process_image(file_path, attachment_id)
                results.update(image_results)
                
            elif file_type == str(AttachmentType.PDF.value) or attachment.file_extension.lower() == 'pdf':
                # Process PDF file
                pdf_results = self._process_pdf(file_path, attachment_id)
                results.update(pdf_results)
                
            elif file_type == str(AttachmentType.VIDEO.value) or attachment.file_extension.lower() in ['mp4']:
                # Video processing could be implemented in the future
                results = {"status": "skipped", "message": "Video processing not implemented"}
                
            else:
                # Unknown file type
                results = {"status": "skipped", "message": f"No processor available for {file_type}"}
            
            # Update attachment with processing results
            self._update_attachment_after_processing(attachment, results)
            
            logger.info(f"Successfully processed attachment: {attachment.filename}")
            return {
                "status": "success", 
                "attachment_id": str(attachment.attachment_id),
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error processing attachment {attachment.attachment_id}: {str(e)}", exc_info=True)
            
            # Update status to failed
            self.attachment_repo.update_processing_status(
                attachment_id=str(attachment.attachment_id),
                status=AttachmentProcessingStatus.FAILED,
                error_message=str(e)
            )
            
            return {
                "status": "error",
                "attachment_id": str(attachment.attachment_id),
                "message": str(e)
            }
    
    def _process_text(self, file_path: str, attachment_id: str) -> Dict[str, Any]:
        """Process a text file using the enhanced text processor."""
        logger.info(f"Processing text file: {file_path}")
        
        text_output_dir = os.path.join(self.output_dir, 'text')
        os.makedirs(text_output_dir, exist_ok=True)
        
        # Process the text file
        text_content, _ = process_text_file(
            file_path=file_path,
            output_dir=text_output_dir,
            store_in_db=False,  # Don't store directly, we'll handle that here
            attachment_id=attachment_id
        )
        
        # Store text content in the database
        db_text_content = self.text_repo.create_text_content(
            content=text_content.content,
            language=text_content.language,
            encoding=text_content.encoding,
            extraction_method=text_content.extraction_method
        )
        
        # Create metadata dict for the attachment
        metadata = {
            "word_count": text_content.metadata.get("word_count"),
            "line_count": text_content.metadata.get("line_count"),
            "character_count": text_content.metadata.get("character_count"),
            "language": text_content.language,
            "encoding": text_content.encoding
        }
        
        return {
            "text_content_id": str(db_text_content.id),
            "metadata": metadata,
            "processor": "text"
        }
    
    def _process_image(self, file_path: str, attachment_id: str) -> Dict[str, Any]:
        """Process an image file using the enhanced image processor."""
        logger.info(f"Processing image file: {file_path}")
        
        image_output_dir = os.path.join(self.output_dir, 'images')
        os.makedirs(image_output_dir, exist_ok=True)
        
        # Process the image file
        image_content, ocr_text = process_image_file(
            file_path=file_path,
            output_dir=image_output_dir,
            perform_ocr_flag=True,
            store_in_db=False,  # Don't store directly, we'll handle that here
            attachment_id=attachment_id
        )
        
        # Store OCR text in the database if available
        text_content_id = None
        if ocr_text:
            db_text_content = self.text_repo.create_text_content(
                content=ocr_text.content,
                language=ocr_text.language,
                encoding=ocr_text.encoding,
                extraction_method=ocr_text.extraction_method
            )
            text_content_id = str(db_text_content.id)
        
        # Store image content in the database
        metadata = {
            "width": image_content.metadata.width,
            "height": image_content.metadata.height,
            "format": image_content.metadata.format,
            "color_mode": image_content.metadata.color_mode,
            "dpi": image_content.metadata.dpi,
            "bits_per_pixel": image_content.metadata.bits_per_pixel
        }
        
        db_image_content = self.image_repo.create_image_content(
            metadata=metadata,
            file_path=image_content.file_path,
            storage_location="file_system",
            ocr_text_id=text_content_id,
            ocr_confidence=image_content.ocr_confidence
        )
        
        return {
            "image_content_id": str(db_image_content.id),
            "ocr_text_id": text_content_id,
            "ocr_confidence": image_content.ocr_confidence if image_content.ocr_confidence else None,
            "metadata": metadata,
            "processor": "image"
        }
    
    def _process_pdf(self, file_path: str, attachment_id: str) -> Dict[str, Any]:
        """Process a PDF file using the enhanced PDF processor."""
        logger.info(f"Processing PDF file: {file_path}")
        
        pdf_output_dir = os.path.join(self.output_dir, 'pdfs')
        os.makedirs(pdf_output_dir, exist_ok=True)
        
        # Process the PDF file
        pdf_result = process_pdf_file(
            pdf_path=file_path,
            output_dir=pdf_output_dir,
            store_in_db=False,  # Don't store directly, we'll handle that here
            attachment_id=attachment_id
        )
        
        pdf_content = pdf_result.get("pdf_content")
        text_contents = pdf_result.get("text_contents", [])
        image_contents = pdf_result.get("image_contents", [])
        
        # Store PDF content in the database
        metadata = {
            "title": pdf_content.title,
            "author": pdf_content.author,
            "creation_date": pdf_content.creation_date,
            "modification_date": pdf_content.modification_date,
            "num_pages": pdf_content.num_pages
        }
        
        # Create or get the PDFContent
        db_pdf_content = self.pdf_repo.get_by_id(str(pdf_content.pdf_id))
        if not db_pdf_content:
            # Create new PDF content without importing models again
            # Create a new PDFContent instance using the repository's methods
            new_pdf_content_data = {
                "pdf_id": str(pdf_content.pdf_id),
                "file_path": pdf_content.file_path,
                "storage_location": "file_system",
                "title": pdf_content.title,
                "author": pdf_content.author,
                "num_pages": pdf_content.num_pages,
                "processing_timestamp": datetime.now()
            }
            
            # Use the repository to create the PDF content
            db_pdf_content = self.pdf_repo.create_from_dict(new_pdf_content_data)
        
        # Store text and image contents with proper page associations
        text_content_ids = []
        db_text_contents = []
        for text_content in text_contents:
            db_text_content = self.text_repo.create_text_content(
                content=text_content.content,
                language=text_content.language,
                encoding=text_content.encoding,
                extraction_method=text_content.extraction_method
            )
            text_content_ids.append(str(db_text_content.text_id))
            db_text_contents.append(db_text_content)
        
        image_content_ids = []
        db_image_contents = []
        for image_content in image_contents:
            img_metadata = {}
            if hasattr(image_content, 'metadata') and image_content.metadata:
                if hasattr(image_content.metadata, 'width'):
                    img_metadata["width"] = image_content.metadata.width
                if hasattr(image_content.metadata, 'height'):
                    img_metadata["height"] = image_content.metadata.height
                if hasattr(image_content.metadata, 'format'):
                    img_metadata["format"] = image_content.metadata.format
                if hasattr(image_content.metadata, 'color_mode'):
                    img_metadata["color_mode"] = image_content.metadata.color_mode
            
            db_image_content = self.image_repo.create_image_content(
                metadata=img_metadata,
                file_path=image_content.file_path,
                storage_location="file_system",
                ocr_text_id=image_content.ocr_text_id,
                ocr_confidence=image_content.ocr_confidence
            )
            image_content_ids.append(str(db_image_content.image_id))
            db_image_contents.append(db_image_content)
        
        # Create PDF pages directly without importing PDFPage again
        # Add pages to the database using SQL directly to avoid import issues
        for i, page_data in enumerate(pdf_content.pages):
            # Create page data as a dictionary
            page_data_dict = {
                "pdf_id": db_pdf_content.pdf_id,
                "page_number": page_data.page_number,
                "has_text": page_data.has_text,
                "has_images": page_data.has_images
            }
            
            # Use a SQL statement to insert the page
            from sqlalchemy import text
            insert_stmt = text("""
                INSERT INTO pdf_pages (page_id, pdf_id, page_number, has_text, has_images)
                VALUES (:page_id, :pdf_id, :page_number, :has_text, :has_images)
                RETURNING page_id
            """)
            
            import uuid
            page_id = str(uuid.uuid4())
            params = {
                "page_id": page_id,
                "pdf_id": page_data_dict["pdf_id"],
                "page_number": page_data_dict["page_number"],
                "has_text": page_data_dict["has_text"],
                "has_images": page_data_dict["has_images"]
            }
            
            result = self.pdf_repo.session.execute(insert_stmt, params)
            self.pdf_repo.session.flush()
            
            # Associate text with this page if there's a matching text_id
            if page_data.text_id:
                for db_text in db_text_contents:
                    if str(db_text.text_id) == page_data.text_id:
                        # Insert into the association table directly
                        text_assoc_stmt = text("""
                            INSERT INTO pdf_page_text_association (pdf_page_id, text_content_id)
                            VALUES (:pdf_page_id, :text_content_id)
                        """)
                        self.pdf_repo.session.execute(text_assoc_stmt, {
                            "pdf_page_id": page_id,
                            "text_content_id": db_text.text_id
                        })
            
            # Associate images with this page
            if page_data.image_ids:
                for img_id in page_data.image_ids:
                    for db_img in db_image_contents:
                        if str(db_img.image_id) == img_id:
                            # Insert into the association table directly
                            img_assoc_stmt = text("""
                                INSERT INTO pdf_page_image_association (pdf_page_id, image_content_id)
                                VALUES (:pdf_page_id, :image_content_id)
                            """)
                            self.pdf_repo.session.execute(img_assoc_stmt, {
                                "pdf_page_id": page_id,
                                "image_content_id": db_img.image_id
                            })
        
        # Commit all the changes
        self.pdf_repo.session.commit()
        
        return {
            "pdf_content_id": str(db_pdf_content.pdf_id),
            "text_content_ids": text_content_ids,
            "image_content_ids": image_content_ids,
            "num_pages": pdf_content.num_pages,  # Changed to match model field
            "metadata": metadata,
            "processor": "pdf"
        }
    
    def _update_attachment_after_processing(self, attachment, results: Dict[str, Any]) -> None:
        """Update attachment with processing results."""
        # Update attachment metadata
        if attachment.metadata and isinstance(attachment.metadata, dict):
            metadata = dict(attachment.metadata)
        else:
            metadata = {}
        
        # Add new metadata - create a new dictionary rather than using update
        for key, value in results.get("metadata", {}).items():
            metadata[key] = value
        
        # Update the attachment
        update_data = {
            "processing_status": "completed",
            "last_processed_timestamp": datetime.now(),
            "metadata": metadata
        }
        
        # Handle PDF content first (direct foreign key)
        if "pdf_content_id" in results:
            update_data["pdf_content_id"] = results["pdf_content_id"]
            
        # First update the basic attachment data
        updated_attachment = self.attachment_repo.update_by_id(str(attachment.attachment_id), update_data)
        if not updated_attachment:
            return
            
        # Now handle text_content_ids (many-to-many relationship)
        if "text_content_id" in results:
            text_content = self.text_repo.get_text_content_by_id(results["text_content_id"])
            if text_content and text_content not in updated_attachment.text_contents:
                updated_attachment.text_contents.append(text_content)
        
        if "text_content_ids" in results and results["text_content_ids"]:
            for text_id in results["text_content_ids"]:
                text_content = self.text_repo.get_text_content_by_id(text_id)
                if text_content and text_content not in updated_attachment.text_contents:
                    updated_attachment.text_contents.append(text_content)
        
        # Handle image_content_ids (many-to-many relationship)
        if "image_content_id" in results:
            image_content = self.image_repo.get_image_content_by_id(results["image_content_id"])
            if image_content and image_content not in updated_attachment.image_contents:
                updated_attachment.image_contents.append(image_content)
        
        if "image_content_ids" in results and results["image_content_ids"]:
            for image_id in results["image_content_ids"]:
                image_content = self.image_repo.get_image_content_by_id(image_id)
                if image_content and image_content not in updated_attachment.image_contents:
                    updated_attachment.image_contents.append(image_content)
        
        # Commit the changes to the relationship tables
        self.attachment_repo.session.commit()
