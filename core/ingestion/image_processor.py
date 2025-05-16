"""
Image Attachment Processor

This module handles processing of image file attachments (.jpg, .jpeg, .png) by:
1. Loading and validating the image
2. Extracting image metadata
3. Performing OCR when appropriate
4. Creating structured representations for storage in the database
"""

import os
import sys
import logging
import uuid
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple

import numpy as np
from PIL import Image, ExifTags
import pytesseract
import cv2

# Add the project root to the path to allow importing from modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, project_root)

# Import the attachment schema
from core.models.attachment_schema import ImageContent, TextContent, ImageMetadata


def extract_image_metadata(img: Image.Image) -> ImageMetadata:
    """
    Extract metadata from an image.
    
    Args:
        img: PIL Image object
        
    Returns:
        ImageMetadata object with extracted metadata
    """
    # Get basic metadata
    metadata = ImageMetadata(
        width=img.width,
        height=img.height,
        format=img.format if img.format else "Unknown"
    )
    
    # Get color mode
    metadata.color_mode = img.mode
    
    # Try to get DPI information
    try:
        dpi = img.info.get('dpi')
        if dpi and len(dpi) >= 2:
            metadata.dpi = int(dpi[0])
    except (AttributeError, KeyError, IndexError, TypeError):
        pass
    
    # Try to get bit depth
    try:
        if img.mode == "1":  # Binary (1-bit)
            metadata.bits_per_pixel = 1
        elif img.mode == "L":  # Grayscale (8-bit)
            metadata.bits_per_pixel = 8
        elif img.mode == "P":  # Palette (8-bit)
            metadata.bits_per_pixel = 8
        elif img.mode == "RGB":  # RGB (24-bit)
            metadata.bits_per_pixel = 24
        elif img.mode == "RGBA":  # RGBA (32-bit)
            metadata.bits_per_pixel = 32
        elif img.mode == "CMYK":  # CMYK (32-bit)
            metadata.bits_per_pixel = 32
    except:
        pass
    
    return metadata


def perform_ocr(img: Image.Image) -> Optional[TextContent]:
    """
    Perform OCR on an image.
    
    Args:
        img: PIL Image object
        
    Returns:
        TextContent object with OCR results or None if no text was found
    """
    logger = logging.getLogger("image_processor")
    
    try:
        # Convert to OpenCV format for preprocessing
        img_np = np.array(img)
        
        # Convert to grayscale if not already
        if len(img_np.shape) == 3 and img_np.shape[2] >= 3:
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_np
        
        # Apply preprocessing to improve OCR results
        # 1. Denoise
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        
        # 2. Thresholding
        _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # 3. Dilation to connect components
        kernel = np.ones((1, 1), np.uint8)
        dilated = cv2.dilate(binary, kernel, iterations=1)
        
        # Convert back to PIL for OCR
        processed_img = Image.fromarray(dilated)
        
        # Perform OCR
        ocr_text = pytesseract.image_to_string(processed_img)
        
        # Create text content only if text was found
        if ocr_text.strip():
            return TextContent(
                text_id=str(uuid.uuid4()),
                content=ocr_text,
                extraction_method="ocr",
                processing_timestamp=datetime.now()
            )
        else:
            logger.info("No text found in image during OCR")
            return None
    
    except Exception as e:
        logger.error(f"Error performing OCR: {str(e)}")
        return None


def process_image_file(file_path: str, output_dir: Optional[str] = None,
                      perform_ocr_flag: bool = True) -> Tuple[ImageContent, Optional[TextContent]]:
    """
    Process an image file attachment.
    
    Args:
        file_path: Path to the image file
        output_dir: Optional directory to store the processed file
        perform_ocr_flag: Whether to perform OCR on the image
        
    Returns:
        Tuple of (ImageContent, Optional[TextContent])
    """
    logger = logging.getLogger("image_processor")
    logger.info(f"Processing image file: {file_path}")
    
    # Create image content ID
    image_id = str(uuid.uuid4())
    
    # Load image
    try:
        img = Image.open(file_path)
        logger.info(f"Loaded image: {img.width}x{img.height}, {img.mode}, {img.format}")
    except Exception as e:
        logger.error(f"Failed to load image: {str(e)}")
        raise
    
    # Extract metadata
    metadata = extract_image_metadata(img)
    
    # Perform OCR if requested
    ocr_text = None
    ocr_confidence = None
    
    if perform_ocr_flag:
        logger.info("Performing OCR on image")
        ocr_text = perform_ocr(img)
        if ocr_text:
            ocr_confidence = 0.7  # Placeholder, ideally this would be from the OCR engine
    
    # Copy file to output directory if provided
    storage_location = None
    if output_dir:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)
        
        # Create output file path
        output_file_path = output_dir_path / f"{image_id}_{Path(file_path).name}"
        
        # Copy file
        shutil.copy2(file_path, output_file_path)
        logger.info(f"Copied image file to: {output_file_path}")
        
        storage_location = "file_system"
    
    # Create image content object
    image_content = ImageContent(
        image_id=image_id,
        file_path=str(output_file_path) if output_dir else file_path,
        storage_location=storage_location,
        metadata=metadata,
        ocr_text_id=ocr_text.text_id if ocr_text else None,
        ocr_confidence=ocr_confidence,
        processing_timestamp=datetime.now()
    )
    
    logger.info(f"Image processing complete, ID: {image_id}")
    return image_content, ocr_text
