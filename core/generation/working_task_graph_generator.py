"""
Task Graph Generator (Working Implementation)

This module provides functionality to generate task graphs from raw bug report data
using Google's Gemini API with a working, tested implementation.
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import argparse
import sys

from google import genai
from google.genai import types

class TaskGraphGenerator:
    """
    Class for generating task graphs from raw bug report data using Gemini.
    
    This implementation is based on a working example and properly handles
    the Gemini API calls with the correct structure.
    """
    
    def __init__(self, 
                 model_name: str = "gemini-2.5-flash-preview-04-17", 
                 output_dir: Optional[str] = None, 
                 log_level: int = logging.INFO):
        """
        Initialize the Task Graph Generator.
        
        Args:
            model_name: Name of the Gemini model to use
            output_dir: Directory to save generated task graphs
            log_level: Logging level
        """
        # Configure logging
        self.logger = logging.getLogger("task_graph_generator")
        self.logger.setLevel(log_level)
        
        # Configure Gemini client
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        self.logger.info(f"TaskGraphGenerator initialized with model: {model_name}")
        
        # Set output directory
        if output_dir:
            self.output_dir = Path(output_dir)
            self.output_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.output_dir = None
        
        # Load system prompt template
        self.system_prompt_template = self._get_system_prompt()
    
    def _get_system_prompt(self) -> str:
        """
        Get the system prompt template for task graph generation.
        
        Returns:
            System prompt template as a string
        """
        # Define the system prompt that guides the model behavior
        system_prompt = """
        You are a helpful assistant that generates task graphs for software bug reproduction steps.
        
        INSTRUCTIONS:
        1. Generate a structured task graph from the bug report data
        2. Each step must be detailed and actionable 
        3. Include specific UI elements, inputs, and expected results
        4. Reference the provided screenshots for visual context
        5. Your task graph should enable a computer agent to reproduce the bug
        
        OUTPUT FORMAT:
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
                "id": "[step_number]",
                "type": "action",
                "content": "[Detailed description of action]",
                "metadata": {
                  "image_refs": ["[screenshot_filename]"],
                  "ui_elements": ["[UI element to interact with]"],
                  "inputs": ["[input=value]"],
                  "expected_result": "[What should happen after this step]"
                }
              }
            ],
            "edges": [
              {
                "source": "[source_step_id]",
                "target": "[target_step_id]"
              }
            ]
          },
          "verification_steps": [
            "[Step to verify the bug is present]"
          ],
          "confidence_score": 0.85,
          "missing_information": ["[Any critical missing information]"] 
        }
        """
        return system_prompt
    
    def generate_task_graph(self, bug_data_package: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a task graph from bug data.
        
        Args:
            bug_data_package: Dictionary containing bug data
                Expected structure varies, but should contain enough information
                to generate a task graph
        
        Returns:
            Dictionary containing the task graph
        """
        # Extract information from the bug data package
        if "id" in bug_data_package:
            bug_id = str(bug_data_package["id"])
        elif "bug_id" in bug_data_package:
            bug_id = str(bug_data_package["bug_id"])
        elif "name" in bug_data_package:
            bug_id = str(bug_data_package["name"]).replace("bug_", "")
        else:
            bug_id = "unknown"
        
        self.logger.info(f"Generating task graph for: {bug_id}")
        
        # Create a user prompt from the bug data
        user_prompt = self._create_user_prompt(bug_data_package)
        self.logger.info(f"User prompt length: {len(user_prompt)} characters")
        
        # Call the Gemini API to generate the task graph
        task_graph = self._call_gemini_api(user_prompt)
        
        # Add the bug ID if it's not already present
        if "name" not in task_graph or not task_graph["name"]:
            task_graph["name"] = f"bug_{bug_id}"
        
        # Save the task graph if an output directory is specified
        if self.output_dir:
            output_path = self.output_dir / f"{bug_id}_task_graph.json"
            with open(output_path, "w") as f:
                json.dump(task_graph, f, indent=2)
            self.logger.info(f"Saved task graph to: {output_path}")
        
        return task_graph
    
    def _create_user_prompt(self, bug_data_package: Dict[str, Any]) -> str:
        """
        Create a user prompt from bug data.
        
        Args:
            bug_data_package: Dictionary containing bug data
        
        Returns:
            String containing the user prompt
        """
        # Handle different schema formats
        if "raw_text" in bug_data_package:
            # Enhanced schema
            raw_text = bug_data_package.get("raw_text", "")
            bug_title = bug_data_package.get("title", "Unknown Bug")
            screenshots = bug_data_package.get("screenshots", [])
            
            # Build the prompt
            prompt = f"Bug Title: {bug_title}\n\n"
            prompt += "Raw Text from Bug Report:\n"
            prompt += raw_text + "\n\n"
            
            # Add screenshot information
            if screenshots:
                prompt += "Screenshots in the Bug Report:\n"
                for i, screenshot in enumerate(screenshots):
                    filename = screenshot.get("filename", f"screenshot_{i}.jpg")
                    caption = screenshot.get("caption", "No caption provided")
                    ocr_text = screenshot.get("ocr_text", "No OCR text available")
                    
                    prompt += f"Screenshot: {filename}\n"
                    prompt += f"Caption: {caption}\n"
                    prompt += f"OCR Text: {ocr_text}\n\n"
        
        else:
            # Legacy schema - format the whole package as text
            prompt = json.dumps(bug_data_package, indent=2)
        
        # Append task instructions
        prompt += "\n\nPlease generate a task graph for reproducing this bug using the format specified."
        return prompt
    
    def _call_gemini_api(self, prompt: str) -> Dict[str, Any]:
        """
        Call the Gemini API to generate a task graph.
        
        Args:
            prompt: String containing the user prompt
        
        Returns:
            Dictionary containing the task graph
        """
        try:
            # Use the model specified in the constructor
            model = self.model_name
            self.logger.info(f"Using model: {model}")
            
            # Prepare the content with the text prompt (following the working example)
            contents = [
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=prompt)]
                )
            ]
            
            # Create a generation config for JSON response
            generate_content_config = types.GenerateContentConfig(
                response_mime_type="application/json"
            )
            
            # Make the API call to Gemini
            self.logger.info("Calling Gemini API...")
            response = self.client.models.generate_content(
                model=model,
                contents=contents,
                config=generate_content_config
            )
            
            self.logger.info("Received response from Gemini API")
            
            # Extract and parse the JSON response
            if hasattr(response, 'text'):
                # Most direct approach - if the response has a text attribute
                try:
                    parsed_response = json.loads(response.text)
                    self.logger.info("Successfully parsed JSON from response.text")
                    
                    # Handle the case where the response is a list instead of a dictionary
                    if isinstance(parsed_response, list) and len(parsed_response) > 0:
                        self.logger.info("Response is a list, using the first item")
                        task_graph = parsed_response[0] if isinstance(parsed_response[0], dict) else {"task_graph": parsed_response}
                    else:
                        task_graph = parsed_response
                    return task_graph
                except json.JSONDecodeError:
                    self.logger.warning("Failed to parse JSON from response.text, trying alternatives")
            
            if hasattr(response, 'parts') and response.parts:
                # Try parsing from parts
                try:
                    parsed_response = json.loads(response.parts[0].text)
                    self.logger.info("Successfully parsed JSON from response.parts[0].text")
                    
                    # Handle the case where the response is a list instead of a dictionary
                    if isinstance(parsed_response, list) and len(parsed_response) > 0:
                        self.logger.info("Response is a list, using the first item")
                        task_graph = parsed_response[0] if isinstance(parsed_response[0], dict) else {"task_graph": parsed_response}
                    else:
                        task_graph = parsed_response
                    return task_graph
                except (json.JSONDecodeError, AttributeError, IndexError):
                    self.logger.warning("Failed to parse JSON from parts, trying extraction fallback")
            
            # Last resort: try to extract JSON from the response text
            response_text = str(response)
            self.logger.info("Attempting to extract JSON from response string")
            return self._extract_json_from_response(response_text)
            
        except Exception as e:
            self.logger.error(f"Error generating task graph: {str(e)}")
            # Return a fallback task graph with error information
            return {
                "name": f"bug_{prompt[:20]}...",
                "error": str(e),
                "status": "failed",
                "task_graph": {
                    "nodes": [],
                    "edges": []
                },
                "confidence_score": 0.0
            }
    
    def _extract_json_from_response(self, response_text: str) -> Dict[str, Any]:
        """
        Extract a JSON object from the Gemini API response.
        
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
            
            # Method 4: Look for JSON-like structures and try to fix common issues
            json_like = re.search(r'({[^{]*?"name"[^{]*?})', response_text)
            if json_like:
                # Try to clean up and parse the matched JSON-like text
                json_str = json_like.group(1)
                # Replace common issues like JavaScript-style comments and trailing commas
                json_str = re.sub(r'//.*?\n', '\n', json_str)
                json_str = re.sub(r',\s*}', '}', json_str)
                json_str = re.sub(r',\s*]', ']', json_str)
                
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    pass
            
            # If all parsing attempts fail, return a minimal task graph
            self.logger.warning("All attempts to extract JSON failed")
            return {
                "name": "unknown",
                "error": "Failed to parse response from Gemini API",
                "status": "failed",
                "task_graph": {
                    "nodes": [],
                    "edges": []
                },
                "confidence_score": 0.0
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting JSON from response: {str(e)}")
            return {
                "name": "unknown",
                "error": f"Error extracting JSON: {str(e)}",
                "status": "failed",
                "task_graph": {
                    "nodes": [],
                    "edges": []
                },
                "confidence_score": 0.0
            }
