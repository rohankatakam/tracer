#!/usr/bin/env python3
"""
Test script for enhanced attachment processors using the provided test files.
"""

import os
import sys
import uuid
import logging
import tempfile
import json
from datetime import datetime
from pathlib import Path

# Add the project root to the path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from core.models.attachment_schema import BugAttachment, AttachmentType, AttachmentProcessingStatus
from core.ingestion.attachment_processor import AttachmentProcessor, process_attachment

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("step6_tests")

def determine_attachment_type(file_path):
    """Determine attachment type based on file extension."""
    ext = Path(file_path).suffix.lower().lstrip('.')
    
    if ext == 'pdf':
        return AttachmentType.PDF
    elif ext in ['jpg', 'jpeg']:
        return AttachmentType.IMAGE_JPG
    elif ext == 'png':
        return AttachmentType.IMAGE_PNG
    elif ext == 'txt':
        return AttachmentType.TEXT
    elif ext == 'mp4':
        return AttachmentType.VIDEO
    else:
        return None

def process_test_files():
    """Process all test files in the test directory."""
    test_dir = "/Users/rohankatakam/Documents/cu/tests/step_6_test"
    output_dir = "/Users/rohankatakam/Documents/cu/tests/step_6_output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Create attachment processor
    processor = AttachmentProcessor(output_dir=output_dir)
    results = []
    
    # Process all files in the test directory
    test_files = [f for f in os.listdir(test_dir) if os.path.isfile(os.path.join(test_dir, f))]
    
    for file_name in test_files:
        file_path = os.path.join(test_dir, file_name)
        attachment_type = determine_attachment_type(file_path)
        
        if attachment_type:
            logger.info(f"Processing {file_name} as {attachment_type.name}")
            
            # Create a Bug ID for this test
            bug_id = f"BUG-STEP6-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            
            try:
                # Create a BugAttachment object
                file_name = Path(file_path).name
                file_extension = Path(file_path).suffix.lstrip('.')
                file_size = Path(file_path).stat().st_size
                
                # Create attachment content object
                attachment_content = AttachmentContent(
                    text_content_ids=[],
                    image_content_ids=[],
                    pdf_content_id=None,
                    video_content_id=None
                )
                
                attachment = BugAttachment(
                    bug_id=bug_id,
                    attachment_id=str(uuid.uuid4()),
                    file_path=file_path,
                    filename=file_name,
                    file_extension=file_extension,
                    file_type=attachment_type,
                    file_size=file_size,
                    upload_timestamp=datetime.now().isoformat(),
                    uploader="test_user@example.com",
                    description=f"Test {attachment_type.name} Attachment",
                    processing_status=AttachmentProcessingStatus.PENDING,
                    content=attachment_content,
                    metadata={}
                )
                
                # Process the attachment using the processor instance
                processed_attachment = processor.process_attachment(attachment)
                
                result = {
                    "file_name": file_name,
                    "file_type": attachment_type.name,
                    "bug_id": bug_id,
                    "attachment_id": processed_attachment.attachment_id,
                    "processing_status": processed_attachment.processing_status.value,
                    "content": {}
                }
                
                if processed_attachment.content:
                    if hasattr(processed_attachment.content, "text_content_ids") and processed_attachment.content.text_content_ids:
                        result["content"]["text_content_ids"] = processed_attachment.content.text_content_ids
                    
                    if hasattr(processed_attachment.content, "image_content_ids") and processed_attachment.content.image_content_ids:
                        result["content"]["image_content_ids"] = processed_attachment.content.image_content_ids
                    
                    if hasattr(processed_attachment.content, "pdf_content_id") and processed_attachment.content.pdf_content_id:
                        result["content"]["pdf_content_id"] = processed_attachment.content.pdf_content_id
                
                if processed_attachment.metadata:
                    result["metadata"] = processed_attachment.metadata
                
                results.append(result)
                
                logger.info(f"Successfully processed {file_name}: {processed_attachment.processing_status.name}")
            
            except Exception as e:
                logger.error(f"Error processing {file_name}: {str(e)}")
                results.append({
                    "file_name": file_name,
                    "file_type": attachment_type.name if attachment_type else "unknown",
                    "error": str(e)
                })
    
    # Write results to a JSON file
    results_path = os.path.join(output_dir, "processing_results.json")
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Processing complete. Results saved to {results_path}")
    logger.info(f"Processed files can be found in {output_dir}")
    
    return results, output_dir

if __name__ == "__main__":
    print("Running Step 6 attachment processor tests...")
    results, output_dir = process_test_files()
    
    # Print a summary of results
    print("\nProcessing Summary:")
    for result in results:
        status = result.get("processing_status", "ERROR")
        file_name = result.get("file_name")
        print(f"- {file_name}: {status}")
    
    print(f"\nDetailed results and processed files are in: {output_dir}")
