#!/usr/bin/env python3
"""
Test script for PDF processor only - isolated to debug issues
"""

import os
import sys
import logging
import uuid
from pathlib import Path

# Add project root to the path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from core.ingestion.pdf_processor import PDFProcessor

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("pdf_test")

def test_pdf_processor():
    # Define paths
    test_dir = Path("/Users/rohankatakam/Documents/cu/tests/step_6_test")
    output_dir = Path("/Users/rohankatakam/Documents/cu/tests/step_6_output/pdf_debug")
    os.makedirs(output_dir, exist_ok=True)
    
    # Create PDF processor
    pdf_processor = PDFProcessor(output_dir=str(output_dir))
    
    # Process PDF files
    for pdf_file in test_dir.glob("*.pdf"):
        logger.info(f"Processing PDF: {pdf_file.name}")
        try:
            # Direct processing without going through attachment pipeline
            result = pdf_processor.process_pdf(str(pdf_file))
            logger.info(f"Successfully processed {pdf_file.name}")
            logger.info(f"  - Pages: {result['metadata']['pages']}")
            logger.info(f"  - Title: {result['metadata']['title']}")
            
            # Create raw data package
            raw_package = pdf_processor.create_raw_data_package(result, name=pdf_file.stem)
            logger.info(f"Created raw data package for {pdf_file.name}")
            
        except Exception as e:
            logger.error(f"Failed to process {pdf_file.name}: {str(e)}", exc_info=True)
    
    logger.info(f"All PDF processing complete. Check results in {output_dir}")

if __name__ == "__main__":
    test_pdf_processor()
