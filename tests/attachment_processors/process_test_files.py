#!/usr/bin/env python3
"""
Script to process the test files using our enhanced attachment processors.
This script uses the core processing functions directly to avoid any model validation issues.
"""

import os
import sys
import json
import logging
import shutil
from pathlib import Path
from datetime import datetime

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import processors
from core.ingestion.text_processor import process_text_file
from core.ingestion.image_processor import process_image_file
from core.ingestion.pdf_processor import process_pdf_file

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('test_processor')

def main():
    # Define paths
    test_dir = Path("/Users/rohankatakam/Documents/cu/tests/step_6_test")
    output_dir = Path("/Users/rohankatakam/Documents/cu/tests/step_6_output")
    
    # Create output dir if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Clean previous output if exists
    if os.path.exists(output_dir):
        for item in os.listdir(output_dir):
            item_path = os.path.join(output_dir, item)
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            else:
                os.remove(item_path)
    
    # Create subdirectories for organization
    os.makedirs(output_dir / "text", exist_ok=True)
    os.makedirs(output_dir / "images", exist_ok=True)
    os.makedirs(output_dir / "pdfs", exist_ok=True)
    
    # Process all files in test directory
    results = []
    
    for file_path in test_dir.glob('*'):
        if not file_path.is_file():
            continue
            
        test_id = f"TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        file_ext = file_path.suffix.lower()
        
        try:
            logger.info(f"Processing {file_path.name}")
            result = {"file": file_path.name, "test_id": test_id}
            
            # Process based on file type
            if file_ext == '.txt':
                text_content, _ = process_text_file(
                    str(file_path), 
                    output_dir=str(output_dir / "text"),
                    store_in_db=True,
                    attachment_id=test_id
                )
                result["processor"] = "text"
                result["content_id"] = text_content.text_id
                result["metadata"] = {
                    "word_count": text_content.metadata.get("word_count"),
                    "line_count": text_content.metadata.get("line_count"),
                    "language": text_content.language
                }
                
            elif file_ext in ['.png', '.jpg', '.jpeg']:
                image_content, text_content = process_image_file(
                    str(file_path),
                    output_dir=str(output_dir / "images"),
                    perform_ocr_flag=True,
                    store_in_db=True,
                    attachment_id=test_id
                )
                result["processor"] = "image"
                result["content_id"] = image_content.image_id
                result["metadata"] = {
                    "width": image_content.metadata.width,
                    "height": image_content.metadata.height,
                    "format": image_content.metadata.format,
                    "has_ocr": text_content is not None
                }
                if text_content:
                    result["ocr_text_id"] = text_content.text_id
                    result["ocr_confidence"] = image_content.ocr_confidence
                
            elif file_ext == '.pdf':
                pdf_result = process_pdf_file(
                    str(file_path),
                    output_dir=str(output_dir / "pdfs"),
                    store_in_db=True,
                    attachment_id=test_id
                )
                result["processor"] = "pdf"
                result["content_id"] = pdf_result.get("pdf_content").pdf_id
                result["metadata"] = {
                    "page_count": pdf_result.get("pdf_content").page_count,
                    "title": pdf_result.get("pdf_content").title,
                    "text_content_count": len(pdf_result.get("text_contents", [])),
                    "image_content_count": len(pdf_result.get("image_contents", []))
                }
                # Add IDs of extracted content
                result["extracted_text_ids"] = [t.text_id for t in pdf_result.get("text_contents", [])]
                result["extracted_image_ids"] = [i.image_id for i in pdf_result.get("image_contents", [])]
            
            logger.info(f"Successfully processed {file_path.name}")
            results.append(result)
            
        except Exception as e:
            logger.error(f"Error processing {file_path.name}: {str(e)}")
            results.append({
                "file": file_path.name,
                "error": str(e)
            })
    
    # Save results to JSON
    result_file = output_dir / "processing_results.json"
    with open(result_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Processing complete. Results saved to {result_file}")
    
    # Print summary
    print("\nProcessing Summary:")
    for result in results:
        if "error" in result:
            status = f"ERROR: {result['error']}"
        else:
            status = f"SUCCESS - {result['processor']} processor"
        
        print(f"- {result['file']}: {status}")
    
    print(f"\nAll processed files can be found in: {output_dir}")
    print(f"Detailed results saved to: {result_file}")

if __name__ == "__main__":
    main()
