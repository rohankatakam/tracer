#!/usr/bin/env python3
"""
Attachment Processing Demo Script

This script demonstrates the end-to-end flow of the attachment processing pipeline:
1. Process bug attachments (text, images, PDFs, videos)
2. Extract content from attachments
3. Store processed content in the database
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Optional

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

# Import core components
from core.ingestion.attachment_processor import process_attachment, process_bug_attachments
from core.models.attachment_schema import BugAttachment, AttachmentType
from core.database.attachment_db import get_attachment, get_attachments_by_bug_id
from core.utils.logging_utils import setup_logging
from core.utils.json_utils import save_json


def process_single_file(file_path: str, bug_id: str, description: Optional[str] = None,
                     output_dir: Optional[str] = None) -> BugAttachment:
    """
    Process a single attachment file.
    
    Args:
        file_path: Path to the attachment file
        bug_id: ID of the bug this attachment belongs to
        description: Optional description of the attachment
        output_dir: Optional directory to store processed files
        
    Returns:
        The processed attachment
    """
    logger = setup_logging("process_attachment")
    logger.info(f"Processing attachment: {file_path}")
    
    # Process the attachment
    attachment = process_attachment(
        file_path=file_path,
        bug_id=bug_id,
        description=description,
        output_dir=output_dir
    )
    
    # Print summary
    logger.info(f"Attachment processed successfully:")
    logger.info(f"  ID: {attachment.attachment_id}")
    logger.info(f"  File: {attachment.filename}")
    logger.info(f"  Type: {attachment.file_type}")
    logger.info(f"  Status: {attachment.processing_status}")
    
    if attachment.content.text_content_ids:
        logger.info(f"  Text content IDs: {attachment.content.text_content_ids}")
    if attachment.content.image_content_ids:
        logger.info(f"  Image content IDs: {attachment.content.image_content_ids}")
    if attachment.content.pdf_content_id:
        logger.info(f"  PDF content ID: {attachment.content.pdf_content_id}")
    if attachment.content.video_content_id:
        logger.info(f"  Video content ID: {attachment.content.video_content_id}")
    
    return attachment


def process_multiple_files(bug_id: str, file_paths: List[str], output_dir: Optional[str] = None) -> List[BugAttachment]:
    """
    Process multiple attachment files for a bug.
    
    Args:
        bug_id: ID of the bug these attachments belong to
        file_paths: List of paths to attachment files
        output_dir: Optional directory to store processed files
        
    Returns:
        List of processed attachments
    """
    logger = setup_logging("process_attachments")
    logger.info(f"Processing {len(file_paths)} attachments for bug {bug_id}")
    
    # Process all attachments
    attachments = process_bug_attachments(
        bug_id=bug_id,
        attachments=file_paths,
        output_dir=output_dir
    )
    
    # Print summary
    logger.info(f"Processed {len(attachments)} attachments successfully")
    
    return attachments


def main():
    """Main entry point for attachment processing demonstration."""
    parser = argparse.ArgumentParser(description="Process bug attachments")
    parser.add_argument("--file", "-f", help="Path to a single attachment file")
    parser.add_argument("--files", "-F", nargs="+", help="Paths to multiple attachment files")
    parser.add_argument("--bug-id", "-b", default="BUG-1234", help="Bug ID")
    parser.add_argument("--description", "-d", help="Attachment description")
    parser.add_argument("--output-dir", "-o", help="Output directory for processed files")
    
    args = parser.parse_args()
    
    if not args.file and not args.files:
        print("Error: You must provide either --file or --files")
        parser.print_help()
        return 1
    
    if args.file and args.files:
        print("Error: You cannot provide both --file and --files. Choose one.")
        parser.print_help()
        return 1
    
    # Set up output directory
    output_dir = args.output_dir
    if not output_dir:
        output_dir = os.path.join(project_root, "output", "attachments")
    
    if args.file:
        # Process a single file
        attachment = process_single_file(
            file_path=args.file,
            bug_id=args.bug_id,
            description=args.description,
            output_dir=output_dir
        )
        
        # Save attachment info to JSON
        attachment_info_path = os.path.join(output_dir, f"attachment_{attachment.attachment_id}.json")
        save_json(attachment.dict(), attachment_info_path)
        print(f"Attachment info saved to: {attachment_info_path}")
        
    else:
        # Process multiple files
        attachments = process_multiple_files(
            bug_id=args.bug_id,
            file_paths=args.files,
            output_dir=output_dir
        )
        
        # Save attachments info to JSON
        attachments_info_path = os.path.join(output_dir, f"attachments_{args.bug_id}.json")
        save_json([a.dict() for a in attachments], attachments_info_path)
        print(f"Attachments info saved to: {attachments_info_path}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
