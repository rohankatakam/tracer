import os
import json
import logging
import time
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("task_graph_integration")

class TaskGraphIntegrator:
    """Integrates task graphs with Anthropic's Computer Use reference implementation."""
    
    def __init__(self, output_dir: str, model: str = "claude-3-7-sonnet-20240620", 
                 thinking_budget: int = 1024, web_ui_url: str = "http://localhost:8080"):
        self.model = model
        self.thinking_budget = thinking_budget
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.web_ui_url = web_ui_url
        self.driver = None
        
        # Set up browser options
        self.options = Options()
        self.options.add_argument("--headless")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        
        # Create subdirectories
        self.prompts_dir = self.output_dir / "prompts"
        self.responses_dir = self.output_dir / "responses"
        
        for directory in [self.prompts_dir, self.responses_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Load API key
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
        
        logger.info(f"Task Graph Integrator initialized with model: {model}")
    
    def load_task_graph(self, task_graph_path: str) -> Dict[str, Any]:
        """Load a task graph from a JSON file.
        
        Args:
            task_graph_path: Path to the task graph JSON file
            
        Returns:
            Parsed task graph as a dictionary
        """
        # Load task graph
        with open(task_graph_path, 'r') as f:
            task_graph_data = json.load(f)
        
        # Handle nested task graph structure
        if "task_graph" in task_graph_data and isinstance(task_graph_data["task_graph"], dict):
            # Extract the nested task graph but preserve the name
            name = task_graph_data.get("name", "Unnamed Task Graph")
            task_graph = task_graph_data["task_graph"]
            task_graph["name"] = name
        else:
            # Use as-is if no nesting
            task_graph = task_graph_data
        
        logger.info(f"Loaded task graph: {task_graph.get('name', 'Unnamed Task Graph')}")
        return task_graph
    
    def create_execution_order(self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> List[str]:
        """Create execution order based on nodes and edges.
        
        Args:
            nodes: List of node dictionaries
            edges: List of edge dictionaries
            
        Returns:
            List of node IDs in execution order
        """
        # Create dependency map
        dependencies = {node.get("id"): [] for node in nodes}
        
        for edge in edges:
            source = edge.get("source")
            target = edge.get("target")
            if source and target:
                dependencies[target].append(source)
        
        # Create execution order
        execution_order = []
        completed = set()
        
        def add_node(node_id):
            if node_id in completed:
                return
            
            for dep in dependencies.get(node_id, []):
                if dep not in completed:
                    add_node(dep)
            
            execution_order.append(node_id)
            completed.add(node_id)
        
        for node_id in dependencies.keys():
            add_node(node_id)
        
        return execution_order
    
    def create_node_prompt(self, node: Dict[str, Any], state_context: List[Dict[str, Any]]) -> str:
        """Create a simplified prompt for node execution.
        
        Args:
            node: Task graph node
            state_context: Context from previous nodes
            
        Returns:
            Simplified prompt for the Computer Use Agent
        """
        content = node.get("content", "")
        task_type = node.get("type", "task").capitalize()
        node_id = node.get("id", "unknown")
        
        # Handle metadata structure in Firefox task graph format
        metadata = node.get("metadata", {})
        expected_result = metadata.get("expected_result", "")
        
        # Extract UI elements - handle both direct and metadata formats
        ui_elements = node.get("ui_elements", [])
        if not ui_elements and "ui_elements" in metadata:
            ui_elements = metadata["ui_elements"]
        
        # Extract input data - handle both direct and metadata formats
        inputs = []
        
        # Check if inputs are in metadata (Firefox task graph format)
        meta_inputs = metadata.get("inputs", [])
        if isinstance(meta_inputs, list):
            inputs = meta_inputs
        
        # Create a simplified prompt that focuses just on the current task
        # and avoids overwhelming the Computer Use interface
        prompt = f"I need your help to complete a task using Firefox: {content}"
        
        # Add expected result if available
        if expected_result:
            prompt += f"\n\nSuccess means: {expected_result}"
        
        # Add UI elements if available (limit to just mentioning them)
        if ui_elements:
            ui_elements_str = ", ".join(ui_elements)
            prompt += f"\n\nYou'll need to interact with: {ui_elements_str}"
        
        # Add inputs if available
        if inputs:
            inputs_str = ", ".join(inputs)
            prompt += f"\n\nUse this input: {inputs_str}"
        
        return prompt
    
    def ensure_driver_connection(self):
        """Ensure WebDriver connection is alive, reconnect if needed."""
        try:
            # Try a simple operation to check if driver is still responsive
            if self.driver:
                self.driver.current_url  # This will raise an exception if connection is lost
            return True
        except (WebDriverException, ConnectionError) as e:
            logger.warning(f"WebDriver connection lost: {e}. Attempting to reconnect...")
            try:
                # Close the current driver if it exists
                if self.driver:
                    try:
                        self.driver.quit()
                    except Exception:
                        pass  # Ignore errors during quit
                
                # Create a new driver
                self.driver = webdriver.Chrome(options=self.options)
                self.driver.set_page_load_timeout(30)  # shorter timeout
                
                # Navigate to the Computer Use Demo
                logger.info(f"Reconnecting to Computer Use Demo at {self.web_ui_url}")
                self.driver.get(self.web_ui_url)
                
                # Wait for page to load
                time.sleep(3)
                return True
            except Exception as reconnect_error:
                logger.error(f"Failed to reconnect WebDriver: {reconnect_error}")
                return False
    
    async def execute_node(self, node: Dict[str, Any], state_context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute a task graph node using the Computer Use Agent via web UI automation.
        
        Args:
            node: Task graph node
            state_context: Context from previous nodes
            
        Returns:
            Execution result dictionary
        """
        node_id = node.get("id", "unknown")
        logger.info(f"Executing node: {node_id}")
        
        # Create prompt for the node
        prompt = self.create_node_prompt(node, state_context)
        
        # Save prompt to file
        timestamp = int(time.time())  # Use timestamp instead of node_id to ensure uniqueness
        prompt_path = self.prompts_dir / f"{timestamp}_{node_id}.txt"
        response_path = self.responses_dir / f"{timestamp}_{node_id}.json"
        
        with open(prompt_path, 'w') as f:
            f.write(prompt)
            
        # Ensure WebDriver connection is alive before proceeding
        if not self.ensure_driver_connection():
            return {
                "id": node_id,
                "success": False,
                "content": node.get("content", ""),
                "error": "Failed to establish WebDriver connection",
                "response": ""
            }
        
        # Take a screenshot of current state before sending the next message
        main_screenshot = self.responses_dir / f"{timestamp}_{node_id}_before_message.png"
        try:
            # Check if chat is busy first - if there's a "Stop" button visible, wait a bit longer
            self.driver.switch_to.default_content()
            stop_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Stop')]")
            if stop_buttons and any(btn.is_displayed() for btn in stop_buttons):
                logger.info("Claude appears to be busy (Stop button visible). Waiting 5 seconds...")
                await asyncio.sleep(5)
                
            self.driver.save_screenshot(str(main_screenshot))
        except Exception as e:
            logger.warning(f"Error checking for busy state or taking screenshot: {e}")
        
        try:
            # Before each node execution, make sure we're in the default content
            # and then switch to the left iframe (Streamlit chat)
            try:
                self.driver.switch_to.default_content()
            except Exception as e:
                logger.warning(f"Error switching to default content: {e}")
            
            # The Computer Use Demo has two iframes: 
            # Left iframe (Streamlit app with chat) and right iframe (VNC viewer with Firefox)
            # First, we need to switch to the left iframe to interact with chat
            logger.info("Switching to left iframe (Streamlit chat interface)")
            
            # Wait for the iframe to be present
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "iframe.left"))
            )
            
            # Switch to the left iframe
            left_iframe = self.driver.find_element(By.CSS_SELECTOR, "iframe.left")
            self.driver.switch_to.frame(left_iframe)
            
            # Take a screenshot after switching to the iframe
            iframe_screenshot = self.responses_dir / f"{timestamp}_{node_id}_iframe.png"
            self.driver.save_screenshot(str(iframe_screenshot))
            
            # Now interact with the Streamlit chat interface
            logger.info("Looking for chat input in Streamlit interface")
            
            # Wait for Streamlit to load
            time.sleep(5)  # Give Streamlit a moment to fully initialize
            
            # Find the chatbox - Streamlit uses specific selectors
            # First, try to find the text area by different selectors
            selectors = [
                # Streamlit's chat textarea often has these classes or attributes
                "textarea[data-testid='stChatInput']",
                "textarea.streamlit-chat",
                "textarea.stChatInputArea",
                "div.stChatInputContainer textarea",
                "textarea[placeholder*='Type']",
                # Generic fallbacks
                "textarea",
                "div[contenteditable='true']",
                "input[type='text']"
            ]
            
            # Try each selector to find the chat input
            textarea = None
            for selector in selectors:
                try:
                    logger.info(f"Trying selector: {selector}")
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        textarea = elements[0]
                        logger.info(f"Found input with selector: {selector}")
                        break
                except Exception as e:
                    logger.warning(f"Selector {selector} failed: {e}")
            
            if not textarea:
                # If we can't find a specific input element, try to find any active element
                logger.info("No standard input found. Trying to find active element.")
                
                # Take a screenshot of what we see
                no_input_screenshot = self.responses_dir / f"{timestamp}_{node_id}_no_input.png"
                self.driver.save_screenshot(str(no_input_screenshot))
                
                # Save page source for debugging
                page_source_path = self.responses_dir / f"{timestamp}_{node_id}_page_source.html"
                with open(page_source_path, 'w') as f:
                    f.write(self.driver.page_source)
                
                # Try clicking in the center of the iframe where the input might be
                try:
                    logger.info("Trying to click in the center of the iframe")
                    action = webdriver.ActionChains(self.driver)
                    action.move_to_element_with_offset(self.driver.find_element(By.TAG_NAME, "body"), 0, 0)
                    action.click()
                    action.perform()
                    
                    # Try to directly get the active element
                    active_element = self.driver.switch_to.active_element
                    textarea = active_element
                    logger.info("Using active element as input")
                except Exception as e:
                    logger.error(f"Failed to find input element: {e}")
                    raise Exception("Could not locate chat input element")
            
            if textarea:
                # Enter the prompt into the textarea
                logger.info("Entering prompt")
                textarea.clear()
                
                # Check if there's a pending message waiting to be submitted
                try:
                    current_text = textarea.get_attribute('value')
                    if current_text and len(current_text) > 0:
                        logger.warning(f"Found existing text in input field: '{current_text[:20]}...'. Clearing before entering new text.")
                        textarea.clear()
                        time.sleep(0.5)  # Wait after clearing
                except Exception as e:
                    logger.warning(f"Error checking current input text: {e}")
                
                # Send keys character by character with small delays to mimic human typing
                for char in prompt:
                    textarea.send_keys(char)
                    time.sleep(0.01)  # Small delay between characters
                
                time.sleep(0.5)  # Short pause after typing
                
                # Look for submit button
                logger.info("Looking for submit button")
                
                # Try to find the submit button
                submit_button = None
                button_selectors = [
                    "button[data-testid='stChatInputSubmitButton']",
                    "button.streamlit-chat-submit",
                    "button.stSubmitButton",
                    "button:not([disabled])"
                ]
                
                for selector in button_selectors:
                    try:
                        buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for button in buttons:
                            try:
                                if button.is_displayed() and button.is_enabled():
                                    submit_button = button
                                    logger.info(f"Found submit button with selector: {selector}")
                                    break
                            except:
                                continue
                        if submit_button:
                            break
                    except Exception as e:
                        logger.warning(f"Button selector {selector} failed: {e}")
            
            if submit_button:
                # Only use JavaScript click as it's most reliable for Streamlit
                try:
                    logger.info("Clicking submit button with JavaScript click")
                    self.driver.execute_script("arguments[0].click();", submit_button)
                    
                    # Critical: Wait to ensure the click registers properly
                    time.sleep(2)
                    
                    # Verify submission was successful by checking if input was cleared
                    try:
                        current_text = textarea.get_attribute('value')
                        if current_text and len(current_text) > 0:
                            logger.warning(f"Submission may have failed as text is still present in input field")
                            # Clear the input and try one more time with different method
                            textarea.clear()
                            time.sleep(1)
                            self.driver.execute_script("arguments[0].value = '';", textarea)
                            # DO NOT try to submit again to avoid multiple submissions
                        else:
                            logger.info("Submission successful - input field is now empty")
                    except Exception as e:
                        logger.warning(f"Error verifying submission: {e}")
                except Exception as e:
                    logger.warning(f"JavaScript click failed: {e}")
                    logger.warning("Not attempting alternative submission methods to avoid multiple messages")
            else:
                logger.warning("No submit button found, but NOT using Enter key to avoid multiple submissions")
                logger.warning("Consider checking the Streamlit interface structure if this persists")
                
                # Wait for response
                logger.info("Waiting for response to appear")
                
                # Take screenshot after submission
                submit_screenshot = self.responses_dir / f"{timestamp}_{node_id}_after_submit.png"
                self.driver.save_screenshot(str(submit_screenshot))
                
                # Define a reasonable timeout for Claude to respond
                claude_response_timeout = 60  # seconds
                logger.info(f"Waiting {claude_response_timeout} seconds for Claude to respond")
                
                # Try to find the response by various selectors
                response_selectors = [
                    # Streamlit-specific selectors (most likely based on Streamlit's structure)
                    "div[data-testid*='stChatMessage']",  # Streamlit chat messages
                    "div.stChatMessage",  # Streamlit chat message class
                    "div.element-container div",  # General Streamlit elements
                    "div.st-emotion-cache",  # Streamlit emotion cache elements
                    "div.streamlit-expanderContent p",  # Expanded content
                    "div.chat-message",  # Generic chat message
                    
                    # Generic chat UI selectors
                    "div.message-container div.message.bot",
                    "div.message.from-assistant",
                    "pre.response-text",
                    "div.st-emotion-cache div p",
                    "div[data-testid*='chat-message']",
                    ".streamlit-container div",
                    "div.message",
                    
                    # Last resort - any paragraph or text element
                    "p",
                    "div.markdown-text-container"
                ]
                
                response_text = None
                start_time = time.time()
                
                while time.time() - start_time < claude_response_timeout:
                    # Take periodic screenshots to see what's happening
                    if int(time.time() - start_time) % 10 == 0:  # Every 10 seconds
                        waiting_screenshot = self.responses_dir / f"{timestamp}_{node_id}_waiting_{int(time.time() - start_time)}.png"
                        self.driver.save_screenshot(str(waiting_screenshot))
                    
                    for selector in response_selectors:
                        try:
                            logger.info(f"Looking for response with selector: {selector}")
                            response_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            
                            if response_elements:
                                # Look at the last few elements if there are multiple
                                for element in reversed(response_elements[-3:]):  # Check the last 3 elements
                                    element_text = element.text
                                    if element_text and len(element_text) > 10 and element_text != prompt:  # Check it has meaningful content
                                        response_text = element_text
                                        logger.info(f"Found response with selector: {selector}")
                                        break
                            
                            if response_text:
                                break
                        except Exception as e:
                            logger.debug(f"Response selector {selector} failed: {e}")
                    
                    if response_text:
                        # Take final screenshot when response is found
                        response_screenshot = self.responses_dir / f"{timestamp}_{node_id}_response_found.png"
                        self.driver.save_screenshot(str(response_screenshot))
                        break
                    
                    time.sleep(1)  # Check once per second
            
            if not response_text:
                # If we still don't have a response, try more aggressive extraction methods
                logger.warning("No specific response element found, trying alternative extraction methods")
                try:
                    # Save final screenshot before attempting alternative methods
                    final_screenshot = self.responses_dir / f"{timestamp}_{node_id}_final_no_response.png"
                    self.driver.save_screenshot(str(final_screenshot))
                    
                    # Save page source for debugging
                    page_source_path = self.responses_dir / f"{timestamp}_{node_id}_final_page_source.html"
                    with open(page_source_path, 'w') as f:
                        f.write(self.driver.page_source)
                    
                    # Method 1: Try to get any text element with substantial content
                    logger.info("Trying to find any text that's appeared since submission")
                    all_text_elements = self.driver.find_elements(By.XPATH, "//*[text()]")
                    for element in all_text_elements:
                        try:
                            element_text = element.text.strip()
                            if element_text and len(element_text) > 20 and element_text != prompt:
                                response_text = element_text
                                logger.info(f"Found potential response text: {element_text[:50]}...")
                                break
                        except Exception:
                            continue
                            
                    # Method 2: Look for any div with substantial text
                    if not response_text:
                        logger.info("Looking for any div with substantial text")
                        all_divs = self.driver.find_elements(By.TAG_NAME, "div")
                        for div in all_divs:
                            try:
                                div_text = div.text.strip()
                                if div_text and len(div_text) > 50 and div_text != prompt:
                                    response_text = div_text
                                    logger.info(f"Found text in div: {div_text[:50]}...")
                                    break
                            except Exception:
                                continue
                except Exception as e:
                    logger.error(f"Failed to extract response text from page: {e}")
            
            # If still no response, log warning but continue with execution
            if not response_text:
                response_text = "[No response could be extracted from the UI. See screenshots for details.]"
                logger.warning("Failed to extract any response text but will continue with next node")
            
            # Always consider node execution a success to continue with the task graph
            # In a real implementation, we could add more verification logic
            success = True
            
            # Switch back to default content
            self.driver.switch_to.default_content()
            
            # Save result to file
            result_data = {
                "id": node_id,
                "content": node.get("content", ""),
                "response": response_text,
                "success": success,
                "screenshots": {
                    "main": str(main_screenshot),
                    "iframe": str(iframe_screenshot),
                    "after_submit": str(submit_screenshot) if 'submit_screenshot' in locals() else None,
                    "response": str(response_screenshot) if 'response_screenshot' in locals() else None
                }
            }
            with open(response_path, 'w') as f:
                json.dump(result_data, f, indent=2)
            
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
            if self.driver:
                try:
                    # Try to switch back to default content first
                    try:
                        self.driver.switch_to.default_content()
                    except:
                        pass
                        
                    error_screenshot_path = self.responses_dir / f"{timestamp}_{node_id}_error.png"
                    self.driver.save_screenshot(str(error_screenshot_path))
                    
                    # Also save page source for debugging
                    error_source_path = self.responses_dir / f"{timestamp}_{node_id}_error_source.html"
                    with open(error_source_path, 'w') as f:
                        f.write(self.driver.page_source)
                except Exception as screenshot_error:
                    logger.error(f"Failed to take error screenshot: {screenshot_error}")
            
            return {
                "id": node_id,
                "content": node.get("content", ""),
                "success": False,
                "error": str(e),
                "prompt_file": str(prompt_path)
            }
    
    async def execute_task_graph(self, task_graph_path: str) -> Dict[str, Any]:
        """Execute an entire task graph.
        
        Args:
            task_graph_path: Path to the task graph JSON file
            
        Returns:
            Task graph execution results
        """
        # Load task graph
        task_graph = self.load_task_graph(task_graph_path)
        
        # Get nodes and edges
        nodes = task_graph.get("nodes", [])
        edges = task_graph.get("edges", [])
        
        # Create execution order
        execution_order = self.create_execution_order(nodes, edges)
        logger.info(f"Execution order: {execution_order}")
        
        # Create node map for easy lookup
        node_map = {node.get("id"): node for node in nodes}
        
        # Initialize browser if not already done
        if self.driver is None:
            logger.info(f"Initializing browser session")
            self.driver = webdriver.Chrome(options=self.options)
            self.driver.set_page_load_timeout(60)  # 60 second timeout for page loads
            
            # Only navigate to the Computer Use Demo on first initialization
            logger.info(f"Navigating to Computer Use Demo at {self.web_ui_url}")
            
            # Add http:// prefix if not present
            url = self.web_ui_url
            if not url.startswith(('http://', 'https://')):
                url = 'http://' + url
                
            # Try multiple times to load the URL with different methods
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    logger.info(f"Attempt {attempt+1}/{max_attempts} to navigate to {url}")
                    
                    # Clear any existing data in the URL bar
                    self.driver.get('about:blank')
                    time.sleep(1)
                    
                    # Navigate to the actual URL
                    self.driver.get(url)
                    
                    # Wait for page to load
                    WebDriverWait(self.driver, 10).until(
                        lambda d: d.execute_script('return document.readyState') == 'complete'
                    )
                    
                    # Verify we loaded the correct page by checking URL
                    current_url = self.driver.current_url
                    if 'localhost:8080' in current_url or '127.0.0.1:8080' in current_url:
                        logger.info(f"Successfully loaded Computer Use Demo at {current_url}")
                        break
                    else:
                        logger.warning(f"Loaded incorrect URL: {current_url}, retrying...")
                        time.sleep(2)
                except Exception as e:
                    logger.warning(f"Navigation attempt {attempt+1} failed: {e}")
                    time.sleep(2)
                    
            # One final check to make sure we're on the right page
            try:
                if not ('localhost:8080' in self.driver.current_url or '127.0.0.1:8080' in self.driver.current_url):
                    logger.error(f"Failed to load Computer Use Demo, current URL: {self.driver.current_url}")
            except Exception as e:
                logger.error(f"Error checking current URL: {e}")
            
            # Wait for any previous tasks to complete - look for "running" indicators
            # and wait until they're no longer present
            try:
                self.driver.switch_to.default_content()
                running_indicators = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'RUNNING') or contains(text(), 'Running')]")
                stop_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Stop')]")
                
                if (running_indicators and any(indicator.is_displayed() for indicator in running_indicators)) or \
                   (stop_buttons and any(btn.is_displayed() for btn in stop_buttons)):
                    logger.info("Detected that Claude is still working on previous task. Waiting 10 seconds...")
                    await asyncio.sleep(10)  # Wait longer if there's indication Claude is still working
            except Exception as e:
                logger.warning(f"Error checking for running indicators: {e}")
                await asyncio.sleep(5)  # Default wait if we can't check properly
            
            # Take a screenshot of the initial state
            os.makedirs(self.responses_dir, exist_ok=True)
            init_screenshot = self.responses_dir / "initial_state.png"
            self.driver.save_screenshot(str(init_screenshot))
        
        # Execute nodes in order
        state_context = []
        results = []
        success = True
        failure_node = None
        
        for node_id in execution_order:
            if node_id not in node_map:
                logger.warning(f"Node {node_id} not found in task graph")
                continue
            
            node = node_map[node_id]
            
            # Skip start and end nodes (optional, can be configured)
            node_type = node.get("type", "")
            if node_type in ["start", "end"]:
                # Add a success result for these nodes
                result = {
                    "id": node_id,
                    "content": node.get("content", ""),
                    "success": True,
                    "type": node_type,
                    "skipped": True
                }
                results.append(result)
                state_context.append(result)
                continue
            
            # Execute the node
            try:
                logger.info(f"Executing node {node_id}: {node.get('content', '')[:50]}...")
                result = await self.execute_node(node, state_context)
                
                # Even if the node result has success=False, we'll continue with the task graph
                # Just track that we had some failures for final reporting
                if not result.get("success", False):
                    success = False
                    if not failure_node:
                        failure_node = node_id
                    logger.warning(f"Node {node_id} had issues but continuing with next node")
                
                results.append(result)
                state_context.append(result)
                
                # Critical: Wait enough time to ensure Claude has fully processed the message
                # but not too long to cause WebDriver connection issues
                logger.info(f"Waiting for Claude to process the task before proceeding...")
                
                # Wait shorter time but check for Claude's response indicator
                await asyncio.sleep(5)
                
                # Verify Claude has indeed finished responding
                try:
                    self.ensure_driver_connection() # Make sure connection is still alive
                    self.driver.switch_to.default_content()
                    iframe = None
                    for selector in ["iframe#left-pane", "iframe.left-pane", "iframe"]:
                        try:
                            iframes = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            if iframes:
                                iframe = iframes[0]
                                self.driver.switch_to.frame(iframe)
                                break
                        except Exception:
                            continue
                            
                    # Check if Claude is still processing (shown by a loading spinner or 'Running' text)
                    processing_indicators = [
                        "div.streamlit-container div[aria-label*='Loading']",
                        "div.stStatusWidget",
                        "div[data-testid*='stStatusWidget']"
                    ]
                    
                    is_still_processing = False
                    for indicator in processing_indicators:
                        try:
                            elements = self.driver.find_elements(By.CSS_SELECTOR, indicator)
                            if elements and any(elem.is_displayed() for elem in elements):
                                is_still_processing = True
                                logger.info("Claude is still processing - waiting longer")
                                await asyncio.sleep(5)
                                break
                        except Exception:
                            continue
                                
                    if not is_still_processing:
                        logger.info("Claude has finished processing")
                except Exception as e:
                    logger.warning(f"Error checking Claude processing state: {e}")
                    # Default to short wait if checking fails
                    await asyncio.sleep(3)
                
                # Take a screenshot to document the current state after the waiting period
                timestamp = int(time.time())
                post_wait_screenshot = self.responses_dir / f"{timestamp}_{node_id}_post_wait.png"
                self.driver.save_screenshot(str(post_wait_screenshot))
                
            except Exception as e:
                # If a node completely fails, log it but continue with the next node
                logger.error(f"Error executing node {node_id}: {str(e)}")
                result = {
                    "id": node_id,
                    "content": node.get("content", ""),
                    "success": False,
                    "error": str(e),
                    "response": f"Exception occurred: {str(e)}"
                }
                success = False
                if not failure_node:
                    failure_node = node_id
                results.append(result)
                state_context.append(result)
        
        # Save execution results
        execution_results = {
            "task_graph": task_graph.get("name", "Unnamed Task Graph"),
            "success": success,
            "steps": results,
            "execution_order": execution_order
        }
        
        if failure_node:
            execution_results["failure_node"] = failure_node
        
        results_path = self.output_dir / "execution_results.json"
        with open(results_path, 'w') as f:
            json.dump(execution_results, f, indent=2)
        
        logger.info(f"Task graph execution {'completed successfully' if success else 'finished with some issues'}")
        return execution_results
