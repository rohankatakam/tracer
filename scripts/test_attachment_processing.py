#!/usr/bin/env python
"""
Test Attachment Processing

This script tests the automatic preprocessing of attachments by:
1. Creating a test bug
2. Uploading test attachments (text, image, PDF)
3. Verifying that processing completes successfully
4. Retrieving and displaying the processed content
"""

import os
import sys
import time
import json
import logging
import requests
import argparse
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default API endpoint
DEFAULT_API_URL = 'http://localhost:8000'
DEFAULT_TEST_FILES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'test_files')

def create_test_bug(api_url):
    """Create a test bug for attachment testing."""
    endpoint = f"{api_url}/bugs"
    
    bug_data = {
        "title": f"Test Bug for Attachment Processing {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "description": "This is a test bug created to verify attachment processing functionality.",
        "schema_type": "base",
        "status": "NEW",
        "reporter": "automated_test",
        "product": "Bug Processing System",
        "component": "Attachment Processor"
    }
    
    try:
        response = requests.post(endpoint, json=bug_data)
        response.raise_for_status()
        bug_id = response.json().get('bug_id')
        logger.info(f"Created test bug with ID: {bug_id}")
        return bug_id
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to create test bug: {str(e)}")
        sys.exit(1)

def ensure_test_files(test_files_dir):
    """Ensure test files exist and create them if they don't."""
    os.makedirs(test_files_dir, exist_ok=True)
    
    # Test text file
    text_file_path = os.path.join(test_files_dir, 'test_text.txt')
    if not os.path.exists(text_file_path):
        with open(text_file_path, 'w') as f:
            f.write("This is a test text file for attachment processing.\n")
            f.write("It contains multiple lines to test text extraction.\n")
            f.write("The attachment processor should extract this text and store it in the database.\n")
            f.write("It should also identify the language as English.\n")
    
    # If no test image, provide instructions
    image_file_path = os.path.join(test_files_dir, 'test_image.png')
    if not os.path.exists(image_file_path):
        logger.warning(f"Test image file not found at {image_file_path}")
        logger.warning("Please add a test image file named 'test_image.png' to the test_files directory")
    
    # If no test PDF, provide instructions
    pdf_file_path = os.path.join(test_files_dir, 'test_pdf.pdf')
    if not os.path.exists(pdf_file_path):
        logger.warning(f"Test PDF file not found at {pdf_file_path}")
        logger.warning("Please add a test PDF file named 'test_pdf.pdf' to the test_files directory")
    
    return {
        "text": text_file_path if os.path.exists(text_file_path) else None,
        "image": image_file_path if os.path.exists(image_file_path) else None,
        "pdf": pdf_file_path if os.path.exists(pdf_file_path) else None
    }

def upload_attachment(api_url, bug_id, file_path, description):
    """Upload an attachment to the test bug."""
    if not file_path or not os.path.exists(file_path):
        logger.warning(f"Skipping file upload, file not found: {file_path}")
        return None
    
    endpoint = f"{api_url}/bugs/{bug_id}/attachments"
    
    try:
        with open(file_path, 'rb') as f:
            filename = os.path.basename(file_path)
            files = {'file': (filename, f)}
            data = {
                'description': description,
                'uploader': 'automated_test',
                'auto_process': 'true'  # Enable automatic processing
            }
            
            logger.info(f"Uploading attachment: {filename}")
            response = requests.post(endpoint, files=files, data=data)
            response.raise_for_status()
            
            attachment_id = response.json().get('id')
            logger.info(f"Uploaded attachment with ID: {attachment_id}")
            return attachment_id
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to upload attachment: {str(e)}")
        return None

def wait_for_processing(api_url, attachment_id, timeout_seconds=60):
    """Wait for attachment processing to complete."""
    endpoint = f"{api_url}/attachments/{attachment_id}"
    start_time = time.time()
    
    while time.time() - start_time < timeout_seconds:
        try:
            response = requests.get(endpoint)
            response.raise_for_status()
            
            attachment = response.json()
            status = attachment.get('processing_status')
            
            if status == 'completed':
                logger.info(f"Attachment {attachment_id} processing completed")
                return True
            elif status == 'failed':
                logger.error(f"Attachment {attachment_id} processing failed")
                return False
            
            logger.info(f"Attachment {attachment_id} processing status: {status}. Waiting...")
            time.sleep(2)  # Wait 2 seconds before checking again
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to check attachment status: {str(e)}")
            time.sleep(2)  # Wait 2 seconds before trying again
    
    logger.error(f"Timed out waiting for attachment {attachment_id} processing")
    return False

