"""
PDF Bug Report Processor

This module provides functionality to extract raw content from PDF bug reports,
including text and images. It extracts all available content without attempting
to interpret it, storing the raw text and images for further processing.

This is part of Phase 1.3A: PDF Bug Report Data Extraction.
"""

import os
import io
import re
import uuid
import json
import base64
import logging
import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Union

import fitz  # PyMuPDF
import cv2
import numpy as np
from PIL import Image
import pytesseract

from core.utils.logging_utils import setup_logging
from core.utils.json_utils import save_json, load_json


class PDFProcessor:
    """Class for processing PDF bug reports and extracting raw content."""
    
    def __init__(self, output_dir: Optional[str] = None, 
                 log_level: int = logging.INFO,
                 ocr_enabled: bool = True):
        """Initialize the PDF processor.
        
        Args:
            output_dir: Directory to save extracted artifacts (images, etc.)
            log_level: Logging level
            ocr_enabled: Whether to use OCR to extract text from images
        """
        self.log_level = log_level
        
        # Set up enhanced logging
        log_dir = 'logs/pdf_processor'
        os.makedirs(log_dir, exist_ok=True)
        self.logger = setup_logging("pdf_processor", log_dir, log_level)
        
        # Set up output directory for artifacts
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path("data/pdf_artifacts")
        
        self.ocr_enabled = ocr_enabled
        self.logger.info(f"PDF Processor initialized with output dir: {self.output_dir}")
        self.logger.info(f"OCR enabled: {self.ocr_enabled}")
    
    def process_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Process a PDF bug report and extract its raw content.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dict containing raw content from the PDF, including all text and images
        """
        self.logger.info(f"Processing PDF: {pdf_path}")
        
        if not os.path.exists(pdf_path):
            err_msg = f"PDF file does not exist: {pdf_path}"
            self.logger.error(err_msg)
            raise FileNotFoundError(err_msg)
        
        # Create a timestamp-based directory for this PDF
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_name = os.path.basename(pdf_path)
        pdf_dir = self.output_dir / f"pdf_{timestamp}_{pdf_name}"
        pdf_dir.mkdir(parents=True, exist_ok=True)
        
        # Create an images directory within the PDF directory
        images_dir = pdf_dir / "images"
        images_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize result structure
        result = {
            "file_path": pdf_path,
            "filename": pdf_name,
            "extraction_time": timestamp,
            "output_directory": str(pdf_dir),
            "images_directory": str(images_dir),
            "pages": [],
            "images": [],
            "raw_text": "",
            "metadata": {}
        }
        
        try:
            # Open the PDF document
            doc = fitz.open(pdf_path)
            
            # Extract document metadata
            result["metadata"] = self._extract_metadata(doc)
            
            # Process each page
            for page_num, page in enumerate(doc):
                self.logger.info(f"Processing page {page_num+1} of {len(doc)}")
                page_content = self._process_page(page, page_num, images_dir)
                result["pages"].append(page_content)
                
                # Add page text to raw text with page marker
                result["raw_text"] += f"\n\n== PAGE {page_num+1} ==\n\n"
                result["raw_text"] += page_content["text"]
                
                # Add image references to the result
                result["images"].extend(page_content["images"])
            
            # Log completion
            self.logger.info(f"PDF processing complete. Extracted {len(result['pages'])} pages and "
                           f"{len(result['images'])} images.")
            
            # Save the raw text to a file
            with open(pdf_dir / "raw_text.txt", "w", encoding="utf-8") as f:
                f.write(result["raw_text"])
            self.logger.info(f"Saved raw text to {pdf_dir / 'raw_text.txt'}")
            
            # Save the extraction result
            output_file = pdf_dir / "extraction_result.json"
            save_json(result, str(output_file))
            self.logger.info(f"Saved extraction result to {output_file}")
            
        except Exception as e:
            self.logger.error(f"Error processing PDF: {str(e)}")
            raise
        
        return result
    
    def _extract_metadata(self, doc: fitz.Document) -> Dict[str, Any]:
        """Extract metadata from a PDF document.
        
        Args:
            doc: PyMuPDF document
            
        Returns:
            Dictionary of metadata
        """
        metadata = {}
        
        # Extract basic metadata
        metadata["title"] = doc.metadata.get("title", "")
        metadata["author"] = doc.metadata.get("author", "")
        metadata["subject"] = doc.metadata.get("subject", "")
        metadata["keywords"] = doc.metadata.get("keywords", "")
        metadata["creator"] = doc.metadata.get("creator", "")
        metadata["producer"] = doc.metadata.get("producer", "")
        metadata["pages"] = len(doc)
        metadata["creation_date"] = doc.metadata.get("creationDate", "")
        metadata["modification_date"] = doc.metadata.get("modDate", "")
        
        self.logger.info(f"Extracted metadata: title='{metadata['title']}', pages={metadata['pages']}")
        return metadata
    
    def _process_page(self, page: fitz.Page, page_num: int, output_dir: Path) -> Dict[str, Any]:
        """Process a single page from a PDF document.
        
        Args:
            page: PyMuPDF page object
            page_num: Page number (0-based)
            output_dir: Directory to save extracted images
            
        Returns:
            Dictionary containing page content
        """
        page_content = {
            "page_number": page_num + 1,  # 1-based for user-friendly display
            "text": "",
            "images": []
        }
        
        # Extract text
        page_content["text"] = page.get_text()
        
        # Extract images
        image_list = self._extract_images(page, output_dir)
        page_content["images"] = image_list
        
        # Perform OCR on images if enabled
        if self.ocr_enabled and image_list:
            ocr_text = self._perform_ocr_on_images(image_list)
            if ocr_text:
                self.logger.info(f"Added {len(ocr_text)} characters of OCR text from page {page_num+1}")
                page_content["ocr_text"] = ocr_text
                page_content["text"] += "\n\n" + ocr_text
        
        return page_content
    
    def _extract_images(self, page: fitz.Page, output_dir: Path) -> List[Dict[str, Any]]:
        """Extract images from a page.
        
        Args:
            page: PyMuPDF page object
            output_dir: Directory to save extracted images
            
        Returns:
            List of extracted images with metadata
        """
        extracted_images = []
        image_list = page.get_images(full=True)
        
        self.logger.info(f"Extracted {len(image_list)} images from page {page.number + 1}")
        
        for img_idx, img_info in enumerate(image_list):
            try:
                # Extract image
                xref = img_info[0]  # Cross-reference ID
                base_image = page.parent.extract_image(xref)
                
                if not base_image:
                    continue  # Skip if image extraction failed
                
                # Get image data and metadata
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                
                # Always convert to PNG or JPG for consistency
                if image_ext.lower() not in ['jpg', 'jpeg', 'png']:
                    try:
                        # Convert to PNG
                        image = Image.open(io.BytesIO(image_bytes))
                        img_buffer = io.BytesIO()
                        image.save(img_buffer, format='PNG')
                        image_bytes = img_buffer.getvalue()
                        image_ext = 'png'
                    except Exception as e:
                        self.logger.warning(f"Failed to convert image to PNG: {str(e)}")
                
                width = base_image.get("width", 0)
                height = base_image.get("height", 0)
                colorspace = base_image.get("colorspace", None)
                
                # Generate a unique filename
                img_filename = f"page_{page.number + 1}_img_{img_idx + 1}.{image_ext}"
                img_path = output_dir / img_filename
                
                # Save the image to disk
                with open(img_path, "wb") as img_file:
                    img_file.write(image_bytes)
                
                # Add to extracted images list
                extracted_images.append({
                    "filename": img_filename,
                    "path": str(img_path),
                    "page": page.number + 1,
                    "index": img_idx + 1,
                    "width": width,
                    "height": height,
                    "format": image_ext,
                    "colorspace": colorspace
                })
                
            except Exception as e:
                self.logger.warning(f"Failed to extract image {img_idx} from page {page.number + 1}: {str(e)}")
        
        return extracted_images
    
    def _perform_ocr_on_images(self, images: List[Dict[str, Any]]) -> str:
        """Perform OCR on a list of images.
        
        Args:
            images: List of images (with paths)
            
        Returns:
            Concatenated OCR text
        """
        ocr_text = ""
        
        for image in images:
            try:
                # Open the image file
                img = Image.open(image["path"])
                
                # Improve image for OCR - resize if too small
                if img.width < 300 or img.height < 300:
                    scale_factor = max(300 / img.width, 300 / img.height)
                    new_width = int(img.width * scale_factor)
                    new_height = int(img.height * scale_factor)
                    img = img.resize((new_width, new_height), Image.LANCZOS)
                
                # Convert to grayscale for better OCR
                img = img.convert('L')
                
                # Apply some image processing to improve OCR results
                img_np = np.array(img)
                img_np = cv2.GaussianBlur(img_np, (3, 3), 0)
                img_np = cv2.adaptiveThreshold(
                    img_np, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
                )
                
                # Convert back to PIL Image
                img_processed = Image.fromarray(img_np)
                
                # Perform OCR with pytesseract
                text = pytesseract.image_to_string(img_processed)
                
                if text.strip():
                    ocr_text += f"--- OCR from {os.path.basename(image['path'])} ---\n"
                    ocr_text += text + "\n\n"
            
            except Exception as e:
                self.logger.warning(f"OCR failed for image {image['filename']}: {str(e)}")
        
        return ocr_text
    
    def create_raw_data_package(self, pdf_result: Dict[str, Any], name: Optional[str] = None) -> Dict[str, Any]:
        """Create a raw data package from the extracted PDF content.
        
        This focuses on providing raw data rather than trying to interpret it,
        as interpretation will be handled in Phase 1.3B by the LLM.
        
        Args:
            pdf_result: Result from process_pdf
            name: Optional name for the data package
                
        Returns:
            Raw data package with full text and image references
        """
        # Generate a name based on the PDF filename if none provided
        if not name:
            pdf_name = os.path.splitext(pdf_result["filename"])[0]
            name = f"bug_{pdf_name.lower().replace(' ', '_')}"
        
        # Create a raw data package
        raw_data_package = {
            "name": name,
            "description": f"Raw data extraction for {pdf_result['filename']}",
            "source": "pdf",
            "source_file": pdf_result["file_path"],
            "output_directory": pdf_result["output_directory"],
            "raw_text_file": os.path.join(pdf_result["output_directory"], "raw_text.txt"),
            "raw_text": pdf_result["raw_text"],
            "metadata": pdf_result["metadata"],
            "images_directory": pdf_result["images_directory"],
            "images": pdf_result["images"],
            "total_pages": len(pdf_result["pages"]),
            "total_images": len(pdf_result["images"])
        }
        
        self.logger.info(f"Created raw data package: {name} with {raw_data_package['total_pages']} pages and {raw_data_package['total_images']} images")
        return raw_data_package


def process_bug_report(pdf_path: str, output_dir: Optional[str] = None) -> Dict[str, Any]:
    """Process a PDF bug report and extract raw text and images.
    
    This function is the main entry point for PDF processing and focuses on 
    extracting all raw content without interpretation.
    
    Args:
        pdf_path: Path to the PDF bug report
        output_dir: Optional directory to save extracted artifacts
        
    Returns:
        Dictionary containing the raw extracted data
    """
    processor = PDFProcessor(output_dir=output_dir)
    pdf_result = processor.process_pdf(pdf_path)
    raw_data_package = processor.create_raw_data_package(pdf_result)
    
    # Save the raw data package to a JSON file using custom encoder
    if output_dir:
        output_path = Path(output_dir) / f"{raw_data_package['name']}_raw_data.json"
        save_json(raw_data_package, str(output_path), pretty=True)
    
    return {
        "pdf_result": pdf_result,
        "raw_data_package": raw_data_package
    }
