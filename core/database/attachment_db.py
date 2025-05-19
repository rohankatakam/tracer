"""
Attachment Database Handler

This module provides functions for storing and retrieving attachments and their content
in a simple file-based storage system. In a production environment, this would likely
be replaced with a proper database solution.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import pickle

# Import the attachment schema
from core.models.attachment_schema import (
    BugAttachment, TextContent, ImageContent, 
    PDFContent, VideoContent, AttachmentDatabase
)

# Set up logging
logger = logging.getLogger("attachment_db")

# Database paths
DB_DIR = Path("data/attachment_db")
ATTACHMENT_DB_PATH = DB_DIR / "attachments.pkl"
TEXT_DB_PATH = DB_DIR / "text_contents.pkl"
IMAGE_DB_PATH = DB_DIR / "image_contents.pkl"
PDF_DB_PATH = DB_DIR / "pdf_contents.pkl"
VIDEO_DB_PATH = DB_DIR / "video_contents.pkl"

# Initialize database
DB_DIR.mkdir(parents=True, exist_ok=True)


def _initialize_db():
    """Initialize the database files if they don't exist."""
    if not ATTACHMENT_DB_PATH.exists():
        with open(ATTACHMENT_DB_PATH, 'wb') as f:
            pickle.dump({}, f)
    
    if not TEXT_DB_PATH.exists():
        with open(TEXT_DB_PATH, 'wb') as f:
            pickle.dump({}, f)
    
    if not IMAGE_DB_PATH.exists():
        with open(IMAGE_DB_PATH, 'wb') as f:
            pickle.dump({}, f)
    
    if not PDF_DB_PATH.exists():
        with open(PDF_DB_PATH, 'wb') as f:
            pickle.dump({}, f)
    
    if not VIDEO_DB_PATH.exists():
        with open(VIDEO_DB_PATH, 'wb') as f:
            pickle.dump({}, f)


def _load_db(db_path: Path) -> Dict:
    """Load a database file."""
    if not db_path.exists():
        return {}
    
    try:
        with open(db_path, 'rb') as f:
            return pickle.load(f)
    except Exception as e:
        logger.error(f"Error loading database {db_path}: {str(e)}")
        return {}


def _save_db(db_path: Path, data: Dict):
    """Save a database file."""
    try:
        with open(db_path, 'wb') as f:
            pickle.dump(data, f)
    except Exception as e:
        logger.error(f"Error saving database {db_path}: {str(e)}")


# Attachment functions
def store_attachment(attachment: BugAttachment) -> bool:
    """
    Store an attachment in the database.
    
    Args:
        attachment: The attachment to store
        
    Returns:
        True if successful, False otherwise
    """
    try:
        _initialize_db()
        attachments = _load_db(ATTACHMENT_DB_PATH)
        attachments[attachment.attachment_id] = attachment
        _save_db(ATTACHMENT_DB_PATH, attachments)
        return True
    except Exception as e:
        logger.error(f"Error storing attachment: {str(e)}")
        return False


def get_attachment(attachment_id: str) -> Optional[BugAttachment]:
    """
    Get an attachment from the database.
    
    Args:
        attachment_id: ID of the attachment to get
        
    Returns:
        The attachment if found, None otherwise
    """
    try:
        attachments = _load_db(ATTACHMENT_DB_PATH)
        return attachments.get(attachment_id)
    except Exception as e:
        logger.error(f"Error getting attachment: {str(e)}")
        return None


def get_attachments_by_bug_id(bug_id: str) -> List[BugAttachment]:
    """
    Get all attachments for a bug.
    
    Args:
        bug_id: ID of the bug
        
    Returns:
        List of attachments for the bug
    """
    try:
        attachments = _load_db(ATTACHMENT_DB_PATH)
        return [a for a in attachments.values() if a.bug_id == bug_id]
    except Exception as e:
        logger.error(f"Error getting attachments by bug ID: {str(e)}")
        return []


# Text content functions
def store_text_content(text_content: TextContent) -> str:
    """
    Store text content in the database.
    
    Args:
        text_content: The text content to store
        
    Returns:
        The text_id if successful, empty string otherwise
    """
    try:
        _initialize_db()
        text_contents = _load_db(TEXT_DB_PATH)
        text_contents[text_content.text_id] = text_content
        _save_db(TEXT_DB_PATH, text_contents)
        return text_content.text_id
    except Exception as e:
        logger.error(f"Error storing text content: {str(e)}")
        return ""