def get_processed_content(api_url, attachment_id):
    """Get processed content for an attachment."""
    endpoint = f"{api_url}/attachments/{attachment_id}/processed"
    
    try:
        logger.info(f"Retrieving processed content for attachment: {attachment_id}")
        response = requests.get(endpoint)
        response.raise_for_status()
        
        processed_content = response.json()
        return processed_content
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to retrieve processed content: {str(e)}")
        return None

def main():
    parser = argparse.ArgumentParser(description='Test attachment processing')
    parser.add_argument('--api-url', default=DEFAULT_API_URL, help='API URL')
    parser.add_argument('--test-files-dir', default=DEFAULT_TEST_FILES_DIR, help='Directory containing test files')
    args = parser.parse_args()
    
    logger.info("Starting attachment processing test")
    
    # Ensure test files exist
    test_files = ensure_test_files(args.test_files_dir)
    
    # Create a test bug
    bug_id = create_test_bug(args.api_url)
    
    # Upload attachments
    attachment_results = {}
    
    if test_files["text"]:
        text_id = upload_attachment(args.api_url, bug_id, test_files["text"], "Test text file")
        if text_id:
            attachment_results["text"] = {"id": text_id}
    
    if test_files["image"]:
        image_id = upload_attachment(args.api_url, bug_id, test_files["image"], "Test image file")
        if image_id:
            attachment_results["image"] = {"id": image_id}
    
    if test_files["pdf"]:
        pdf_id = upload_attachment(args.api_url, bug_id, test_files["pdf"], "Test PDF file")
        if pdf_id:
            attachment_results["pdf"] = {"id": pdf_id}
    
    # Wait for processing to complete and get results
    for file_type, data in attachment_results.items():
        attachment_id = data["id"]
        logger.info(f"Waiting for {file_type} attachment processing to complete...")
        
        if wait_for_processing(args.api_url, attachment_id):
            # Get processed content
            processed_content = get_processed_content(args.api_url, attachment_id)
            if processed_content:
                attachment_results[file_type]["processed"] = processed_content
                logger.info(f"{file_type.capitalize()} processing succeeded")
                
                # Display a summary of the processing results
                if file_type == "text" and "text_contents" in processed_content:
                    for text in processed_content["text_contents"]:
                        content_preview = text["content"][:100] + "..." if len(text["content"]) > 100 else text["content"]
                        logger.info(f"Text content preview: {content_preview}")
                        logger.info(f"Language: {text.get('language', 'unknown')}")
                
                if file_type == "image" and "image_contents" in processed_content:
                    for image in processed_content["image_contents"]:
                        logger.info(f"Image metadata: {json.dumps(image.get('metadata', {}), indent=2)}")
                        if "ocr_text_id" in image and image["ocr_text_id"]:
                            logger.info(f"Image has OCR text with confidence: {image.get('ocr_confidence', 'unknown')}")
                
                if file_type == "pdf" and "pdf_content" in processed_content:
                    pdf_content = processed_content["pdf_content"]
                    logger.info(f"PDF metadata: {json.dumps(pdf_content.get('metadata', {}), indent=2)}")
                    logger.info(f"Page count: {pdf_content.get('page_count', 0)}")
                    
                    if "text_contents" in processed_content:
                        logger.info(f"Extracted {len(processed_content['text_contents'])} text contents from PDF")
                        
                    if "image_contents" in processed_content:
                        logger.info(f"Extracted {len(processed_content['image_contents'])} images from PDF")
            else:
                logger.error(f"{file_type.capitalize()} processing results retrieval failed")
        else:
            logger.error(f"{file_type.capitalize()} processing failed or timed out")
    
    # Print final summary
    successful_types = [file_type for file_type, data in attachment_results.items() if "processed" in data]
    logger.info("=" * 60)
    logger.info(f"Test completed. Successfully processed {len(successful_types)}/{len(attachment_results)} attachments.")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
