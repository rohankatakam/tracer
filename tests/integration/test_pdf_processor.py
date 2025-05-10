#!/usr/bin/env python
"""Test script for the PDF processor implementation (Phase 1.3A).

This script tests the extraction of content from a PDF bug report and
converts it to a test case for the CUA test framework.
"""

import os
import sys
import logging
from pathlib import Path

# Add the project root to Python path for imports when run directly
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.utils.logging_utils import setup_logging
from src.ingestion.pdf_processor import PDFProcessor, process_bug_report

# Set up logging
log_dir = os.path.join(project_root, "logs/test")
os.makedirs(log_dir, exist_ok=True)
logger = setup_logging("pdf_processor_test", log_dir, logging.INFO)

def find_pdf_files(directory: str) -> list:
    """Find PDF files in the directory."""
    pdf_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(root, file))
    return pdf_files

def run_test(pdf_path: str = None):
    """Run the PDF processor test.
    
    Args:
        pdf_path: Path to a PDF file to process. If None, will look for PDFs in the data directory.
    """
    logger.info("Starting PDF processor test")
    
    # Create output directory
    output_dir = os.path.join(project_root, "data/test_outputs/pdf")
    os.makedirs(output_dir, exist_ok=True)
    
    # If no PDF specified, look in test_inputs/pdf directory
    if not pdf_path:
        test_inputs_dir = os.path.join(project_root, "data/test_inputs/pdf")
        if not os.path.exists(test_inputs_dir):
            os.makedirs(test_inputs_dir, exist_ok=True)
        
        pdf_files = find_pdf_files(test_inputs_dir)
        if not pdf_files:
            logger.error("No PDF files found in test inputs directory. Please add a PDF or specify a path.")
            print("\n❌ FAILED: No PDF files found in data/test_inputs/pdf to test.")
            return False
        
        pdf_path = pdf_files[0]
        logger.info(f"Found PDF file: {pdf_path}")
    
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file does not exist: {pdf_path}")
        print(f"\n❌ FAILED: PDF file does not exist: {pdf_path}")
        return False
    
    try:
        # Process the PDF
        logger.info(f"Processing PDF: {pdf_path}")
        
        # Create PDF processor
        processor = PDFProcessor(output_dir=str(output_dir))
        
        # Process the PDF
        result = processor.process_pdf(pdf_path)
        
        # Create raw data package
        raw_data = processor.create_raw_data_package(result)
        
        # Display results
        print(f"\n✅ SUCCESS: PDF processor test passed!")
        print(f"Processed PDF: {pdf_path}")
        print(f"Output directory: {output_dir}")
        print(f"Extracted {len(result['pages'])} pages and {len(result['images'])} images")
        print(f"Raw text saved to: {raw_data['raw_text_file']}")
        print(f"Images saved to: {raw_data['images_directory']}")
        
        # Print a sample of the extracted text (first 200 characters)
        text_sample = raw_data["raw_text"][:200] + "..." if len(raw_data["raw_text"]) > 200 else raw_data["raw_text"]
        print(f"\nRaw Text Sample:\n{text_sample}")
        
        # Print image information
        print(f"\nExtracted Images:")
        for i, img in enumerate(raw_data["images"][:5]):  # Show only first 5 images
            print(f"  {i+1}. {img['filename']} ({img['width']}x{img['height']})")
        
        if len(raw_data["images"]) > 5:
            print(f"  ... and {len(raw_data['images']) - 5} more images")
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        
        print("\n❌ FAILED: PDF processor test failed!")
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    import sys
    
    # Check if a PDF path was provided as a command-line argument
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    # Run the test
    success = run_test(pdf_path)
    sys.exit(0 if success else 1)
