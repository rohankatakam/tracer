"""
PDF Bug Report Processor

This module provides functionality to extract content from PDF bug reports,
including text, images, and structured content. It transforms PDF documents
into a format that can be processed by the CUA test framework.

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

from src.utils.logging_utils import setup_logging
from src.utils.json_utils import save_json, load_json


class PDFProcessor:
    """Class for processing PDF bug reports and extracting content."""
    
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
        
        self.images_dir = self.output_dir / "images"
        self.images_dir.mkdir(parents=True, exist_ok=True)
        
        self.ocr_enabled = ocr_enabled
        self.logger.info(f"PDF Processor initialized with output dir: {self.output_dir}")
        self.logger.info(f"OCR enabled: {self.ocr_enabled}")
    
    def process_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Process a PDF bug report and extract its content.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dict containing structured content from the PDF
        """
        self.logger.info(f"Processing PDF: {pdf_path}")
        
        if not os.path.exists(pdf_path):
            err_msg = f"PDF file does not exist: {pdf_path}"
            self.logger.error(err_msg)
            raise FileNotFoundError(err_msg)
        
        # Create a timestamp-based directory for this PDF
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_dir = self.output_dir / f"pdf_{timestamp}_{os.path.basename(pdf_path)}"
        pdf_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize result structure
        result = {
            "file_path": pdf_path,
            "filename": os.path.basename(pdf_path),
            "extraction_time": timestamp,
            "pages": [],
            "images": [],
            "extracted_text": "",
            "metadata": {},
            "bug_steps": []
        }
        
        try:
            # Open the PDF document
            doc = fitz.open(pdf_path)
            
            # Extract document metadata
            result["metadata"] = self._extract_metadata(doc)
            
            # Process each page
            for page_num, page in enumerate(doc):
                self.logger.info(f"Processing page {page_num+1} of {len(doc)}")
                page_content = self._process_page(page, page_num, pdf_dir)
                result["pages"].append(page_content)
                result["extracted_text"] += page_content["text"] + "\n\n"
                result["images"].extend(page_content["images"])
            
            # Extract bug steps from the content
            result["bug_steps"] = self._extract_bug_steps(result["extracted_text"])
            
            self.logger.info(f"PDF processing complete. Extracted {len(result['pages'])} pages, "
                            f"{len(result['images'])} images, and {len(result['bug_steps'])} bug steps.")
            
            # Save the extracted result to a JSON file
            result_path = pdf_dir / "extraction_result.json"
            save_json(result, str(result_path), pretty=True)
            self.logger.info(f"Saved extraction result to {result_path}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing PDF: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            raise
    
    def _extract_metadata(self, doc: fitz.Document) -> Dict[str, Any]:
        """Extract metadata from a PDF document.
        
        Args:
            doc: PyMuPDF document
            
        Returns:
            Dictionary of metadata
        """
        metadata = {
            "title": doc.metadata.get("title", ""),
            "author": doc.metadata.get("author", ""),
            "subject": doc.metadata.get("subject", ""),
            "keywords": doc.metadata.get("keywords", ""),
            "creator": doc.metadata.get("creator", ""),
            "producer": doc.metadata.get("producer", ""),
            "creation_date": doc.metadata.get("creationDate", ""),
            "modification_date": doc.metadata.get("modDate", ""),
            "page_count": len(doc)
            # Note: filesize attribute doesn't exist in current PyMuPDF version
        }
        
        self.logger.info(f"Extracted metadata: title='{metadata['title']}', pages={metadata['page_count']}")
        return metadata
    
    def _process_page(self, page: fitz.Page, page_num: int, output_dir: Path) -> Dict[str, Any]:
        """Process a single page from a PDF document.
        
        Args:
            page: PyMuPDF page object
            page_num: Page number (0-based)
            output_dir: Directory to save extracted content
            
        Returns:
            Dictionary containing page content
        """
        page_content = {
            "page_number": page_num + 1,  # 1-based for user-friendly display
            "text": "",
            "images": [],
            "tables": []
        }
        
        # Create directory for page-specific content
        page_dir = output_dir / f"page_{page_num+1}"
        page_dir.mkdir(exist_ok=True)
        
        # Extract text
        page_content["text"] = page.get_text()
        
        # Save the text to a file
        text_path = page_dir / "text.txt"
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(page_content["text"])
        
        # Extract images
        image_list = self._extract_images(page, page_dir)
        page_content["images"] = image_list
        
        # Perform OCR on images if enabled
        if self.ocr_enabled and image_list:
            ocr_text = self._perform_ocr_on_images(image_list)
            if ocr_text:
                # Save OCR text to file
                ocr_path = page_dir / "ocr_text.txt"
                with open(ocr_path, "w", encoding="utf-8") as f:
                    f.write(ocr_text)
                
                self.logger.info(f"Added {len(ocr_text)} characters of OCR text from page {page_num+1}")
                page_content["ocr_text"] = ocr_text
                page_content["text"] += "\n\n" + ocr_text
        
        # Extract tables
        tables = self._extract_tables(page)
        if tables:
            page_content["tables"] = tables
            # Save tables to JSON
            tables_path = page_dir / "tables.json"
            save_json(tables, str(tables_path))
        
        return page_content
    
    def _extract_images(self, page: fitz.Page, output_dir: Path) -> List[Dict[str, Any]]:
        """Extract images from a page.
        
        Args:
            page: PyMuPDF page object
            output_dir: Directory to save extracted images
            
        Returns:
            List of extracted images with metadata
        """
        image_list = page.get_images(full=True)
        images = []
        
        # Create directory for images
        images_dir = output_dir / "images"
        images_dir.mkdir(exist_ok=True)
        
        for img_index, img_info in enumerate(image_list):
            try:
                img_id = img_info[0]  # Image ID/reference
                base_img = page.parent.extract_image(img_id)
                image_bytes = base_img["image"]
                
                # Generate a unique filename
                img_filename = f"page_{page.number+1}_img_{img_index+1}.png"
                img_path = images_dir / img_filename
                
                # Save the image
                with open(img_path, "wb") as img_file:
                    img_file.write(image_bytes)
                
                # Get image properties
                image_info = {
                    "filename": img_filename,
                    "path": str(img_path),
                    "width": base_img["width"],
                    "height": base_img["height"],
                    "colorspace": base_img.get("colorspace", ""),
                    "xres": base_img.get("xres", 0),
                    "yres": base_img.get("yres", 0),
                }
                
                # Convert image to base64 for including in JSON
                if base_img["width"] * base_img["height"] < 1000000:  # Only include small images
                    image_info["base64"] = base64.b64encode(image_bytes).decode('utf-8')
                
                images.append(image_info)
                self.logger.debug(f"Extracted image {img_filename}: {base_img['width']}x{base_img['height']}")
            
            except Exception as e:
                self.logger.warning(f"Error extracting image: {str(e)}")
        
        self.logger.info(f"Extracted {len(images)} images from page {page.number+1}")
        return images
    
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
    
    def _extract_tables(self, page: fitz.Page) -> List[Dict[str, Any]]:
        """Extract table-like structures from a page.
        
        This is a simple heuristic-based approach. For more complex table extraction,
        consider using dedicated libraries like Camelot or Tabula.
        
        Args:
            page: PyMuPDF page object
            
        Returns:
            List of extracted tables
        """
        tables = []
        
        # Simple heuristic: Look for text with multiple pipe characters or tabs
        text = page.get_text()
        lines = text.split('\n')
        
        table_data = []
        in_table = False
        
        for line in lines:
            # Count pipes and tabs as potential table indicators
            pipe_count = line.count('|')
            tab_count = line.count('\t')
            
            if pipe_count > 2 or tab_count > 2:
                # Potential table row
                if not in_table:
                    in_table = True
                    table_data = []
                
                # Process the row based on the delimiter
                if pipe_count > tab_count:
                    cells = [cell.strip() for cell in line.split('|')]
                else:
                    cells = [cell.strip() for cell in line.split('\t')]
                
                table_data.append(cells)
            else:
                # Not a table row
                if in_table and len(table_data) > 2:  # Require at least 3 rows to be a valid table
                    tables.append({
                        "rows": len(table_data),
                        "columns": max(len(row) for row in table_data),
                        "data": table_data
                    })
                
                in_table = False
        
        # Handle case where table is at the end of the page
        if in_table and len(table_data) > 2:
            tables.append({
                "rows": len(table_data),
                "columns": max(len(row) for row in table_data),
                "data": table_data
            })
        
        self.logger.info(f"Extracted {len(tables)} potential tables from page {page.number+1}")
        return tables
    
    def _extract_bug_steps(self, text: str) -> List[str]:
        """Extract bug reproduction steps from text.
        
        This method looks for patterns in the text that indicate bug steps,
        such as numbered lists or phrases like "Steps to reproduce".
        
        Args:
            text: Extracted text from the PDF
            
        Returns:
            List of bug steps
        """
        self.logger.info("Extracting bug steps from text")
        steps = []
        
        try:
            # Normalize text for easier pattern matching
            normalized_text = text.replace("\t", " ").replace("\r", "")
            
            # Try to detect a reproduction steps section
            steps_section_patterns = [
                r"(?i)steps to reproduce\s*:\s*\n",
                r"(?i)reproduction steps\s*:\s*\n",
                r"(?i)steps to repro\s*:\s*\n",
                r"(?i)steps\s*:\s*\n",
                r"(?i)to reproduce\s*:\s*\n",
                r"(?i)how to reproduce\s*:\s*\n"
            ]
            
            # Look for "Steps to reproduce" section
            section_start = -1
            section_pattern_matched = None
            
            for pattern in steps_section_patterns:
                match = re.search(pattern, normalized_text)
                if match:
                    section_start = match.end()
                    section_pattern_matched = match.group(0)
                    break
            
            if section_start > 0:
                self.logger.info(f"Found bug steps section starting with: '{section_pattern_matched.strip()}'")
                
                # Extract the section
                section_text = normalized_text[section_start:]
                
                # Look for the end of the section (e.g., the next section header)
                section_end_indicators = [
                    r"(?i)expected result\s*:",
                    r"(?i)actual result\s*:",
                    r"(?i)observed behavior\s*:",
                    r"(?i)environment\s*:",
                    r"(?i)additional information\s*:"
                ]
                
                section_end = len(section_text)
                for indicator in section_end_indicators:
                    match = re.search(indicator, section_text)
                    if match and match.start() > 0 and match.start() < section_end:
                        section_end = match.start()
                
                section_text = section_text[:section_end].strip()
                
                # Split into lines and process
                lines = section_text.split("\n")
                current_step = ""
                current_step_num = 0
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Try to detect if this is a new step
                    is_new_step = False
                    step_num = None
                    
                    # Check for numbered steps (e.g., "1.", "1)", "Step 1:")
                    if line[0].isdigit():
                        # Try to extract step number
                        match = re.match(r"(\d+)[.):] ", line)
                        if match:
                            step_num = int(match.group(1))
                            is_new_step = True
                    elif re.match(r"(?i)step\s+\d+", line):
                        # Try to extract step number from "Step N:" format
                        match = re.match(r"(?i)step\s+(\d+)[:.] ?", line)
                        if match:
                            step_num = int(match.group(1))
                            is_new_step = True
                    
                    if is_new_step and step_num is not None:
                        # Save the previous step if any
                        if current_step and current_step_num > 0:
                            steps.append(current_step.strip())
                        
                        # Start new step
                        current_step_num = step_num
                        
                        # Remove the step number prefix from the line
                        if line[0].isdigit():
                            # Remove "1. " or similar
                            match = re.match(r"\d+[.):] ", line)
                            if match:
                                current_step = line[match.end():]
                            else:
                                current_step = line
                        elif re.match(r"(?i)step\s+\d+", line):
                            # Remove "Step 1: " or similar
                            match = re.match(r"(?i)step\s+\d+[:.] ?", line)
                            if match:
                                current_step = line[match.end():]
                            else:
                                current_step = line
                    else:
                        # Continue the current step
                        if current_step_num > 0:
                            current_step += " " + line
                
                # Add the last step if any
                if current_step and current_step_num > 0:
                    steps.append(current_step.strip())
            
            # If no steps were found using the above methods, try simpler approaches
            if not steps:
                self.logger.warning("No structured steps section found. Using text pattern matching.")
                
                # Try numbered steps format: "1. Step one", "2. Step two", etc.
                numbered_steps_pattern = r"(\d+)[.):]\s+([^\n]+)"
                numbered_matches = re.findall(numbered_steps_pattern, normalized_text)
                
                if numbered_matches and len(numbered_matches) >= 2:  # At least 2 steps to be considered valid
                    steps = [step_text.strip() for _, step_text in numbered_matches]
                    self.logger.info(f"Found {len(steps)} numbered steps using pattern matching")
                else:
                    # Try bullet point steps format: "• Step one", "• Step two", etc.
                    bullet_pattern = r"[•\*-]\s+([^\n]+)"
                    bullet_matches = re.findall(bullet_pattern, normalized_text)
                    
                    if bullet_matches and len(bullet_matches) >= 2:  # At least 2 steps to be considered valid
                        steps = [step.strip() for step in bullet_matches]
                        self.logger.info(f"Found {len(steps)} bullet point steps")
                    else:
                        # Try to find steps by looking for keywords like "Click", "Enter", etc.
                        action_steps = []
                        action_verbs = ["click", "select", "enter", "type", "navigate", "go to", "open", "check"]
                        
                        # Use a regex to find sentences containing action verbs
                        action_pattern = r"([^.\n]+(?:" + "|".join(action_verbs) + r")[^.\n]+\.)"
                        action_matches = re.findall(action_pattern, normalized_text.lower())
                        
                        if action_matches and len(action_matches) >= 2:
                            steps = [step.strip() for step in action_matches]
                            self.logger.info(f"Found {len(steps)} action-based steps")
                        else:
                            # Last resort: just split by sentences
                            sentences = re.split(r'\.', normalized_text)
                            potential_steps = [s.strip() for s in sentences if len(s.strip()) > 15]
                            
                            if len(potential_steps) >= 2:
                                steps = potential_steps[:min(10, len(potential_steps))]  # Limit to 10 steps
                                self.logger.warning(f"No clear steps found, using {len(steps)} sentences as steps")
        
        except Exception as e:
            self.logger.error(f"Error extracting bug steps: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
        
        # Clean up steps - remove very short or duplicate steps
        steps = [step for step in steps if len(step) > 5]
        
        # Remove duplicate steps
        unique_steps = []
        for step in steps:
            if step not in unique_steps:
                unique_steps.append(step)
        
        self.logger.info(f"Extracted {len(unique_steps)} bug steps")
        return unique_steps
    
    def convert_to_test_case(self, pdf_result: Dict[str, Any], name: Optional[str] = None) -> Dict[str, Any]:
        """Convert the extracted PDF content to a CUA test case format.
        
        Args:
            pdf_result: Result from process_pdf
            name: Optional name for the test case
                
        Returns:
            Test case in the format expected by the CUA test framework
        """
        if not name:
            # Generate a name based on the PDF filename
            name = f"bug_{os.path.splitext(pdf_result['filename'])[0]}"
        
        # Get bug steps
        bug_steps = pdf_result.get("bug_steps", [])
        if not bug_steps:
            self.logger.warning("No bug steps found in PDF. Creating a minimal test case.")
            bug_steps = ["Navigate to the application"]
        
        # Create test case
        test_case = {
            "name": name,
            "description": f"Bug reproduction test case from {pdf_result['filename']}",
            "steps": []
        }
        
        # Convert bug steps to test steps
        for i, step_text in enumerate(bug_steps):
            prompt = self._format_prompt_for_step(step_text)
            validation_keyword = self._extract_validation_keyword(step_text)
            
            test_step = {
                "name": f"Step {i+1}",
                "prompt": prompt,
                "validation": {
                    "type": "text_content",
                    "params": {
                        "text": validation_keyword
                    }
                }
            }
            test_case["steps"].append(test_step)
        
        self.logger.info(f"Converted to test case: {test_case['name']} with {len(test_case['steps'])} steps")
        return test_case
    
    def _extract_validation_keyword(self, step_text: str) -> str:
        """Extract a keyword that can be used for validation from the step text.
        
        This is a simple approach - in a real implementation, you'd use NLP
        to identify key elements that should be present after the step.
        
        Args:
            step_text: Text of the bug step
            
        Returns:
            A keyword for validation
        """
        # Clean up the step text
        text = step_text.strip().lower()
        
        # Look for keywords that might be good validation targets
        validation_targets = ["page", "form", "button", "field", "menu", "option", "dialog", "error", "message"]
        
        for target in validation_targets:
            if target in text:
                # Try to get a few words around the target
                words = text.split()
                for i, word in enumerate(words):
                    if target in word:
                        # Get a context window around the word
                        start = max(0, i - 2)
                        end = min(len(words), i + 3)
                        return " ".join(words[start:end])
        
        # Look for UI elements
        ui_elements = ["button", "link", "page", "dialog", "menu", "tab"]
        for element in ui_elements:
            if element in text:
                # Extract the phrase containing the UI element
                before, after = text.split(element, 1)
                # Get the words around the element
                words_before = before.split()[-3:] if len(before.split()) > 3 else before.split()
                words_after = after.split()[:3] if len(after.split()) > 3 else after.split()
                
                phrase = " ".join(words_before + [element] + words_after)
                return phrase.strip(".,:;() ")
        
        # Look for action targets
        action_verbs = ["click", "select", "enter", "type", "navigate", "go to", "open"]
        for verb in action_verbs:
            if verb in text:
                # Extract what comes after the verb
                after = text.split(verb, 1)[1]
                # Get a few words after the verb
                words = after.split()[:5] if len(after.split()) > 5 else after.split()
                
                return " ".join(words).strip(".,:;() ")
        
        # Fallback: return a substring
        words = text.split()
        if len(words) > 5:
            return " ".join(words[2:5])  # Take a few words from the middle
        else:
            return text  # Return the whole step if it's short
    
    def _truncate_text(self, text: str, max_length: int) -> str:
        """Truncate text to a maximum length, adding ellipsis if needed.
        
        Args:
            text: Text to truncate
            max_length: Maximum length
            
        Returns:
            Truncated text
        """
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."
    
    def _format_prompt_for_step(self, step_text: str) -> str:
        """Format a bug step as a prompt for the CUA agent.
        
        This method converts a bug step description into a clear
        action-oriented prompt for the Computer Use Agent.
        
        Args:
            step_text: Text of the bug step
            
        Returns:
            Formatted prompt
        """
        # Clean up the step text
        step_text = step_text.strip()
        
        # Check if the step already starts with an action verb
        action_verbs = ["click", "select", "enter", "type", "navigate", 
                        "go", "open", "check", "verify", "scroll"]
        
        first_word = step_text.split()[0].lower() if step_text else ""
        
        if first_word in action_verbs:
            # Step already starts with a verb, use as is
            return step_text
        
        # Try to identify the action in the step
        for verb in action_verbs:
            if verb in step_text.lower():
                # Extract and restructure around the verb
                parts = step_text.lower().split(verb, 1)
                return f"{verb.capitalize()} {parts[1].strip()}"
        
        # If no clear action verb, use a generic prompt
        return f"Perform the following action: {step_text}"


def process_bug_report(pdf_path: str, output_dir: Optional[str] = None) -> Dict[str, Any]:
    """Process a PDF bug report and convert it to a test case.
    
    Args:
        pdf_path: Path to the PDF bug report
        output_dir: Optional directory to save extracted artifacts
        
    Returns:
        Dictionary containing the processed test case
    """
    processor = PDFProcessor(output_dir=output_dir)
    pdf_result = processor.process_pdf(pdf_path)
    test_case = processor.convert_to_test_case(pdf_result)
    
    # Save the test case to a JSON file using custom encoder
    if output_dir:
        output_path = Path(output_dir) / f"{test_case['name']}_test_case.json"
        save_json(test_case, str(output_path), pretty=True)
    
    return {
        "pdf_result": pdf_result,
        "test_case": test_case
    }
