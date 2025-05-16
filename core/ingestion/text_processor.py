"""
Text Attachment Processor

This module handles processing of text file attachments (.txt) by:
1. Reading and validating text content
2. Detecting encoding and language
3. Creating structured representations for storage in the database
"""

import os
import sys
import logging
import uuid
import chardet
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

# Add the project root to the path to allow importing from modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, project_root)

# Import the attachment schema
from core.models.attachment_schema import TextContent


def detect_encoding(text_bytes: bytes) -> str:
    """
    Detect the encoding of text bytes.
    
    Args:
        text_bytes: Bytes to analyze
        
    Returns:
        Detected encoding (defaults to 'utf-8' if detection fails)
    """
    result = chardet.detect(text_bytes)
    encoding = result.get('encoding', 'utf-8')
    return encoding


def detect_language(text: str) -> Optional[str]:
    """
    Detect the language of text.
    
    Args:
        text: Text to analyze
        
    Returns:
        Detected language code or None if detection fails
    
    Note:
        This is a stub implementation. In a real implementation, you would use a
        language detection library like langdetect or langid.
    """
    # Simple language detection based on common words (very basic)
    english_words = ['the', 'and', 'to', 'of', 'a', 'in', 'that', 'is', 'was', 'for']
    spanish_words = ['el', 'la', 'de', 'y', 'en', 'un', 'una', 'que', 'es', 'por']
    french_words = ['le', 'la', 'de', 'et', 'en', 'un', 'une', 'qui', 'est', 'pour']
    
    # Normalize text
    norm_text = text.lower()
    
    # Count word occurrences
    en_count = sum(1 for word in english_words if f" {word} " in f" {norm_text} ")
    es_count = sum(1 for word in spanish_words if f" {word} " in f" {norm_text} ")
    fr_count = sum(1 for word in french_words if f" {word} " in f" {norm_text} ")
    
    # Determine language
    if max(en_count, es_count, fr_count) == 0:
        return None
    
    if en_count >= es_count and en_count >= fr_count:
        return 'en'
    elif es_count >= en_count and es_count >= fr_count:
        return 'es'
    else:
        return 'fr'


def process_text_file(file_path: str, output_dir: Optional[str] = None) -> TextContent:
    """
    Process a text file attachment.
    
    Args:
        file_path: Path to the text file
        output_dir: Optional directory to store the processed file
        
    Returns:
        TextContent object with the extracted text
    """
    logger = logging.getLogger("text_processor")
    logger.info(f"Processing text file: {file_path}")
    
    # Create text content ID
    text_id = str(uuid.uuid4())
    
    # Read file bytes
    with open(file_path, 'rb') as f:
        file_bytes = f.read()
    
    # Detect encoding
    encoding = detect_encoding(file_bytes)
    logger.info(f"Detected encoding: {encoding}")
    
    # Decode text
    try:
        text_content = file_bytes.decode(encoding)
    except UnicodeDecodeError:
        logger.warning(f"Failed to decode with detected encoding {encoding}, falling back to utf-8")
        text_content = file_bytes.decode('utf-8', errors='replace')
    
    # Detect language
    language = detect_language(text_content)
    logger.info(f"Detected language: {language}")
    
    # Copy file to output directory if provided
    if output_dir:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)
        
        # Create output file path
        output_file_path = output_dir_path / f"{text_id}_{Path(file_path).name}"
        
        # Copy file
        shutil.copy2(file_path, output_file_path)
        logger.info(f"Copied text file to: {output_file_path}")
    
    # Create text content object
    text_content_obj = TextContent(
        text_id=text_id,
        content=text_content,
        language=language,
        encoding=encoding,
        extraction_method="direct",
        processing_timestamp=datetime.now()
    )
    
    logger.info(f"Text processing complete, ID: {text_id}")
    return text_content_obj
