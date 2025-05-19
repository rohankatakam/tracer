"""
Image Attachment Processor

This module handles processing of image file attachments (.jpg, .jpeg, .png) by:
1. Loading and validating the image
2. Extracting comprehensive image metadata
3. Performing enhanced OCR using Tesseract with preprocessing
4. Creating structured representations for storage in the database
5. Integrating with the PostgreSQL database for efficient storage and retrieval
"""

import os
import sys
import logging
import uuid
import shutil
import math
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple
import mimetypes

import numpy as np
from PIL import Image, ExifTags, ImageFilter, ImageEnhance, ImageDraw, ImageFont
import pytesseract
import cv2

# Add the project root to the path to allow importing from modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, project_root)

# Import the attachment schema and database connector
from core.models.attachment_schema import ImageContent, TextContent, ImageMetadata
from core.database.attachment_db import store_image_content, store_text_content


def extract_image_metadata(img: Image.Image, file_path: str) -> Dict[str, Any]:
    """
    Extract comprehensive metadata from an image.
    
    Args:
        img: PIL Image object
        file_path: Path to the image file
        
    Returns:
        Dictionary with detailed image metadata
    """
    # Initialize metadata with basic image properties
    metadata = {
        'width': img.width,
        'height': img.height,
        'format': img.format if img.format else "Unknown",
        'color_mode': img.mode,
        'aspect_ratio': round(img.width / img.height, 3) if img.height != 0 else None,
        'file_size_bytes': os.path.getsize(file_path),
        'mime_type': mimetypes.guess_type(file_path)[0] or f'image/{img.format.lower() if img.format else "unknown"}',
        'last_modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
        'created': datetime.fromtimestamp(os.path.getctime(file_path)).isoformat(),
    }
    
    # Calculate image hash for potential duplicate detection
    try:
        # Resize to thumbnail for faster hashing
        thumb = img.copy()
        thumb.thumbnail((100, 100))
        img_hash = hashlib.md5(thumb.tobytes()).hexdigest()
        metadata['hash_md5'] = img_hash
    except Exception as e:
        logging.warning(f"Could not generate image hash: {str(e)}")
    
    # Get color mode-specific information
    try:
        if img.mode == "1":  # Binary (1-bit)
            metadata['bits_per_pixel'] = 1
            metadata['color_depth'] = '1-bit monochrome'
        elif img.mode == "L":  # Grayscale (8-bit)
            metadata['bits_per_pixel'] = 8
            metadata['color_depth'] = '8-bit grayscale'
        elif img.mode == "P":  # Palette (8-bit)
            metadata['bits_per_pixel'] = 8
            metadata['color_depth'] = '8-bit palette'
            metadata['palette_size'] = len(img.getcolors(maxcolors=65536)) if img.getcolors(maxcolors=65536) else 'Over 65536'
        elif img.mode == "RGB":  # RGB (24-bit)
            metadata['bits_per_pixel'] = 24
            metadata['color_depth'] = '24-bit RGB'
        elif img.mode == "RGBA":  # RGBA (32-bit)
            metadata['bits_per_pixel'] = 32
            metadata['color_depth'] = '32-bit RGBA'
            metadata['has_transparency'] = True
        elif img.mode == "CMYK":  # CMYK (32-bit)
            metadata['bits_per_pixel'] = 32
            metadata['color_depth'] = '32-bit CMYK'
    except Exception as e:
        logging.warning(f"Error determining color properties: {str(e)}")
    
    # Try to get DPI information
    try:
        dpi = img.info.get('dpi')
        if dpi and len(dpi) >= 2:
            metadata['dpi'] = int(dpi[0])
    except (AttributeError, KeyError, IndexError, TypeError):
        pass
    
    # Extract EXIF data if available
    try:
        exif_data = {}
        if hasattr(img, '_getexif') and img._getexif() is not None:
            for tag, value in img._getexif().items():
                tag_name = ExifTags.TAGS.get(tag, str(tag))
                # Exclude binary data which doesn't serialize well
                if isinstance(value, (str, int, float, bool)):
                    exif_data[tag_name] = value
                elif isinstance(value, bytes):
                    # We don't include binary data but we note its presence
                    exif_data[tag_name] = f"<binary data: {len(value)} bytes>"
            
            # Extract capture device information
            if 'Make' in exif_data or 'Model' in exif_data:
                metadata['capture_device'] = {
                    'make': exif_data.get('Make'),
                    'model': exif_data.get('Model')
                }
            
            # Extract geo-location if available
            if 'GPSInfo' in exif_data:
                gps_info = exif_data['GPSInfo']
                metadata['geo_location'] = {
                    'latitude': gps_info.get('GPSLatitude'),
                    'longitude': gps_info.get('GPSLongitude'),
                    'altitude': gps_info.get('GPSAltitude')
                }
            
            # Extract creation date
            if 'DateTimeOriginal' in exif_data:
                metadata['date_taken'] = exif_data['DateTimeOriginal']
            
            # Store full EXIF data
            metadata['exif'] = exif_data
    except Exception as e:
        logging.warning(f"Error extracting EXIF data: {str(e)}")
    
    # Image quality assessment (very basic)
    try:
        # Convert to grayscale for analysis
        img_gray = img.convert('L')
        img_array = np.array(img_gray)
        
        # Calculate basic sharpness (variance of Laplacian)
        laplacian = cv2.Laplacian(img_array, cv2.CV_64F)
        sharpness = laplacian.var()
        metadata['sharpness_score'] = round(sharpness, 2)
        
        # Determine if image is likely a screenshot, diagram, or photo
        histogram = img_gray.histogram()
        unique_colors = sum(1 for count in histogram if count > 0)
        color_variance = np.std(histogram)
        
        if unique_colors < 50 or color_variance < 1000:
            metadata['content_type_estimate'] = 'diagram/illustration'
        elif metadata.get('sharpness_score', 0) > 500:
            metadata['content_type_estimate'] = 'screenshot/computer-generated'
        else:
            metadata['content_type_estimate'] = 'photograph'
    except Exception as e:
        logging.warning(f"Error performing image quality assessment: {str(e)}")
    
    # Create ImageMetadata object with the core required fields
    image_metadata = ImageMetadata(
        width=img.width,
        height=img.height,
        format=metadata['format'],
        color_mode=metadata['color_mode'],
        dpi=metadata.get('dpi'),
        bits_per_pixel=metadata.get('bits_per_pixel')
    )
    
    # Store the full metadata dictionary in ImageMetadata's metadata field
    return metadata, image_metadata


