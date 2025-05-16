"""
PDF to Task Graph Integration Module

This module integrates the PDF processing functionality with task graph generation,
using Pydantic models for validation and standardization. It provides:

1. Functions to extract data from PDF attachments
2. Convert PDF content to structured bug reports
3. Generate task graphs from extracted bug data
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

# Add the project root to the path to allow importing from modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, project_root)

# Import from the core module structure
from core.ingestion.pdf_processor import PDFProcessor, process_bug_report
from core.generation.working_task_graph_generator import TaskGraphGenerator
from core.models.task_graph_schema import (
    BugReport, TaskGraph, Attachment, AttachmentContent, AttachmentType
)


class PDFToTaskGraphProcessor:
    """
    Class to process PDFs and generate task graphs using the structured Pydantic models.
    """
    
    def __init__(
        self,
        output_dir: Optional[str] = None,
        model_name: str = "gemini-2.5-flash-preview-04-17",
        log_level: int = logging.INFO,
        ocr_enabled: bool = True
    ):
        """
        Initialize the PDF to Task Graph processor.
        
        Args:
            output_dir: Directory to save extracted artifacts and generated task graphs
            model_name: Name of the LLM model to use for task graph generation
            log_level: Logging level
            ocr_enabled: Whether to use OCR to extract text from images
        """
        self.log_level = log_level
        
        # Set up logging
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger("pdf_to_task_graph")
        
        # Create output directories
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path("output")
        
        self.pdf_artifacts_dir = self.output_dir / "pdf_artifacts"
        self.task_graphs_dir = self.output_dir / "task_graphs"
        
        # Create directories if they don't exist
        self.pdf_artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.task_graphs_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize PDF processor
        self.pdf_processor = PDFProcessor(
            output_dir=str(self.pdf_artifacts_dir),
            log_level=log_level,
            ocr_enabled=ocr_enabled
        )
        
        # Initialize task graph generator
        self.task_graph_generator = TaskGraphGenerator(
            model_name=model_name,
            output_dir=str(self.task_graphs_dir),
            log_level=log_level
        )
        
        self.logger.info(f"PDF to Task Graph processor initialized with model: {model_name}")
    
    def process_pdf_attachments(self, bug_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process PDF attachments in bug data.
        
        Args:
            bug_data: Dictionary containing bug data with attachments
            
        Returns:
            Updated bug data with processed PDFs
        """
        if "attachments" not in bug_data:
            self.logger.warning("No attachments found in bug data")
            return bug_data
        
        for i, attachment in enumerate(bug_data["attachments"]):
            if "type" in attachment and attachment["type"].lower() == "pdf":
                pdf_path = attachment.get("content", {}).get("file_path")
                
                if not pdf_path or not os.path.exists(pdf_path):
                    self.logger.warning(f"PDF attachment '{attachment.get('name', 'unknown')}' has invalid path: {pdf_path}")
                    continue
                
                self.logger.info(f"Processing PDF attachment: {attachment.get('name', 'unknown')}")
                
                try:
                    # Process the PDF
                    result = self.pdf_processor.process_pdf(pdf_path)
                    
                    # Update the attachment content
                    bug_data["attachments"][i]["content"] = {
                        "raw_text": result["raw_text"],
                        "images": result["images"],
                        "file_path": pdf_path
                    }
                    
                    self.logger.info(f"Successfully processed PDF attachment: {attachment.get('name', 'unknown')}")
                    
                except Exception as e:
                    self.logger.error(f"Error processing PDF attachment '{attachment.get('name', 'unknown')}': {str(e)}")
        
        return bug_data
    
    def convert_to_pydantic_bug_report(self, bug_data: Dict[str, Any]) -> BugReport:
        """
        Convert bug data to a structured BugReport Pydantic model.
        
        Args:
            bug_data: Dictionary containing bug data
            
        Returns:
            BugReport Pydantic model
        """
        # Extract bug metadata
        bug_id = bug_data.get("bug_metadata", {}).get("bug_id", "unknown")
        title = bug_data.get("bug_metadata", {}).get("bug_title", "Unknown Bug")
        
        # Extract bug content
        bug_content = bug_data.get("bug_content", {})
        description = bug_content.get("description", "")
        steps_to_reproduce = bug_content.get("steps_to_reproduce", "")
        expected_outcome = bug_content.get("expected_outcome", "")
        additional_info = bug_content.get("additional_info", "")
        
        # Process attachments
        attachments = []
        raw_text = ""
        
        for attachment_data in bug_data.get("attachments", []):
            # Determine attachment type
            attachment_type = attachment_data.get("type", "").lower()
            if attachment_type not in [e.value for e in AttachmentType]:
                # Skip unsupported attachment types
                continue
            
            # Create attachment content if available
            content_data = attachment_data.get("content", {})
            content = None
            if content_data:
                content = AttachmentContent(
                    raw_text=content_data.get("raw_text", ""),
                    images=content_data.get("images", []),
                    file_path=content_data.get("file_path")
                )
                
                # Add attachment text to raw text
                if content.raw_text:
                    raw_text += f"\n\n=== ATTACHMENT: {attachment_data.get('name', 'unknown')} ===\n\n"
                    raw_text += content.raw_text
            
            # Create attachment
            attachment = Attachment(
                id=attachment_data.get("id", f"unknown_{len(attachments)}"),
                name=attachment_data.get("name", "unknown"),
                type=attachment_type,
                uploaded_by=attachment_data.get("uploaded_by"),
                uploaded_at=attachment_data.get("uploaded_at"),
                description=attachment_data.get("description"),
                content=content,
                confidentiality=attachment_data.get("confidentiality")
            )
            
            attachments.append(attachment)
        
        # Create comments text if available
        if "comments" in bug_data:
            raw_text += "\n\n=== COMMENTS ===\n\n"
            for comment in bug_data["comments"]:
                author = comment.get("author", {}).get("id", "unknown")
                role = comment.get("author", {}).get("role", "")
                timestamp = comment.get("timestamp", "")
                content = comment.get("content", "")
                
                raw_text += f"[{timestamp}] {author} ({role}):\n{content}\n\n"
        
        # Create bug report model
        bug_report = BugReport(
            bug_id=bug_id,
            title=title,
            description=description,
            steps_to_reproduce=steps_to_reproduce,
            expected_outcome=expected_outcome,
            additional_info=additional_info,
            attachments=attachments,
            raw_text=raw_text
        )
        
        return bug_report
    
    def process_bug_data(self, bug_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process bug data to generate a task graph.
        
        Args:
            bug_data: Dictionary containing bug data
            
        Returns:
            Dictionary with the bug report and generated task graph
        """
        # Process PDF attachments
        self.logger.info("Processing PDF attachments...")
        bug_data = self.process_pdf_attachments(bug_data)
        
        # Convert to Pydantic model
        self.logger.info("Converting to structured bug report...")
        bug_report = self.convert_to_pydantic_bug_report(bug_data)
        
        # Save the bug report
        bug_report_path = self.output_dir / f"{bug_report.bug_id}_bug_report.json"
        with open(bug_report_path, "w") as f:
            f.write(bug_report.json(indent=2))
        
        self.logger.info(f"Saved bug report to: {bug_report_path}")
        
        # Generate task graph
        self.logger.info("Generating task graph...")
        task_graph_dict = self.task_graph_generator.generate_task_graph(bug_data)
        
        try:
            # Convert to Pydantic model for validation
            # Use TaskGraph.parse_obj if the object is already a dictionary
            task_graph = TaskGraph.parse_obj(task_graph_dict)
            
            # Save validated task graph
            task_graph_path = self.task_graphs_dir / f"{bug_report.bug_id}_task_graph_validated.json"
            with open(task_graph_path, "w") as f:
                f.write(task_graph.json(indent=2))
            
            self.logger.info(f"Saved validated task graph to: {task_graph_path}")
            
            # Update the bug report with the task graph
            bug_report.task_graph = task_graph
            
            # Save the updated bug report
            with open(bug_report_path, "w") as f:
                f.write(bug_report.json(indent=2))
            
            self.logger.info(f"Updated bug report with task graph: {bug_report_path}")
            
            return {
                "bug_report": bug_report.dict(),
                "task_graph": task_graph.dict(),
                "status": "success"
            }
            
        except Exception as e:
            self.logger.error(f"Error validating task graph: {str(e)}")
            
            return {
                "bug_report": bug_report.dict(),
                "task_graph": task_graph_dict,
                "status": "error",
                "error": str(e)
            }


def process_bug_data_to_task_graph(
    bug_data_path: str,
    output_dir: Optional[str] = None,
    model_name: str = "gemini-2.5-flash-preview-04-17",
    log_level: int = logging.INFO
) -> Dict[str, Any]:
    """
    Process bug data from a JSON file to generate a task graph.
    
    Args:
        bug_data_path: Path to the JSON file containing bug data
        output_dir: Directory to save extracted artifacts and generated task graphs
        model_name: Name of the LLM model to use for task graph generation
        log_level: Logging level
        
    Returns:
        Dictionary with the bug report and generated task graph
    """
    logger = logging.getLogger("pdf_to_task_graph")
    
    # Load bug data
    try:
        with open(bug_data_path, "r") as f:
            bug_data = json.load(f)
    except Exception as e:
        logger.error(f"Error loading bug data from {bug_data_path}: {str(e)}")
        return {
            "status": "error",
            "error": f"Error loading bug data: {str(e)}"
        }
    
    # Process bug data
    processor = PDFToTaskGraphProcessor(
        output_dir=output_dir,
        model_name=model_name,
        log_level=log_level
    )
    
    return processor.process_bug_data(bug_data)
