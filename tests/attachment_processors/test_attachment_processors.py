#!/usr/bin/env python3
"""
Test script for enhanced attachment processors with source tracking.

This script tests the attachment processors to verify:
1. Enhanced metadata extraction
2. Source tracking information
3. Proper database integration
"""

import os
import sys
import uuid
import logging
import tempfile
from pathlib import Path
from datetime import datetime

# Add the project root to the path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from core.models.attachment_schema import BugAttachment, AttachmentType, AttachmentProcessingStatus
from core.ingestion.attachment_processor import AttachmentProcessor

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("attachment_test")

def create_test_files():
    """Create test files for each attachment type."""
    test_dir = "/tmp/test_attachments"
    os.makedirs(test_dir, exist_ok=True)
    
    # Create a text file
    text_path = os.path.join(test_dir, "test.txt")
    with open(text_path, "w") as f:
        f.write("This is a test text file.\n")
        f.write("It contains some sample text for testing the enhanced text processor.\n")
        f.write("The processor should extract metadata like word count, line count, etc.\n")
        f.write("It should also track that this text came from attachment ID: TEST-ATTACHMENT-001\n")
        f.write("Website: https://example.com and email: test@example.com should be detected.")
    
    # Create a simple image file or use a test image if available
    image_path = None
    test_images = ["/tmp/test_attachments/test.png", "/tmp/test_attachments/test.jpg"]
    for img in test_images:
        if os.path.exists(img):
            image_path = img
            break
    
    if not image_path:
        logger.warning("No test image found. Please create a test image at /tmp/test_attachments/test.png or test.jpg")
    
    # Check for a test PDF or use a sample if available
    pdf_path = None
    test_pdfs = ["/tmp/test_attachments/test.pdf", "/tmp/test_attachments/sample.pdf"]
    for pdf in test_pdfs:
        if os.path.exists(pdf):
            pdf_path = pdf
            break
    
    if not pdf_path:
        logger.warning("No test PDF found. Please create a test PDF at /tmp/test_attachments/test.pdf")
    
    return {
        "text": text_path,
        "image": image_path,
        "pdf": pdf_path
    }

def create_test_attachment(file_path, attachment_type):
    """Create a test BugAttachment object."""
    file_path_obj = Path(file_path) if file_path else None
    
    if not file_path_obj or not file_path_obj.exists():
        return None
    
    attachment = BugAttachment(
        attachment_id=f"TEST-{attachment_type}-{uuid.uuid4()}",
        bug_id="TEST-BUG-001",
        filename=file_path_obj.name,
        file_extension=file_path_obj.suffix.lstrip(".").lower(),
        file_type=attachment_type,
        file_size=file_path_obj.stat().st_size if file_path_obj.exists() else 0,
        file_path=str(file_path_obj),
        upload_timestamp=datetime.now(),
        processing_status=AttachmentProcessingStatus.PENDING
    )
    
    return attachment

def test_processors():
    """Test the enhanced attachment processors."""
    # Create test directory for output
    output_dir = "/tmp/test_attachments/output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Create test files
    test_files = create_test_files()
    
    # Create attachment processor
    processor = AttachmentProcessor(output_dir=output_dir)
    
    # Test text processor
    if test_files["text"]:
        logger.info(f"Testing text processor with file: {test_files['text']}")
        text_attachment = create_test_attachment(test_files["text"], AttachmentType.TEXT)
        processor.process_attachment(text_attachment)
        
        # Verify source tracking
        if text_attachment.processing_status == AttachmentProcessingStatus.COMPLETED:
            logger.info("✅ Text processor test passed")
            logger.info(f"  - Metadata: {text_attachment.metadata}")
            logger.info(f"  - Content IDs: {text_attachment.content.text_content_ids}")
        else:
            logger.error(f"❌ Text processor test failed: {text_attachment.processing_error}")
    
    # Test image processor if we have a test image
    if test_files["image"]:
        logger.info(f"Testing image processor with file: {test_files['image']}")
        image_attachment = create_test_attachment(test_files["image"], AttachmentType.IMAGE_PNG)
        processor.process_attachment(image_attachment)
        
        # Verify source tracking
        if image_attachment.processing_status == AttachmentProcessingStatus.COMPLETED:
            logger.info("✅ Image processor test passed")
            logger.info(f"  - Metadata: {image_attachment.metadata}")
            logger.info(f"  - Image content IDs: {image_attachment.content.image_content_ids}")
            logger.info(f"  - OCR text IDs: {image_attachment.content.text_content_ids}")
        else:
            logger.error(f"❌ Image processor test failed: {image_attachment.processing_error}")
    
    # Test PDF processor if we have a test PDF
    if test_files["pdf"]:
        logger.info(f"Testing PDF processor with file: {test_files['pdf']}")
        pdf_attachment = create_test_attachment(test_files["pdf"], AttachmentType.PDF)
        processor.process_attachment(pdf_attachment)
        
        # Verify source tracking
        if pdf_attachment.processing_status == AttachmentProcessingStatus.COMPLETED:
            logger.info("✅ PDF processor test passed")
            logger.info(f"  - Metadata: {pdf_attachment.metadata}")
            logger.info(f"  - PDF content ID: {pdf_attachment.content.pdf_content_id}")
            logger.info(f"  - Extracted text IDs: {pdf_attachment.content.text_content_ids}")
            logger.info(f"  - Extracted image IDs: {pdf_attachment.content.image_content_ids}")
        else:
            logger.error(f"❌ PDF processor test failed: {pdf_attachment.processing_error}")

if __name__ == "__main__":
    print("Testing enhanced attachment processors with source tracking...")
    test_processors()
    print("Test complete.")
