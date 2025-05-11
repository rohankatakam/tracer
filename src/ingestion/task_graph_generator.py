"""
Task Graph Generator

This module provides functionality to generate task graphs from raw bug report data
extracted by the PDF processor. It uses Google's Gemini 2.5 Pro to intelligently interpret
the raw text and images, structuring them into actionable reproduction steps.

This is part of Phase 1.3B: Task Graph Generation.
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

from google import genai
from google.genai import types

from src.utils.logging_utils import setup_logging
from src.utils.json_utils import save_json, load_json


class TaskGraphGenerator:
    """Class for generating task graphs from raw PDF extraction data using Gemini."""
    
    def __init__(self, model_name: str = "gemini-2.5-pro-exp-03-25", 
                 output_dir: Optional[str] = None, 
                 log_level: int = logging.INFO):
        """Initialize the Task Graph Generator.
        
        Args:
            model_name: Gemini model to use
            output_dir: Directory to save generated task graphs
            log_level: Logging level
        """
        self.model_name = model_name
        self.log_level = log_level
        
        # Set up enhanced logging
        log_dir = 'logs/task_graph_generator'
        os.makedirs(log_dir, exist_ok=True)
        self.logger = setup_logging("task_graph_generator", log_dir, log_level)
        
        # Set up output directory
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path("data/task_graphs")
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Gemini client
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        # Initialize the client
        self.client = genai.Client(api_key=api_key)
        
        # System prompt template - will be completed with specifics during generation
        self.system_prompt_template = """
You are an AI bug analysis specialist tasked with creating detailed bug reproduction task graphs.
Your job is to analyze bug reports (text and images) and generate structured, actionable reproduction steps that a computer agent could follow to reproduce the bug, including references to relevant screenshots.  

IMPORTANT GUIDELINES:
1. Create a structured task graph with sequential steps for reproducing the bug
2. Each step must be highly detailed and actionable for a computer agent to follow
3. Reference specific screenshots to provide visual context for each step (e.g., "See page_2_img_1.jpeg for the location of the button")
4. Include precise inputs, UI element interactions, and expected results for each step
5. Steps should be specific enough that a computer agent could automate the reproduction process

CONTEXT ABOUT THE DATA:
- Raw text is marked with page numbers ("== PAGE 1 ==") 
- Images are named with page and sequence numbers (e.g., "page_2_img_1.jpeg")
- OCR text from images is marked with "--- OCR from [image filename] ---"
- All screenshot filenames should be referenced exactly as they appear in the data

OUTPUT FORMAT - YOU MUST USE THIS EXACT STRUCTURE:
{
  "name": "bug_[identifier]",
  "description": "[Concise description of the bug]",
  "environment": {
    "application": "[Application name and version]",
    "browser": "[Browser name and version if applicable]",
    "operating_system": "[OS name and version if applicable]"
  },
  "task_graph": {
    "nodes": [
      {
        "id": "1",
        "type": "action",
        "content": "[DETAILED step description, e.g., 'Click the Login button in the top-right corner of the screen']",
        "metadata": {
          "image_refs": ["page_2_img_1.jpeg"],  // List of referenced screenshots for this step
          "ui_elements": ["Login button"],      // UI elements to interact with
          "inputs": ["username=admin"],        // Any input values to enter
          "expected_result": "Login form appears" // What should happen after this step
        }
      }
    ],
    "edges": [
      {
        "source": "1",
        "target": "2"
      }
    ]
  },
  "verification_steps": [
    "Step 1: [How to verify the bug is present]"
  ],
  "confidence_score": 0.85,  // Your confidence in these reproduction steps
  "missing_information": ["Any critical information missing from the report"] 
}