def perform_enhanced_ocr(img: Image.Image, image_id: str = None, attachment_id: str = None) -> Tuple[Optional[TextContent], Optional[float]]:
    """
    Perform enhanced OCR on an image with multiple preprocessing techniques.
    
    Args:
        img: PIL Image object
        image_id: Optional ID to associate with the image
        
    Returns:
        Tuple of (TextContent object with OCR results or None if no text was found,
                 Confidence score of OCR result)
    """
    logger = logging.getLogger("image_processor")
    logger.info("Performing enhanced OCR")
    
    # Create a unique ID for this OCR text content
    text_id = str(uuid.uuid4())
    
    try:
        # Create a working copy of the image
        working_img = img.copy()
        
        # Resize very large images to improve OCR performance
        max_dimension = max(working_img.width, working_img.height)
        if max_dimension > 3000:
            scale_factor = 3000 / max_dimension
            new_width = int(working_img.width * scale_factor)
            new_height = int(working_img.height * scale_factor)
            logger.info(f"Resizing image from {working_img.width}x{working_img.height} to {new_width}x{new_height} for OCR")
            working_img = working_img.resize((new_width, new_height), Image.LANCZOS)
        
        # Convert to numpy array for OpenCV processing
        img_np = np.array(working_img)
        
        # Check if we need to convert to grayscale
        if len(img_np.shape) == 3 and img_np.shape[2] >= 3:
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_np
            
        # Create multiple processed versions of the image with different techniques
        processed_versions = []
        
        # Version 1: Basic grayscale with denoising
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        processed_versions.append(("denoised", Image.fromarray(denoised)))
        
        # Version 2: Otsu's thresholding
        _, binary_otsu = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        processed_versions.append(("otsu", Image.fromarray(binary_otsu)))
        
        # Version 3: Adaptive thresholding
        binary_adaptive = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        processed_versions.append(("adaptive", Image.fromarray(binary_adaptive)))
        
        # Version 4: Dilated after thresholding
        kernel = np.ones((1, 1), np.uint8)
        dilated = cv2.dilate(binary_otsu, kernel, iterations=1)
        processed_versions.append(("dilated", Image.fromarray(dilated)))
        
        # Version 5: Edge enhanced
        edge_enhanced = working_img.filter(ImageFilter.EDGE_ENHANCE)
        processed_versions.append(("edge_enhanced", edge_enhanced))
        
        # Version 6: Contrast enhanced
        contrast_enhanced = ImageEnhance.Contrast(working_img).enhance(1.5)
        processed_versions.append(("contrast", contrast_enhanced))
        
        # Perform OCR on all versions and select the best result
        best_text = ""
        best_score = 0.0
        best_version = ""
        ocr_data = {}
        
        for version_name, processed_img in processed_versions:
            try:
                # Get detailed OCR data with confidence scores
                ocr_data_dict = pytesseract.image_to_data(processed_img, output_type=pytesseract.Output.DICT)
                
                # Extract text and confidence scores
                text_parts = []
                confidences = []
                
                for i in range(len(ocr_data_dict['text'])):
                    if int(ocr_data_dict['conf'][i]) > 0:  # Confidence above 0
                        text_parts.append(ocr_data_dict['text'][i])
                        confidences.append(int(ocr_data_dict['conf'][i]))
                
                # Join text parts with proper spacing
                text = ' '.join(text_parts)
                
                # Calculate average confidence for non-empty words
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                scaled_confidence = avg_confidence / 100.0  # Scale to 0-1 range
                
                # Compare results and keep the best one
                if text.strip() and (len(text) > len(best_text) or 
                                   (len(text) == len(best_text) and scaled_confidence > best_score)):
                    best_text = text
                    best_score = scaled_confidence
                    best_version = version_name
                    ocr_data[version_name] = {
                        'text': text,
                        'confidence': scaled_confidence
                    }
            except Exception as e:
                logger.warning(f"OCR failed for {version_name} version: {str(e)}")
        
        logger.info(f"Best OCR result from {best_version} version with confidence {best_score:.2f}")
        
        # Create text content only if text was found
        if best_text.strip():
            # Create TextContent object
            text_content = TextContent(
                text_id=text_id,
                content=best_text,
                language=None,  # Could use a language detection library here
                encoding="utf-8",
                extraction_method="ocr",
                processing_timestamp=datetime.now(),
                source_image_id=image_id,
                source_attachment_id=attachment_id,
                metadata={
                    'ocr_confidence': best_score,
                    'ocr_method': 'tesseract',
                    'ocr_best_version': best_version,
                    'ocr_versions_tested': list(ocr_data.keys()),
                    'word_count': len(best_text.split())
                }
            )
            return text_content, best_score
        else:
            logger.info("No text found in image during OCR")
            return None, None
    
    except Exception as e:
        logger.error(f"Error performing OCR: {str(e)}")
        return None, None


