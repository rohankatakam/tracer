#!/usr/bin/env python3
"""
Database Integration Test Script

This script tests the SQLAlchemy database implementation by creating test data
and performing basic CRUD operations. It helps verify that the repositories,
models, and services are functioning correctly before moving to API implementation.
"""

import sys
import os
import logging
from pathlib import Path
from uuid import uuid4
from datetime import datetime
import json
from sqlalchemy import text

# Add the project root directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("db_integration_test")

# Import necessary modules
from core.database.engine import db_session
from core.repositories import (
    BugRepository,
    AttachmentRepository,
    TextContentRepository,
    ImageContentRepository
)

from core.models.attachment_schema import (
    BugAttachment,
    AttachmentType,
    AttachmentContent,
    TextContent,
    ImageContent,
    ImageMetadata
)

# Import the service layer that replaced attachment_db.py
from core.services import (
    store_attachment,
    get_attachment,
    get_attachments_by_bug_id,
    store_text_content,
    get_text_content,
    store_image_content,
    get_image_content
)


def test_bug_repository():
    """Test the BugRepository with basic CRUD operations."""
    logger.info("Testing BugRepository...")
    
    with db_session() as session:
        # Create repository
        repo = BugRepository(session)
        
        # Generate a unique title for this test run
        test_id = str(uuid4())[:8]
        bug_title = f"Test Bug {test_id}"
        
        # Create a bug
        bug = repo.create_bug(
            title=bug_title,
            description="This is a test bug created by the integration test script",
            reporter="integration_test@example.com",
            severity="Medium"
        )
        
        bug_id = bug.bug_id  # Save the ID to return instead of the entity
        logger.info(f"Created bug with ID: {bug_id}")
        
        # Retrieve the bug
        retrieved_bug = repo.get_bug_by_id(bug_id)
        assert retrieved_bug is not None, "Failed to retrieve the created bug"
        assert retrieved_bug.title == bug_title, "Retrieved bug has incorrect title"
        
        # Update the bug
        updated_bug = repo.update_bug_status(bug_id, "IN_PROGRESS")
        assert updated_bug is not None, "Failed to update the bug"
        assert updated_bug.status == "IN_PROGRESS", "Bug status was not updated correctly"
        
        logger.info("BugRepository tests passed!")
        return bug_id


def test_text_content_repository():
    """Test the TextContentRepository with basic CRUD operations."""
    logger.info("Testing TextContentRepository...")
    
    with db_session() as session:
        # Create repository
        repo = TextContentRepository(session)
        
        # Create text content
        text_content = repo.create_text_content(
            content="This is test text content created by the integration test script",
            language="en",
            encoding="UTF-8",
            extraction_method="direct"
        )
        
        text_id = text_content.text_id  # Save the ID to return instead of the entity
        logger.info(f"Created text content with ID: {text_id}")
        
        # Retrieve the text content
        retrieved_content = repo.get_text_content_by_id(text_id)
        assert retrieved_content is not None, "Failed to retrieve the created text content"
        assert "test text content" in retrieved_content.content, "Retrieved text has incorrect content"
        
        logger.info("TextContentRepository tests passed!")
        return text_id


def test_image_content_repository():
    """Test the ImageContentRepository with basic CRUD operations."""
    logger.info("Testing ImageContentRepository...")
    
    with db_session() as session:
        # Create repository
        repo = ImageContentRepository(session)
        
        # Create image metadata
        image_metadata = {
            "width": 1920,
            "height": 1080,
            "format": "JPEG",
            "color_mode": "RGB",
            "dpi": 72,
            "bits_per_pixel": 24
        }
        
        # Create image content
        image_content = repo.create_image_content(
            metadata=image_metadata,
            file_path="/test/path/image.jpg",
            storage_location="file_system"
        )
        
        image_id = image_content.image_id  # Save the ID to return instead of the entity
        logger.info(f"Created image content with ID: {image_id}")
        
        # Retrieve the image content
        retrieved_content = repo.get_image_content_by_id(image_id)
        assert retrieved_content is not None, "Failed to retrieve the created image content"
        assert retrieved_content.file_path == "/test/path/image.jpg", "Retrieved image has incorrect path"
        assert retrieved_content.meta_data["width"] == 1920, "Retrieved image has incorrect metadata"
        
        logger.info("ImageContentRepository tests passed!")
        return image_id


