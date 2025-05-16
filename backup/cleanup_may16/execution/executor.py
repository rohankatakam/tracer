"""
Task Graph Executor for Anthropic Computer Use integration.

This module handles the execution of task graph nodes via web interface
with fixes for the critical issues in the original implementation.
"""

import os
import json
import logging
import time
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional

from ..browser.webdriver_manager import WebDriverManager

logger = logging.getLogger("task_graph_integration")

class TaskGraphExecutor:
    """Executes task graph nodes through Anthropic's Computer Use web interface."""
    
    def __init__(self, output_dir: str, web_driver_manager: WebDriverManager):
        """Initialize the TaskGraphExecutor.
        
        Args:
            output_dir: Directory for storing execution outputs
            web_driver_manager: WebDriverManager instance for browser interaction
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        self.prompts_dir = self.output_dir / "prompts"
        self.responses_dir = self.output_dir / "responses"
        
        for directory in [self.prompts_dir, self.responses_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Web driver manager for browser interaction
        self.web_driver = web_driver_manager
        
        # Set screenshots directory for the web driver
        self.web_driver.screenshots_dir = self.responses_dir
    
    async def execute_node(self, node: Dict[str, Any], 
                         state_context: List[Dict[str, Any]], 
                         node_prompt: str) -> Dict[str, Any]:
        """Execute a task graph node using the Computer Use Agent via web UI automation.
        
        Args:
            node: Task graph node
            state_context: Context from previous nodes
            node_prompt: Prompt for the Computer Use Agent
            
        Returns:
            Execution result dictionary
        """
        node_id = node.get("id", "unknown")
        logger.info(f"Executing node: {node_id}")
        
        # Save prompt to file
        timestamp = int(time.time())
        prompt_path = self.prompts_dir / f"{timestamp}_{node_id}.txt"
        response_path = self.responses_dir / f"{timestamp}_{node_id}.json"
        
        with open(prompt_path, 'w') as f:
            f.write(node_prompt)
        
        # Ensure WebDriver connection is alive before proceeding
        if not self.web_driver.ensure_connection():
            return {
                "id": node_id,
                "content": node.get("content", ""),
                "success": False,
                "error": "Failed to establish WebDriver connection",
                "response": ""
            }
        
        # Take a screenshot of current state before sending
        main_screenshot = self.web_driver.take_screenshot(f"{timestamp}_{node_id}_before_message.png")
        
        try:
            # Switch to the left iframe (Streamlit chat)
            iframe_success = self.web_driver.navigate_to_iframe([
                "iframe.left", 
                "iframe#left-pane", 
                "iframe.left-pane", 
                "iframe"
            ])
            
            if not iframe_success:
                raise Exception("Failed to switch to Streamlit chat iframe")
            
            # Take a screenshot after switching to the iframe
            iframe_screenshot = self.web_driver.take_screenshot(f"{timestamp}_{node_id}_iframe.png")
            
            # Find the chat input field
            chat_input_selectors = [
                "textarea[data-testid='stChatInput']",
                "textarea.streamlit-chat",
                "textarea.stChatInputArea",
                "div.stChatInputContainer textarea",
                "textarea[placeholder*='Type']",
                "textarea",
                "div[contenteditable='true']",
                "input[type='text']"
            ]
            
            textarea = self.web_driver.find_interactable_element(chat_input_selectors)
            
            if not textarea:
                raise Exception("Could not find chat input element")
            
            # Enter the prompt - uses improved text entry with fallbacks for element interactability
            text_entry_success = self.web_driver.enter_text(textarea, node_prompt)
            
            if not text_entry_success:
                raise Exception("Failed to enter text into chat input")
            
            # Take a screenshot before submitting
            before_submit_screenshot = self.web_driver.take_screenshot(f"{timestamp}_{node_id}_before_submit.png")
            
            # Submit the message - uses verification to prevent multiple submissions
            button_selectors = [
                "button[data-testid='stChatInputSubmitButton']",
                "button.streamlit-chat-submit",
                "button.stSubmitButton",
                "button:not([disabled])"
            ]
            
            submit_success = self.web_driver.submit_message(textarea, button_selectors)
            
            if not submit_success:
                raise Exception("Failed to submit message")
            
            # Wait for response with improved error handling
            response_text, response_screenshot = self.web_driver.wait_for_response(
                prompt=node_prompt,
                timeout=60
            )
            
            # Switch back to default content
            try:
                self.web_driver.driver.switch_to.default_content()
            except Exception as e:
                logger.warning(f"Error switching back to default content: {e}")
            
            # Always consider node execution a success if we got this far
            success = True
            
            # Prepare result data
            # Convert any Path objects to strings for JSON serialization
            screenshots_dict = {}
            for key, path in {
                "main": main_screenshot,
                "iframe": iframe_screenshot,
                "before_submit": before_submit_screenshot,
                "response": response_screenshot
            }.items():
                screenshots_dict[key] = str(path) if path else None
                
            result_data = {
                "id": node_id,
                "content": node.get("content", ""),
                "response": response_text,
                "success": success,
                "screenshots": screenshots_dict
            }
            
            # Save result to file
            with open(response_path, 'w') as f:
                json.dump(result_data, f, indent=2)
            
            # Ensure all paths are string representations
            return {
                "id": node_id,
                "content": node.get("content", ""),
                "success": success,
                "response": response_text,
                "prompt_file": str(prompt_path),
                "response_file": str(response_path),
                "screenshots": result_data["screenshots"]
            }
            
        except Exception as e:
            logger.error(f"Error executing node {node_id}: {e}")
            
            # Take a screenshot of the error state if possible
            error_screenshot = None
            if self.web_driver.driver:
                try:
                    error_screenshot = self.web_driver.take_screenshot(f"{timestamp}_{node_id}_error.png")
                except Exception as screenshot_error:
                    logger.error(f"Failed to take error screenshot: {screenshot_error}")
            
            return {
                "id": node_id,
                "content": node.get("content", ""),
                "success": False,
                "error": str(e),
                "prompt_file": str(prompt_path)
            }
    
    async def wait_between_nodes(self, seconds: int = 2):
        """Wait between node executions to allow Claude to process.
        
        Args:
            seconds: Number of seconds to wait
        """
        logger.info(f"Waiting {seconds} seconds between nodes...")
        await asyncio.sleep(seconds)