def get_text_content(text_id: str) -> Optional[TextContent]:
    """
    Get text content from the database.
    
    Args:
        text_id: ID of the text content to get
        
    Returns:
        The text content if found, None otherwise
    """
    try:
        text_contents = _load_db(TEXT_DB_PATH)
        return text_contents.get(text_id)
    except Exception as e:
        logger.error(f"Error getting text content: {str(e)}")
        return None


# Image content functions
def store_image_content(image_content: ImageContent) -> str:
    """
    Store image content in the database.
    
    Args:
        image_content: The image content to store
        
    Returns:
        The image_id if successful, empty string otherwise
    """
    try:
        _initialize_db()
        image_contents = _load_db(IMAGE_DB_PATH)
        image_contents[image_content.image_id] = image_content
        _save_db(IMAGE_DB_PATH, image_contents)
        return image_content.image_id
    except Exception as e:
        logger.error(f"Error storing image content: {str(e)}")
        return ""


def get_image_content(image_id: str) -> Optional[ImageContent]:
    """
    Get image content from the database.
    
    Args:
        image_id: ID of the image content to get
        
    Returns:
        The image content if found, None otherwise
    """
    try:
        image_contents = _load_db(IMAGE_DB_PATH)
        return image_contents.get(image_id)
    except Exception as e:
        logger.error(f"Error getting image content: {str(e)}")
        return None


# PDF content functions
def store_pdf_content(pdf_content: PDFContent) -> str:
    """
    Store PDF content in the database.
    
    Args:
        pdf_content: The PDF content to store
        
    Returns:
        The pdf_id if successful, empty string otherwise
    """
    try:
        _initialize_db()
        pdf_contents = _load_db(PDF_DB_PATH)
        pdf_contents[pdf_content.pdf_id] = pdf_content
        _save_db(PDF_DB_PATH, pdf_contents)
        return pdf_content.pdf_id
    except Exception as e:
        logger.error(f"Error storing PDF content: {str(e)}")
        return ""


def get_pdf_content(pdf_id: str) -> Optional[PDFContent]:
    """
    Get PDF content from the database.
    
    Args:
        pdf_id: ID of the PDF content to get
        
    Returns:
        The PDF content if found, None otherwise
    """
    try:
        pdf_contents = _load_db(PDF_DB_PATH)
        return pdf_contents.get(pdf_id)
    except Exception as e:
        logger.error(f"Error getting PDF content: {str(e)}")
        return None


# Video content functions
def store_video_content(video_content: VideoContent) -> str:
    """
    Store video content in the database.
    
    Args:
        video_content: The video content to store
        
    Returns:
        The video_id if successful, empty string otherwise
    """
    try:
        _initialize_db()
        video_contents = _load_db(VIDEO_DB_PATH)
        video_contents[video_content.video_id] = video_content
        _save_db(VIDEO_DB_PATH, video_contents)
        return video_content.video_id
    except Exception as e:
        logger.error(f"Error storing video content: {str(e)}")
        return ""


def get_video_content(video_id: str) -> Optional[VideoContent]:
    """
    Get video content from the database.
    
    Args:
        video_id: ID of the video content to get
        
    Returns:
        The video content if found, None otherwise
    """
    try:
        video_contents = _load_db(VIDEO_DB_PATH)
        return video_contents.get(video_id)
    except Exception as e:
        logger.error(f"Error getting video content: {str(e)}")
        return None


# Attachment database functions
def get_attachment_database() -> AttachmentDatabase:
    """
    Get the complete attachment database.
    
    Returns:
        The attachment database
    """
    try:
        _initialize_db()
        attachments = _load_db(ATTACHMENT_DB_PATH)
        text_contents = _load_db(TEXT_DB_PATH)
        image_contents = _load_db(IMAGE_DB_PATH)
        pdf_contents = _load_db(PDF_DB_PATH)
        video_contents = _load_db(VIDEO_DB_PATH)
        
        return AttachmentDatabase(
            attachments=attachments,
            text_contents=text_contents,
            image_contents=image_contents,
            pdf_contents=pdf_contents,
            video_contents=video_contents
        )
    except Exception as e:
        logger.error(f"Error getting attachment database: {str(e)}")
        return AttachmentDatabase()