def test_attachment_repository(bug_id, text_id, image_id):
    """Test the AttachmentRepository with basic CRUD operations."""
    logger.info("Testing AttachmentRepository...")
    
    with db_session() as session:
        # Create repository
        repo = AttachmentRepository(session)
        
        # Create attachment
        attachment = repo.create_attachment(
            bug_id=bug_id,
            filename="test_attachment.jpg",
            file_extension="jpg",
            file_type=AttachmentType.IMAGE_JPG,
            file_size=12345,
            file_path="/test/path/test_attachment.jpg",
            description="Test attachment for integration testing",
            uploader="integration_test@example.com"
        )
        
        attachment_id = attachment.attachment_id  # Save the ID to return instead of the entity
        logger.info(f"Created attachment with ID: {attachment_id}")
        
        # Add content references
        repo.update_by_id(attachment_id, {
            "processing_status": "completed",
            "last_processed_timestamp": datetime.now()
        })
        
        # Link text and image content to the attachment
        session.execute(
            text("""INSERT INTO attachment_text_association (attachment_id, text_id) 
                 VALUES (:attachment_id, :text_id)""")
            .bindparams(attachment_id=attachment_id, text_id=text_id)
        )
        
        session.execute(
            text("""INSERT INTO attachment_image_association (attachment_id, image_id) 
                 VALUES (:attachment_id, :image_id)""")
            .bindparams(attachment_id=attachment_id, image_id=image_id)
        )
        
        session.commit()
        
        # Retrieve the attachment
        retrieved_attachment = repo.get_attachment_by_id(attachment_id)
        assert retrieved_attachment is not None, "Failed to retrieve the created attachment"
        assert retrieved_attachment.filename == "test_attachment.jpg", "Retrieved attachment has incorrect filename"
        
        # Check that the relationships were created
        assert len(retrieved_attachment.text_contents) > 0, "Attachment has no text content associations"
        assert len(retrieved_attachment.image_contents) > 0, "Attachment has no image content associations"
        
        logger.info("AttachmentRepository tests passed!")
        return attachment_id


def test_service_layer(attachment_id, text_id, image_id):
    """Test the service layer that replaced attachment_db.py."""
    logger.info("Testing service layer...")
    
    # Test get_attachment
    attachment = get_attachment(attachment_id)
    assert attachment is not None, "Failed to retrieve attachment via service layer"
    assert attachment.filename == "test_attachment.jpg", "Retrieved attachment has incorrect filename"
    
    # Test get_text_content
    text = get_text_content(text_id)
    assert text is not None, "Failed to retrieve text content via service layer"
    assert "test text content" in text.content, "Retrieved text has incorrect content"
    
    # Test get_image_content
    image = get_image_content(image_id)
    assert image is not None, "Failed to retrieve image content via service layer"
    assert image.metadata.width == 1920, "Retrieved image has incorrect metadata"
    
    # Test get_attachments_by_bug_id
    bug_attachments = get_attachments_by_bug_id(attachment.bug_id)
    assert len(bug_attachments) > 0, "Failed to retrieve attachments by bug ID via service layer"
    
    logger.info("Service layer tests passed!")


def main():
    """Run all integration tests."""
    logger.info("Starting database integration tests...")
    
    try:
        # Test the repositories
        bug_id = test_bug_repository()
        text_id = test_text_content_repository()
        image_id = test_image_content_repository()
        attachment_id = test_attachment_repository(bug_id, text_id, image_id)
        
        # Test the service layer
        test_service_layer(attachment_id, text_id, image_id)
        
        logger.info("All tests passed successfully!")
        logger.info("The database implementation is working correctly.")
        
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
