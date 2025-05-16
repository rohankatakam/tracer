#!/usr/bin/env python3
"""
PDF to Task Graph Pipeline Runner

This script runs the entire pipeline from PDF bug report to task graph generation:
1. Processes PDF attachments to extract text and images
2. Converts extracted data to a structured bug report using Pydantic models
3. Generates a task graph using the working Gemini model implementation
4. Validates the task graph against the schema

This script is designed to work with both:
- Bug data JSON files that already have PDF attachment references
- Direct PDF files that need to be processed
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

# Add the project root to the path to allow importing from modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

from core.ingestion.pdf_to_task_graph import PDFToTaskGraphProcessor, process_bug_data_to_task_graph
from core.ingestion.pdf_processor import process_bug_report


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Process a PDF bug report or bug data JSON to generate a task graph"
    )
    
    # Input options
    input_group = parser.add_argument_group("Input Options")
    input_group.add_argument(
        "--bug-data", "-b",
        help="Path to the bug data JSON file (containing attachments with PDF paths)"
    )
    input_group.add_argument(
        "--pdf", "-p",
        help="Path to a PDF file to process directly (will create a simple bug data structure)"
    )
    
    # Output options
    parser.add_argument(
        "--output-dir", "-o",
        default=os.path.join("output"),
        help="Directory to save extracted artifacts and generated task graphs"
    )
    
    # Model options
    parser.add_argument(
        "--model", "-m",
        default="gemini-2.5-flash-preview-04-17",
        help="Gemini model to use for task graph generation"
    )
    
    # Logging options
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    # Processing options
    parser.add_argument(
        "--disable-ocr",
        action="store_true",
        help="Disable OCR for image text extraction"
    )
    
    args = parser.parse_args()
    
    # Validate that at least one input is provided
    if not args.bug_data and not args.pdf:
        parser.error("Either --bug-data or --pdf must be provided")
    
    return args


def process_pdf_directly(pdf_path: str, output_dir: str, model_name: str, log_level: int, ocr_enabled: bool) -> Dict[str, Any]:
    """
    Process a PDF file directly to generate a task graph.
    
    Args:
        pdf_path: Path to the PDF file
        output_dir: Directory to save extracted artifacts and generated task graphs
        model_name: Gemini model to use for task graph generation
        log_level: Logging level
        ocr_enabled: Whether to use OCR for image text extraction
        
    Returns:
        Dictionary with the results
    """
    logger = logging.getLogger("pdf_to_task_graph_runner")
    logger.info(f"Processing PDF directly: {pdf_path}")
    
    # Process the PDF to extract raw content
    pdf_result = process_bug_report(pdf_path, output_dir)
    raw_data_package = pdf_result["raw_data_package"]
    
    # Create a minimal bug data structure from the PDF result
    pdf_filename = os.path.basename(pdf_path)
    bug_id = os.path.splitext(pdf_filename)[0].replace(" ", "_").lower()
    
    bug_data = {
        "bug_metadata": {
            "bug_id": bug_id,
            "bug_title": f"Bug extracted from {pdf_filename}"
        },
        "bug_content": {
            "description": f"Content extracted from {pdf_filename}",
            "steps_to_reproduce": "See attached PDF",
            "expected_outcome": "Proper functionality",
            "additional_info": "Automatically processed from PDF"
        },
        "attachments": [
            {
                "id": f"pdf_{bug_id}",
                "name": pdf_filename,
                "type": "pdf",
                "uploaded_by": "system",
                "description": f"Original PDF file: {pdf_filename}",
                "content": {
                    "raw_text": raw_data_package["raw_text"],
                    "images": raw_data_package["images"],
                    "file_path": pdf_path
                }
            }
        ]
    }
    
    # Save the constructed bug data to a file
    bug_data_path = os.path.join(output_dir, f"{bug_id}_bug_data.json")
    with open(bug_data_path, "w") as f:
        json.dump(bug_data, f, indent=2)
    
    logger.info(f"Created bug data file: {bug_data_path}")
    
    # Now process the bug data to generate a task graph
    processor = PDFToTaskGraphProcessor(
        output_dir=output_dir,
        model_name=model_name,
        log_level=log_level,
        ocr_enabled=ocr_enabled
    )
    
    return processor.process_bug_data(bug_data)


def main():
    """Main entry point for the script."""
    args = parse_args()
    
    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger("pdf_to_task_graph_runner")
    
    # Create the output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Process based on input type
    if args.pdf:
        result = process_pdf_directly(
            pdf_path=args.pdf,
            output_dir=str(output_dir),
            model_name=args.model,
            log_level=log_level,
            ocr_enabled=not args.disable_ocr
        )
    elif args.bug_data:
        result = process_bug_data_to_task_graph(
            bug_data_path=args.bug_data,
            output_dir=str(output_dir),
            model_name=args.model,
            log_level=log_level
        )
    
    # Check the result status
    if result.get("status") == "success":
        logger.info("Successfully generated a task graph!")
        logger.info(f"Bug Report ID: {result.get('bug_report', {}).get('bug_id')}")
        logger.info(f"Task Graph Name: {result.get('task_graph', {}).get('name')}")
        
        # Print paths to generated files
        bug_id = result.get('bug_report', {}).get('bug_id', 'unknown')
        bug_report_path = output_dir / f"{bug_id}_bug_report.json"
        task_graph_path = output_dir / "task_graphs" / f"{bug_id}_task_graph_validated.json"
        
        logger.info(f"Bug Report: {bug_report_path}")
        logger.info(f"Task Graph: {task_graph_path}")
        
        return 0
    else:
        logger.error(f"Failed to generate task graph: {result.get('error', 'Unknown error')}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