Remember: You MUST include detailed screenshot references in each step to guide the agent on what to look for and where to interact.
"""
        
        self.logger.info(f"TaskGraphGenerator initialized with model: {self.model_name}")

    def generate_task_graph(self, bug_data_package: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a task graph from comprehensive bug data.
        
        Args:
            bug_data_package: The bug data package containing metadata, content, and attachments
            
        Returns:
            Dict containing the generated task graph
        """
        # Check if this is the old raw_data_package format or the new enhanced schema
        if 'bug_metadata' not in bug_data_package and 'raw_text' in bug_data_package:
            # This is the old schema - handle it with backward compatibility
            return self._generate_task_graph_legacy(bug_data_package)
        
        # This is the new enhanced schema - process it accordingly
        self.logger.info(f"Generating task graph for: {bug_data_package.get('bug_metadata', {}).get('bug_id', 'unknown')}")
        
        # Create a temporary directory for processing attachments if needed
        output_dir = self.output_dir / "temp_processing"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Process any attachments
        processed_attachments = []
        if 'attachments' in bug_data_package and bug_data_package['attachments']:
            for attachment in bug_data_package['attachments']:
                # Check file_path exists
                file_path = attachment.get('content', {}).get('file_path', '')
                if file_path and Path(file_path).exists():
                    # Process the attachment based on its type
                    if attachment['type'] == 'pdf':
                        # Create a directory for this attachment
                        attachment_dir = output_dir / f"attachment_{attachment['id']}"
                        attachment_dir.mkdir(parents=True, exist_ok=True)
                        
                        # Process the PDF using PDFProcessor with the attachment directory as output
                        from src.ingestion.pdf_processor import PDFProcessor
                        pdf_processor = PDFProcessor(output_dir=str(attachment_dir))
                        pdf_data = pdf_processor.process_pdf(file_path)
                        
                        # Update the attachment with the processed data
                        attachment['content']['raw_text'] = pdf_data.get('raw_text', '')
                        attachment['content']['images'] = pdf_data.get('images', [])
                        attachment['content']['processed_dir'] = str(attachment_dir)
                        
                        processed_attachments.append(attachment)
                    elif attachment['type'] in ['image', 'jpg', 'jpeg', 'png']:
                        # Create a directory for this image attachment
                        attachment_dir = output_dir / f"attachment_{attachment['id']}"
                        attachment_dir.mkdir(parents=True, exist_ok=True)
                        
                        # Copy the image to the processing directory
                        import shutil
                        dest_path = attachment_dir / Path(file_path).name
                        shutil.copy2(file_path, dest_path)
                        
                        # Update the attachment with the path info
                        attachment['content']['processed_dir'] = str(attachment_dir)
                        attachment['content']['processed_path'] = str(dest_path)
                        
                        processed_attachments.append(attachment)
        
        # Build a comprehensive prompt that includes all bug data
        user_prompt = self._build_enhanced_prompt(bug_data_package, processed_attachments)
        
        # Generate the task graph
        task_graph = self._call_gemini_api(user_prompt, bug_data_package)
        
        # Save the task graph to a file
        if self.output_dir:
            bug_id = bug_data_package.get('bug_metadata', {}).get('bug_id', 'unknown')
            output_path = self.output_dir / f"{bug_id}_task_graph.json"
            save_json(task_graph, str(output_path), pretty=True)
            self.logger.info(f"Saved task graph to: {output_path}")
        
        return task_graph
    
    def _generate_task_graph_legacy(self, raw_data_package: Dict[str, Any]) -> Dict[str, Any]:
        """Legacy method to generate a task graph from raw PDF extraction data.
        
        Args:
            raw_data_package: The raw data package from the PDF processor
            
        Returns:
            Dict containing the generated task graph
        """
        self.logger.info(f"Generating task graph using legacy method for: {raw_data_package.get('name', 'unknown')}")
        
        # Extract the relevant content from the raw data package
        raw_text = raw_data_package.get('raw_text', '')
        images = raw_data_package.get('images', [])
        
        # Build the full prompt with text and image references
        user_prompt = self._build_gemini_prompt(raw_text, raw_data_package)
        
        # Add image references as text
        if images:
            image_references = self._prepare_image_references(images, raw_data_package.get('images_directory', ''))
            user_prompt += image_references
        
        # Generate the task graph
        task_graph = self._call_gemini_api(user_prompt, raw_data_package)
        
        # Save the task graph to a file
        if self.output_dir:
            task_graph_name = raw_data_package.get('name', 'unknown')
            output_path = self.output_dir / f"{task_graph_name}_task_graph.json"
            save_json(task_graph, str(output_path), pretty=True)
            self.logger.info(f"Saved task graph to: {output_path}")
        
        return task_graph
        
    def _build_enhanced_prompt(self, bug_data_package: Dict[str, Any], processed_attachments: List[Dict[str, Any]]) -> str:
        """Build a comprehensive prompt from the enhanced bug data package.
        
        Args:
            bug_data_package: The enhanced bug data package with metadata, content, etc.
            processed_attachments: List of processed attachments with extracted content
            
        Returns:
            A comprehensive prompt string for the Gemini API
        """
        prompt_parts = []
        
        # Add bug metadata
        if 'bug_metadata' in bug_data_package:
            metadata = bug_data_package['bug_metadata']
            prompt_parts.append(f"BUG ID: {metadata.get('bug_id', 'Unknown')}")
            prompt_parts.append(f"TITLE: {metadata.get('bug_title', 'Unknown')}")
            prompt_parts.append(f"SEVERITY: {metadata.get('severity', {}).get('description', 'Unknown')}")
            prompt_parts.append(f"PRODUCT: {metadata.get('product', {}).get('name', 'Unknown')} {metadata.get('product', {}).get('version', {}).get('reported', 'Unknown')}")
            prompt_parts.append(f"CUSTOMER: {metadata.get('customer', {}).get('name', 'Unknown')}")
            prompt_parts.append(f"ENVIRONMENT: {metadata.get('customer', {}).get('environment', 'Unknown')}")
        
        # Add bug content
        if 'bug_content' in bug_data_package:
            content = bug_data_package['bug_content']
            if 'description' in content:
                prompt_parts.append(f"\nDESCRIPTION:\n{content['description']}")
            if 'steps_to_reproduce' in content:
                prompt_parts.append(f"\nSTEPS TO REPRODUCE:\n{content['steps_to_reproduce']}")
            if 'expected_outcome' in content:
                prompt_parts.append(f"\nEXPECTED OUTCOME:\n{content['expected_outcome']}")
            if 'additional_info' in content:
                prompt_parts.append(f"\nADDITIONAL INFO:\n{content['additional_info']}")
        
        # Add comments if available
        if 'comments' in bug_data_package and bug_data_package['comments']:
            prompt_parts.append("\nCOMMENTS:")
            for comment in bug_data_package['comments']:
                prompt_parts.append(f"Comment by {comment.get('author', 'Unknown')} on {comment.get('date', 'Unknown')}:\n{comment.get('content', '')}\n")
        
        # Add processed attachment content
        if processed_attachments:
            prompt_parts.append("\nATTACHMENT CONTENT:")
            for attachment in processed_attachments:
                attachment_name = attachment.get('name', 'Unknown attachment')
                attachment_type = attachment.get('type', 'unknown')
                
                prompt_parts.append(f"\nAttachment: {attachment_name} (Type: {attachment_type})")
                
                # Add extracted text from attachments if available
                if 'content' in attachment and 'raw_text' in attachment['content'] and attachment['content']['raw_text']:
                    # Truncate very long raw text to avoid exceeding token limits
                    raw_text = attachment['content']['raw_text']
                    if len(raw_text) > 5000:  # Arbitrary limit to avoid extremely long prompts
                        raw_text = raw_text[:5000] + "... [text truncated due to length]"
                    prompt_parts.append(f"Extracted text:\n{raw_text}")
                
                # Add image references if available
                if 'content' in attachment and 'images' in attachment['content'] and attachment['content']['images']:
                    images = attachment['content']['images']
                    prompt_parts.append(f"Contains {len(images)} images/screenshots that can be referenced in the task graph.")
                    for i, image in enumerate(images[:10]):  # Limit to first 10 images to avoid extremely long prompts
                        image_path = image.get('path', '')
                        if image_path:
                            image_name = Path(image_path).name
                            prompt_parts.append(f"Image {i+1}: {image_name}")
        
        # Combine all parts into a single prompt
        return "\n".join(prompt_parts)

    def _prepare_image_references(self, images: List[Dict[str, Any]], images_directory: str) -> str:
        """Prepare image references as text for inclusion in the prompt.
        
        For the initial implementation, we'll include image references as text only.
        Future enhancements will include actual image files in the prompt.
        
        Args:
            images: List of image metadata from the raw data package
            images_directory: Directory containing the images
            
        Returns:
            Text describing the images for inclusion in the prompt
        """
        image_references = "\n\nIMAGE REFERENCES:\n"
        
        for i, image in enumerate(images):
            filename = image.get('filename', f'image_{i}')
            page = image.get('page', 0)
            width = image.get('width', 0)
            height = image.get('height', 0)
            
            image_references += f"Image {i+1}: {filename} (Page {page}, {width}x{height})\n"
        
        self.logger.info(f"Prepared text references for {len(images)} images")
        return image_references

    def _build_gemini_prompt(self, raw_text: str, raw_data_package: Dict[str, Any]) -> str:
        """Build the user prompt for Gemini.
        
        Args:
            raw_text: The raw text from the PDF
            raw_data_package: The complete raw data package
            
        Returns:
            Formatted prompt string
        """
        # Extract metadata from the raw data package
        bug_name = raw_data_package.get('name', 'unknown')
        filename = raw_data_package.get('source_file', '').split('/')[-1] if raw_data_package.get('source_file') else 'unknown'
        total_pages = raw_data_package.get('total_pages', 0)
        total_images = raw_data_package.get('total_images', 0)
        
        # Build a prompt with context about the document
        prompt = f"""
Bug Report Analysis Request:
---------------------------
File: {filename}
Pages: {total_pages}
Images: {total_images}

TASK:
Analyze the following bug report and generate a structured task graph containing all steps needed to reproduce the bug.
Focus on extracting clear, sequential steps with specific inputs, UI elements, and expected behaviors.

The report contains both text content and images. The text includes OCR extracted from images, marked by "--- OCR from [filename] ---".
Reference relevant images in your output using their filenames.

RAW TEXT CONTENT:
----------------
{raw_text[:50000] if len(raw_text) > 50000 else raw_text}

Please generate a complete task graph following the OUTPUT FORMAT provided in the system instructions.
"""
        return prompt

    def _call_gemini_api(self, user_prompt: str, raw_data_package: Dict[str, Any]) -> Dict[str, Any]:
        """Call the Gemini API to generate a task graph using text-only input with structured output.
        
        Args:
            user_prompt: The complete user prompt with text and image references
            raw_data_package: The complete raw data package
            
        Returns:
            Generated task graph following our schema
        """
        # Log prompt length metrics
        self.logger.info(f"User prompt length: {len(user_prompt)} characters")
        
        try:
            # Use the model specified in the constructor
            model = self.model_name
            
            # Prepare the content with the text prompt
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=user_prompt),
                    ],
                ),
            ]
            
            # Define the expected schema for structured output
            # This matches the format specified in our system prompt
            task_graph_schema = genai.types.Schema(
                type=genai.types.Type.OBJECT,
                properties={
                    "name": genai.types.Schema(type=genai.types.Type.STRING),
                    "description": genai.types.Schema(type=genai.types.Type.STRING),
                    "environment": genai.types.Schema(
                        type=genai.types.Type.OBJECT,
                        properties={
                            "application": genai.types.Schema(type=genai.types.Type.STRING),
                            "browser": genai.types.Schema(type=genai.types.Type.STRING),
                            "operating_system": genai.types.Schema(type=genai.types.Type.STRING)
                        }
                    ),
                    "task_graph": genai.types.Schema(
                        type=genai.types.Type.OBJECT,
                        properties={
                            "nodes": genai.types.Schema(
                                type=genai.types.Type.ARRAY,
                                items=genai.types.Schema(
                                    type=genai.types.Type.OBJECT,
                                    properties={
                                        "id": genai.types.Schema(type=genai.types.Type.STRING),
                                        "type": genai.types.Schema(type=genai.types.Type.STRING),
                                        "content": genai.types.Schema(type=genai.types.Type.STRING),
                                        "metadata": genai.types.Schema(
                                            type=genai.types.Type.OBJECT,
                                            properties={
                                                "image_refs": genai.types.Schema(
                                                    type=genai.types.Type.ARRAY,
                                                    items=genai.types.Schema(type=genai.types.Type.STRING)
                                                ),
                                                "ui_elements": genai.types.Schema(
                                                    type=genai.types.Type.ARRAY,
                                                    items=genai.types.Schema(type=genai.types.Type.STRING)
                                                ),
                                                "inputs": genai.types.Schema(
                                                    type=genai.types.Type.ARRAY,
                                                    items=genai.types.Schema(type=genai.types.Type.STRING)
                                                ),
                                                "expected_result": genai.types.Schema(type=genai.types.Type.STRING)
                                            }
                                        )
                                    }
                                )
                            ),
                            "edges": genai.types.Schema(
                                type=genai.types.Type.ARRAY,
                                items=genai.types.Schema(
                                    type=genai.types.Type.OBJECT,
                                    properties={
                                        "source": genai.types.Schema(type=genai.types.Type.STRING),
                                        "target": genai.types.Schema(type=genai.types.Type.STRING)
                                    }
                                )
                            )
                        }
                    ),
                    "verification_steps": genai.types.Schema(
                        type=genai.types.Type.ARRAY,
                        items=genai.types.Schema(type=genai.types.Type.STRING)
                    ),
                    "confidence_score": genai.types.Schema(type=genai.types.Type.NUMBER),
                    "missing_information": genai.types.Schema(
                        type=genai.types.Type.ARRAY,
                        items=genai.types.Schema(type=genai.types.Type.STRING)
                    )
                }
            )
            
            # Prepare the generation config with structured output
            generate_config = types.GenerateContentConfig(
                response_mime_type="application/json",  # Request JSON response
                response_schema=task_graph_schema,     # Use our defined schema
                temperature=0.2,                      # Lower temperature for deterministic outputs
                top_p=0.8,
                top_k=40,
                max_output_tokens=8192,               # Enough tokens for the full task graph
                system_instruction=[
                    types.Part.from_text(text=self.system_prompt_template),
                ],
            )
            
            # Make the API call to Gemini
            self.logger.info("Calling Gemini API with structured output schema...")
            
            try:
                # Try with structured output first
                response = self.client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=generate_config,
                )
                
                self.logger.info("Received structured response from Gemini API")
                
                # Parse the structured JSON response
                if hasattr(response, 'parts') and response.parts:
                    try:
                        task_graph = json.loads(response.parts[0].text)
                        self.logger.info("Successfully parsed structured JSON response")
                    except json.JSONDecodeError:
                        self.logger.warning("Failed to parse structured JSON response, falling back to text extraction")
                        task_graph = self._extract_json_from_response(response.text)
                else:
                    task_graph = self._extract_json_from_response(response.text)
            
            except Exception as e:
                self.logger.warning(f"Structured output failed: {str(e)}, falling back to non-structured approach")
                
                # Fall back to non-structured approach if the structured one fails
                simple_config = types.GenerateContentConfig(
                    temperature=0.2,
                    top_p=0.8,
                    top_k=40,
                    max_output_tokens=8192,
                    system_instruction=[
                        types.Part.from_text(text=self.system_prompt_template),
                    ],
                )
                
                response = self.client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=simple_config,
                )
                
                self.logger.info("Received fallback response from Gemini API")
                
                # Extract JSON from the text response
                response_text = ""
                if hasattr(response, 'text'):
                    response_text = response.text
                elif hasattr(response, 'parts') and response.parts:
                    # Combine all text parts
                    for part in response.parts:
                        if hasattr(part, 'text'):
                            response_text += part.text
                self.logger.info(f"Response text length: {len(response_text)} characters")
                task_graph = self._extract_json_from_response(response_text)
            
            # Add source metadata
            task_graph["source"] = {
                "model": model,
                "raw_data_package": raw_data_package.get("name", "unknown")
            }
            
            # Validate the task graph structure
            self._validate_task_graph(task_graph)
            
            return task_graph
            
        except Exception as e:
            self.logger.error(f"Error generating task graph: {str(e)}")
            # Return a fallback task graph with error information
            return {
                "name": raw_data_package.get("name", "unknown"),
                "error": str(e),
                "status": "failed",
                "task_graph": {
                    "nodes": [],
                    "edges": []
                },
                "confidence_score": 0.0
            }
    
    def _extract_json_from_response(self, response_text: str) -> Dict[str, Any]:
        """Extract a JSON object from the Gemini API response.
        
        Args:
            response_text: The raw text response from Gemini
            
        Returns:
            Parsed JSON object
        """
        # Log the full response for debugging
        self.logger.debug(f"Full response text: {response_text}")
        
        # Try multiple approaches to extract JSON
        try:
            # Method 1: First try to parse the entire response as JSON
            try:
                return json.loads(response_text)
            except json.JSONDecodeError:
                pass
                
            # Method 2: Look for JSON with standard brackets
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    pass
            
            # Method 3: Try to find JSON blocks marked by code markers (common in LLM responses)
            json_matches = re.findall(r'```(?:json)?\s*({[\s\S]*?})\s*```', response_text)
            if json_matches:
                for match in json_matches:
                    try:
                        return json.loads(match)
                    except json.JSONDecodeError:
                        continue
            
            # Method 4: Try to construct a valid JSON structure from the text
            # This is more of a fallback that tries to extract a structured representation
            try:
                # If we reach here, let's try to build a structured task graph manually
                # by looking for step patterns in the text
                extracted_steps = []
                
                # Pattern 1: Numbered steps with a colon (Step 1: Do something)
                step_pattern1 = re.compile(r'Step\s+(\d+)[:.]\s+([^\n]+)', re.IGNORECASE)
                step_matches1 = step_pattern1.findall(response_text)
                
                # Pattern 2: Just numbered steps (1. Do something)
                step_pattern2 = re.compile(r'^\s*(\d+)\.\s+([^\n]+)', re.MULTILINE)
                step_matches2 = step_pattern2.findall(response_text)
                
                # Pattern 3: Steps with headers (STEP 1 - Do something)
                step_pattern3 = re.compile(r'STEP\s+(\d+)\s*[-:]\s*([^\n]+)', re.IGNORECASE)
                step_matches3 = step_pattern3.findall(response_text)
                
                # Combine all matches, favoring the more structured ones first
                all_matches = step_matches1 + step_matches3 + step_matches2
                seen_step_nums = set()
                
                for step_num, content in all_matches:
                    if step_num not in seen_step_nums:
                        extracted_steps.append({
                            "id": step_num,
                            "type": "action",
                            "content": content.strip(),
                            "metadata": {}
                        })
                        seen_step_nums.add(step_num)
                
                # If no structured steps found, try to extract paragraphs as steps
                if not extracted_steps:
                    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', response_text) if p.strip()]
                    # Filter out very short paragraphs or headings
                    action_paragraphs = [p for p in paragraphs if len(p) > 30 and not p.isupper()]
                    
                    for i, paragraph in enumerate(action_paragraphs):
                        extracted_steps.append({
                            "id": str(i+1),
                            "type": "action",
                            "content": paragraph,
                            "metadata": {}
                        })
                
                # Sort steps by ID
                extracted_steps.sort(key=lambda s: int(s["id"]) if s["id"].isdigit() else 999)
                
                # Create edges connecting nodes sequentially
                edges = []
                for i in range(len(extracted_steps) - 1):
                    edges.append({
                        "source": extracted_steps[i]["id"],
                        "target": extracted_steps[i+1]["id"]
                    })
                
                # If we found some steps, return a constructed task graph
                if extracted_steps:
                    self.logger.info(f"Extracted {len(extracted_steps)} steps using pattern matching")
                    return {
                        "name": "extracted_task_graph",
                        "description": "Task graph extracted from unstructured response",
                        "task_graph": {
                            "nodes": extracted_steps,
                            "edges": edges
                        },
                        "confidence_score": 0.6,  # Lower confidence due to extraction method
                        "extraction_method": "pattern_matching"
                    }
            except Exception as e:
                self.logger.warning(f"Failed fallback pattern extraction: {str(e)}")
            
            # If all else fails
            raise ValueError("No valid JSON structure found in the response")
                
        except Exception as e:
            self.logger.error(f"Failed to parse response into task graph: {str(e)}")
            self.logger.debug(f"Response excerpt: {response_text[:1000] if len(response_text) > 1000 else response_text}")
            
            # Return a minimal valid task graph with error information
            return {
                "name": "parsing_failed",
                "description": "Failed to parse task graph from Gemini response",
                "error": str(e),
                "response_text_sample": response_text[:500] + "..." if len(response_text) > 500 else response_text,
                "task_graph": {
                    "nodes": [],
                    "edges": []
                },
                "confidence_score": 0.0
            }
    
    def _validate_task_graph(self, task_graph: Dict[str, Any]) -> bool:
        """Validate the structure of the generated task graph.
        
        Args:
            task_graph: The task graph to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Check required fields
        required_fields = ["name", "description", "task_graph"]
        missing_fields = [field for field in required_fields if field not in task_graph]
        
        if missing_fields:
            self.logger.warning(f"Task graph missing required fields: {missing_fields}")
            
            # Add missing fields with defaults
            for field in missing_fields:
                if field == "name":
                    task_graph["name"] = "unnamed_task_graph"
                elif field == "description":
                    task_graph["description"] = "No description provided"
                elif field == "task_graph":
                    task_graph["task_graph"] = {"nodes": [], "edges": []}
        
        # Validate task graph structure
        if "task_graph" in task_graph:
            graph = task_graph["task_graph"]
            
            # Ensure nodes and edges exist
            if "nodes" not in graph or not isinstance(graph["nodes"], list):
                self.logger.warning("Task graph has no valid nodes list")
                graph["nodes"] = []
            
            if "edges" not in graph or not isinstance(graph["edges"], list):
                self.logger.warning("Task graph has no valid edges list")
                graph["edges"] = []
            
            # Validate nodes
            for i, node in enumerate(graph["nodes"]):
                if "id" not in node:
                    node["id"] = str(i + 1)
                    self.logger.warning(f"Added missing ID to node: {node}")
                
                if "content" not in node:
                    node["content"] = f"Step {node['id']}"
                    self.logger.warning(f"Added missing content to node: {node}")
            
            # Validate edges
            for i, edge in enumerate(graph["edges"]):
                if "source" not in edge or "target" not in edge:
                    self.logger.warning(f"Invalid edge at index {i}: {edge}")
                    # Remove invalid edge
                    graph["edges"][i] = None
            
            # Remove None values from edges
            graph["edges"] = [edge for edge in graph["edges"] if edge is not None]
            
            # Add confidence score if missing
            if "confidence_score" not in task_graph:
                task_graph["confidence_score"] = 0.7
                self.logger.warning("Added default confidence score to task graph")
        
        return True


def generate_task_graph_from_raw_data(raw_data_package_path: str, 
                                      output_dir: Optional[str] = None) -> Dict[str, Any]:
    """Generate a task graph from a raw data package file.
    
    This function is the main entry point for task graph generation.
    
    Args:
        raw_data_package_path: Path to the raw data package JSON file
        output_dir: Optional directory to save the generated task graph
        
    Returns:
        Dictionary containing the generated task graph
    """
    # Load the raw data package
    raw_data_package = load_json(raw_data_package_path)
    
    # Initialize the task graph generator
    generator = TaskGraphGenerator(output_dir=output_dir)
    
    # Generate the task graph
    task_graph = generator.generate_task_graph(raw_data_package)
    
    return {
        "raw_data_package": raw_data_package,
        "task_graph": task_graph
    }
