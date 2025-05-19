"""
Attachment Processing Pipeline

This module provides the main entry point for processing bug attachments of various types:
- Text (.txt)
- Images (.jpg, .jpeg, .png)
- PDFs (.pdf)
- Videos (.mp4)

It follows the workflow depicted in the system architecture diagram, routing
attachments to the appropriate processor based on file type and maintaining
references to all extracted data.
"""

import os
import sys
import logging
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple

# Add the project root to the path to allow importing from modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, project_root)

# Import the attachment schema
from core.models.attachment_schema import (
    BugAttachment, AttachmentType, AttachmentProcessingStatus, 
    TextContent, ImageContent, PDFContent, VideoContent,
    AttachmentContent, AttachmentDatabase
)

# Import the specific processors
from core.ingestion.text_processor import process_text_file
from core.ingestion.image_processor import process_image_file
from core.ingestion.pdf_processor import process_pdf_file
# Stub import for future implementation
# from core.ingestion.video_processor import process_video_file

# Import database connectors
from core.database.attachment_db import (
    store_attachment, store_text_content, store_image_content,
    get_attachment, get_text_content, get_image_content
)


class AttachmentProcessor:
    """
    Main class for processing bug attachments and routing them to appropriate processors.
    
    This class handles the entire attachment processing pipeline:
    1. Validates incoming attachments
    2. Routes to type-specific processors
    3. Stores extracted data in the database
    4. Maintains references between related data
    """
    
    def __init__(self, output_dir: Optional[str] = None, log_level: int = logging.INFO):
        """
        Initialize the attachment processor.
        
        Args:
            output_dir: Directory to store processed files and extracted data
            log_level: Logging level
        """
        # Set up logging
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger("attachment_processor")
        
        # Set up output directory
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path("output/attachments")
        
        # Create subdirectories for different types of content
        self.text_dir = self.output_dir / "text"
        self.image_dir = self.output_dir / "images"
        self.pdf_dir = self.output_dir / "pdfs"
        self.video_dir = self.output_dir / "videos"
        
        # Create all directories
        for directory in [self.output_dir, self.text_dir, self.image_dir, self.pdf_dir, self.video_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Attachment processor initialized with output directory: {self.output_dir}")
    
    def process_attachment(self, attachment: BugAttachment) -> BugAttachment:
        """
        Process a bug attachment based on its file type.
        
        Args:
            attachment: The bug attachment to process
            
        Returns:
            Updated bug attachment with processing status and content references
        """
        self.logger.info(f"Processing attachment: {attachment.filename} (ID: {attachment.attachment_id})")
        
        # Update processing status
        attachment.processing_status = AttachmentProcessingStatus.PROCESSING
        attachment.last_processed_timestamp = datetime.now()
        
        try:
            # Process based on file type
            if attachment.file_type == AttachmentType.TEXT:
                self._process_text_attachment(attachment)
            elif attachment.file_type in [AttachmentType.IMAGE_JPG, AttachmentType.IMAGE_JPEG, AttachmentType.IMAGE_PNG]:
                self._process_image_attachment(attachment)
            elif attachment.file_type == AttachmentType.PDF:
                self._process_pdf_attachment(attachment)
            elif attachment.file_type == AttachmentType.VIDEO:
                self._process_video_attachment(attachment)
            else:
                raise ValueError(f"Unsupported file type: {attachment.file_type}")
            
            # Update processing status
            attachment.processing_status = AttachmentProcessingStatus.COMPLETED
            self.logger.info(f"Successfully processed attachment: {attachment.filename}")
            
        except Exception as e:
            # Handle processing error
            self.logger.error(f"Error processing attachment: {str(e)}")
            attachment.processing_status = AttachmentProcessingStatus.FAILED
            attachment.processing_error = str(e)
        
        # Update timestamp
        attachment.last_processed_timestamp = datetime.now()
        
        # Store updated attachment
        store_attachment(attachment)
        
        return attachment
    
    def _process_text_attachment(self, attachment: BugAttachment) -> None:
        """
        Process a text file attachment.
        
        Args:
            attachment: The text file attachment to process
        """
        self.logger.info(f"Processing text attachment: {attachment.filename}")
        
        try:
            # Process the text file with enhanced processor
            text_content = process_text_file(
                file_path=attachment.file_path,
                output_dir=str(self.text_dir),
                store_in_db=True,  # Directly store in DB during processing
                attachment_id=attachment.attachment_id  # Pass attachment ID for source tracking
            )
            
            # Update attachment with reference
            if not attachment.content:
                attachment.content = AttachmentContent()
            
            attachment.content.text_content_ids = [text_content.text_id]
            
            # Store metadata in attachment
            if not attachment.metadata:
                attachment.metadata = {}
                
            # Add key metadata to the attachment level
            if hasattr(text_content, 'metadata'):
                attachment.metadata.update({
                    'word_count': text_content.metadata.get('word_count'),
                    'line_count': text_content.metadata.get('line_count'),
                    'character_count': text_content.metadata.get('character_count'),
                    'encoding': text_content.encoding,
                    'language': text_content.language
                })
            
            attachment.processing_status = AttachmentProcessingStatus.COMPLETED
            
            self.logger.info(f"Text attachment processing complete for {attachment.filename}")
            
        except Exception as e:
            self.logger.error(f"Error processing text attachment: {str(e)}")
            attachment.processing_status = AttachmentProcessingStatus.FAILED
            attachment.processing_error = str(e)
    
    def _process_image_attachment(self, attachment: BugAttachment) -> None:
        """
        Process an image file attachment.
        
        Args:
            attachment: The image file attachment to process
        """
        self.logger.info(f"Processing image attachment: {attachment.filename}")
        
        try:
            # Process the image file with enhanced processor
            image_content, ocr_text = process_image_file(
                file_path=attachment.file_path,
                output_dir=str(self.image_dir),
                perform_ocr_flag=True,
                store_in_db=True,  # Directly store in DB during processing
                attachment_id=attachment.attachment_id  # Pass attachment ID for source tracking
            )
            
            # Update attachment with references
            if not attachment.content:
                attachment.content = AttachmentContent()
            
            attachment.content.image_content_ids = [image_content.image_id]
            
            if ocr_text:
                if not attachment.content.text_content_ids:
                    attachment.content.text_content_ids = []
                attachment.content.text_content_ids.append(ocr_text.text_id)
            
            # Store metadata in attachment
            if not attachment.metadata:
                attachment.metadata = {}
            
            # Add key metadata to the attachment level
            if hasattr(image_content, 'metadata'):
                meta = image_content.metadata
                attachment.metadata.update({
                    'width': meta.width,
                    'height': meta.height,
                    'format': meta.format,
                    'color_mode': meta.color_mode,
                    'has_ocr_text': ocr_text is not None,
                    'ocr_confidence': image_content.ocr_confidence
                })
                
            attachment.processing_status = AttachmentProcessingStatus.COMPLETED
            
            self.logger.info(f"Image attachment processing complete for {attachment.filename}")
            
        except Exception as e:
            self.logger.error(f"Error processing image attachment: {str(e)}")
            attachment.processing_status = AttachmentProcessingStatus.FAILED
            attachment.processing_error = str(e)
    
    def _process_pdf_attachment(self, attachment: BugAttachment) -> None:
        """
        Process a PDF file attachment.
        
        Args:
            attachment: The PDF file attachment to process
        """
        self.logger.info(f"Processing PDF attachment: {attachment.filename}")
        
        try:
            # Process the PDF file with the enhanced processor
            pdf_result = process_pdf_file(
                pdf_path=attachment.file_path,
                output_dir=str(self.pdf_dir),
                store_in_db=True,  # Directly store in DB during processing
                attachment_id=attachment.attachment_id  # Pass attachment ID for source tracking
            )
            
            # Update attachment with references
            if not attachment.content:
                attachment.content = AttachmentContent()
            
            # Store PDF content ID
            pdf_content = pdf_result.get('pdf_content')
            attachment.content.pdf_content_id = pdf_content.pdf_id
            
            # Store text and image content IDs
            attachment.content.text_content_ids = pdf_result.get('text_ids', [])
            attachment.content.image_content_ids = pdf_result.get('image_ids', [])
            
            # Store metadata in attachment
            if not attachment.metadata:
                attachment.metadata = {}
            
            # Add key metadata to the attachment level
            attachment.metadata.update({
                'page_count': pdf_content.num_pages,
                'author': pdf_content.author,
                'title': pdf_content.title,
                'creation_date': pdf_content.creation_date,
                'modification_date': pdf_content.modification_date,
                'text_count': len(pdf_result.get('text_ids', [])),
                'image_count': len(pdf_result.get('image_ids', []))
            })
            
            attachment.processing_status = AttachmentProcessingStatus.COMPLETED
            
            self.logger.info(f"PDF attachment processing complete for {attachment.filename}")
            
        except Exception as e:
            self.logger.error(f"Error processing PDF attachment: {str(e)}")
            attachment.processing_status = AttachmentProcessingStatus.FAILED
            attachment.processing_error = str(e)
    
    def _process_video_attachment(self, attachment: BugAttachment) -> None:
        """
        Process a video file attachment.
        
        Args:
            attachment: The video file attachment to process
        """
        self.logger.info(f"Video processing is not fully implemented yet, skipping: {attachment.filename}")
        
        # This is a stub for future implementation
        # The actual implementation would:
        # 1. Extract frames from video at regular intervals
        # 2. Process frames as images
        # 3. Extract audio and transcribe if possible
        # 4. Store all extracted content
        # 5. Update attachment with references
        
        # For now, mark as skipped
        attachment.processing_status = AttachmentProcessingStatus.SKIPPED
        attachment.processing_error = "Video processing not implemented yet"


def process_attachment(file_path: str, bug_id: str, description: Optional[str] = None, 
                      output_dir: Optional[str] = None) -> BugAttachment:
    """
    Process a single attachment file for a bug report.
    
    Args:
        file_path: Path to the attachment file
        bug_id: ID of the bug this attachment belongs to
        description: Optional description of the attachment
        output_dir: Optional directory to store processed files
        
    Returns:
        The processed attachment with references to extracted content
    """
    logger = logging.getLogger("attachment_processor")
    
    # Check if file exists
    if not os.path.exists(file_path):
        logger.error(f"Attachment file not found: {file_path}")
        raise FileNotFoundError(f"Attachment file not found: {file_path}")
    
    # Create attachment object
    file_path_obj = Path(file_path)
    attachment = BugAttachment(
        attachment_id=str(uuid.uuid4()),
        bug_id=bug_id,
        filename=file_path_obj.name,
        file_extension=file_path_obj.suffix.lstrip('.').lower(),
        file_size=file_path_obj.stat().st_size,
        file_path=str(file_path_obj),
        description=description
    )
    
    # Store initial attachment
    store_attachment(attachment)
    
    # Process the attachment
    processor = AttachmentProcessor(output_dir=output_dir)
    processed_attachment = processor.process_attachment(attachment)
    
    return processed_attachment


def process_bug_attachments(bug_id: str, attachments: List[str], 
                          output_dir: Optional[str] = None) -> List[BugAttachment]:
    """
    Process multiple attachments for a bug report.
    
    Args:
        bug_id: ID of the bug these attachments belong to
        attachments: List of file paths to attachments
        output_dir: Optional directory to store processed files
        
    Returns:
        List of processed attachments with references to extracted content
    """
    logger = logging.getLogger("attachment_processor")
    logger.info(f"Processing {len(attachments)} attachments for bug {bug_id}")
    
    processor = AttachmentProcessor(output_dir=output_dir)
    processed_attachments = []
    
    for file_path in attachments:
        try:
            # Create attachment object
            file_path_obj = Path(file_path)
            attachment = BugAttachment(
                attachment_id=str(uuid.uuid4()),
                bug_id=bug_id,
                filename=file_path_obj.name,
                file_extension=file_path_obj.suffix.lstrip('.').lower(),
                file_size=file_path_obj.stat().st_size,
                file_path=str(file_path_obj)
            )
            
            # Process the attachment
            processed_attachment = processor.process_attachment(attachment)
            processed_attachments.append(processed_attachment)
            
        except Exception as e:
            logger.error(f"Error processing attachment {file_path}: {str(e)}")
    
    return processed_attachments