def process_image_file(file_path: str, output_dir: Optional[str] = None,
                      perform_ocr_flag: bool = True,
                      store_in_db: bool = True,
                      attachment_id: Optional[str] = None) -> Tuple[ImageContent, Optional[TextContent]]:
    """
    Process an image file attachment with enhanced OCR and metadata extraction.
    
    Args:
        file_path: Path to the image file
        output_dir: Optional directory to store the processed file
        perform_ocr_flag: Whether to perform OCR on the image
        store_in_db: Whether to store the content in the database
        
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
    
    # Extract enhanced metadata
    metadata_dict, metadata_obj = extract_image_metadata(img, file_path)
    logger.info(f"Extracted metadata with {len(metadata_dict)} attributes")
    
    # Perform OCR if requested
    ocr_text = None
    ocr_confidence = None
    
    if perform_ocr_flag:
        logger.info("Performing enhanced OCR on image")
        ocr_text, ocr_confidence = perform_enhanced_ocr(img, image_id, attachment_id)
        
        if ocr_text:
            logger.info(f"OCR extracted {len(ocr_text.content.split())} words with confidence {ocr_confidence:.2f}")
            
            # Store OCR text in database if requested
            if store_in_db and ocr_text:
                try:
                    stored_text_id = store_text_content(ocr_text)
                    logger.info(f"Stored OCR text in database with ID: {stored_text_id}")
                except Exception as e:
                    logger.error(f"Failed to store OCR text in database: {str(e)}")
    
    # Copy file to output directory if provided
    storage_location = None
    output_file_path = None
    
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
        metadata=metadata_obj,
        ocr_text_id=ocr_text.text_id if ocr_text else None,
        ocr_confidence=ocr_confidence,
        processing_timestamp=datetime.now(),
        source_attachment_id=attachment_id
    )
    
    # Store additional extracted metadata
    if hasattr(image_content, 'metadata') and hasattr(image_content.metadata, '__dict__'):
        # Store the full metadata dictionary
        for key, value in metadata_dict.items():
            # Only add items not already in the core metadata fields
            if not hasattr(image_content.metadata, key):
                image_content.metadata.__dict__[key] = value
    
    # Save to database if requested
    if store_in_db:
        try:
            stored_id = store_image_content(image_content)
            logger.info(f"Stored image content in database with ID: {stored_id}")
        except Exception as e:
            logger.error(f"Failed to store image content in database: {str(e)}")
    
    logger.info(f"Image processing complete, ID: {image_id}")
    return image_content, ocr_text
