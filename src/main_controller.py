"""
Enhanced Anthropic Computer Use API Controller

This module provides a comprehensive interface to the Anthropic API for executing
Computer Use Actions (CUA) with support for:
- Full agent loop (sending tool results back to Claude)
- Executing bash commands in a controlled environment
- Error handling and logging
- Task graph execution (for bug reproduction)
- Test case execution
"""

import os
import json
import time
import logging
import subprocess
import anthropic
import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from dotenv import load_dotenv

# Import extraction utilities
from src.extraction.extract_wiki_content import extract_wiki_content

from src.utils.json_utils import save_json, load_json
from src.utils.logging_utils import setup_logging, create_run_logger

# Use enhanced logging from utils

class ComputerUseController:
    """Controller for Anthropic Computer Use Actions (CUA)."""
    
    def __init__(self, api_key=None, model='claude-3-7-sonnet-20250219', 
                 max_tokens=2048, thinking_budget=1024, log_level=logging.INFO,
                 log_dir=None, screenshot_dir=None):
        """Initialize the controller with the given parameters.
        
        Args:
            api_key (str, optional): Anthropic API key. If None, will be loaded from env vars.
            model (str): Anthropic model to use.
            max_tokens (int): Maximum number of tokens to generate in response.
            thinking_budget (int): Token budget for thinking steps.
            log_level (int): Logging level.
            log_dir (str, optional): Directory for logs. If None, uses default.
            screenshot_dir (str, optional): Directory for storing screenshots. If None, uses default.
        """
        # Set up enhanced logging
        if not log_dir:
            log_dir = 'logs/controller'
        os.makedirs(log_dir, exist_ok=True)
        self.logger = setup_logging('cua_controller', log_dir, log_level)
        self.logger.info('Initializing Computer Use Controller...')
        
        # Load API key from environment variables if not provided
        if not api_key:
            load_dotenv()
            api_key = os.getenv('ANTHROPIC_API_KEY')
            
        if not api_key:
            raise ValueError(
                'Anthropic API key not found. Please set the ANTHROPIC_API_KEY environment variable '
                'in a .env file or in your system environment.'
            )
        
        # Create the Anthropic client
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.thinking_budget = thinking_budget
        
        # Initialize conversation history
        self.conversation_history = []
        
        # Define available tools
        self.available_tools = [
            {
                'type': 'bash_20250124',
                'name': 'bash'
            }
        ]
        
        # Set screenshot directory
        if screenshot_dir:
            self.screenshot_dir = Path(screenshot_dir)
        else:
            self.screenshot_dir = Path('data/screenshots')
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info('Computer Use Controller initialized successfully')

    def execute_bash_command(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        """Execute a bash command in a controlled manner.
        
        Args:
            command (str): The bash command to execute.
            timeout (int): Command timeout in seconds.
            
        Returns:
            dict: Result containing stdout, stderr, and status.
        """
        self.logger.info(f"Executing bash command: {command}")
        
        try:
            # Security check - implement more safeguards in production
            if any(unsafe_cmd in command for unsafe_cmd in ['rm -rf', 'sudo', '> /dev/']):
                raise ValueError(f'Potentially unsafe command detected: {command}')
            
            # Execute command
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            # Format the output according to Anthropic's expected format for bash tool
            stdout = result.stdout.strip()
            stderr = result.stderr.strip()
            combined_output = stdout
            if stderr:
                if combined_output:
                    combined_output += f"\n{stderr}"
                else:
                    combined_output = stderr
                    
            # Simple output format for Anthropic API compatibility
            output = {
                "output": combined_output
            }
            
            log_level = logging.INFO if result.returncode == 0 else logging.ERROR
            self.logger.log(log_level, f"Command result: exit_code={result.returncode}")
            return output
            
        except subprocess.TimeoutExpired:
            self.logger.error(f"Command timed out after {timeout} seconds: {command}")
            return {
                "output": f"Command timed out after {timeout} seconds"
            }
        except Exception as e:
            self.logger.error(f"Error executing command: {e}")
            return {
                "output": f"Error executing command: {str(e)}"
            }
    
    def process_tool_use(self, tool_use):
        """Process a tool use request from Claude.
        
        Args:
            tool_use: The tool use request from Claude.
            
        Returns:
            dict: The result of the tool use.
        """
        try:
            if tool_use.name == "bash":
                command = tool_use.input.get("command", "")
                
                # Security check
                if any(unsafe_cmd in command for unsafe_cmd in ['rm -rf', 'sudo', '> /dev/']):
                    return {
                        "output": f"Error: Unsafe command detected: {command}",
                        "error": f"Unsafe command detected: {command}"
                    }
                
                # Special handling for saving text to a file
                if "extract_text" in command and ">" in command:
                    self.logger.info(f"Executing text extraction and saving: {command}")
                    # Let the command run as is, which allows redirection to files
                    result = subprocess.run(command, shell=True, capture_output=True, text=True)
                    
                    # Handle output file path extraction for logging
                    output_file = command.split(">")[-1].strip()
                    if result.returncode == 0:
                        self.logger.info(f"Text extraction saved to: {output_file}")
                        return {
                            "output": f"Text successfully extracted and saved to {output_file}\n{result.stdout}",
                            "exit_code": result.returncode
                        }
                    else:
                        self.logger.error(f"Text extraction failed: exit_code={result.returncode}")
                        return {
                            "output": f"Text extraction failed with exit code {result.returncode}\nStdout: {result.stdout}\nStderr: {result.stderr}",
                            "exit_code": result.returncode,
                            "error": result.stderr
                        }
                else:
                    # Normal command execution
                    self.logger.info(f"Executing bash command: {command}")
                    result = subprocess.run(command, shell=True, capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        self.logger.info(f"Command result: exit_code={result.returncode}")
                        return {
                            "output": f"{result.stdout}",
                            "exit_code": result.returncode
                        }
                    else:
                        self.logger.error(f"Command result: exit_code={result.returncode}")
                        return {
                            "output": f"Command failed with exit code {result.returncode}\nStdout: {result.stdout}\nStderr: {result.stderr}",
                            "exit_code": result.returncode,
                            "error": result.stderr
                        }
            elif tool_use.name == "wiki_extract":
                # Handle wiki extraction command
                try:
                    output_file = tool_use.input.get("output_file", os.path.join("data", "outputs", "wiki_content.json"))
                    
                    # Ensure output directory exists
                    os.makedirs(os.path.dirname(output_file), exist_ok=True)
                    
                    self.logger.info(f"Extracting Wikipedia content to {output_file}")
                    success = extract_wiki_content(output_file)
                    
                    if success:
                        return {
                            "output": f"Successfully extracted Wikipedia content to {output_file}",
                            "file_path": output_file
                        }
                    else:
                        return {
                            "output": "Failed to extract Wikipedia content",
                            "error": "Extraction failed"
                        }
                except Exception as e:
                    self.logger.error(f"Error during wiki extraction: {e}")
                    return {
                        "output": f"Error during wiki extraction: {str(e)}",
                        "error": str(e)
                    }
            else:
                return {
                    "output": f"Unknown tool: {tool_use.name}",
                    "error": f"Unknown tool: {tool_use.name}"
                }
        except Exception as e:
            self.logger.error(f"Error processing tool use: {e}")
            return {
                "output": f"Error: {str(e)}",
                "error": str(e)
            }
    
    def create_prompt_from_node(self, node: Dict[str, Any], task_graph: Dict[str, Any]) -> str:
        """Create a prompt for Claude based on a task graph node.
        
        Args:
            node: The task graph node to create a prompt from
            task_graph: The full task graph for context
            
        Returns:
            A prompt string for Claude
        """
        # Extract node information
        node_id = node.get("id", "unknown")
        node_type = node.get("type", "action")
        content = node.get("content", "")
        metadata = node.get("metadata", {})
        
        # Extract metadata elements
        ui_elements = metadata.get("ui_elements", [])
        inputs = metadata.get("inputs", [])
        expected_result = metadata.get("expected_result", "")
        image_refs = metadata.get("image_refs", [])
        
        # Build the prompt
        prompt = f"""I need you to perform a specific task on a computer using your CUA (Computer Use Agent) capabilities.
You are helping reproduce a bug in {task_graph.get('environment', {}).get('application', 'an application')}.

CURRENT TASK (Step {node_id}):
{content}

Please perform ONLY this specific step using your CUA capabilities. Do not move ahead to subsequent steps.
Be precise in your interactions with the UI elements specified.
"""
        
        return prompt
        
    def run_cua_action(self, prompt: str, conversation_history: List[Dict[str, Any]] = None) -> Tuple[bool, Any, List[Dict[str, Any]]]:
        """Run a CUA action with the given prompt and return the result.
        
        Args:
            prompt: The prompt to send to the assistant.
            conversation_history: Optional conversation history to include.
            
        Returns:
            Tuple of (success, response_content, updated_conversation)
        """
        self.logger.info(f"Running CUA action with prompt: {prompt[:50]}...")
        
        try:
            # Make a deep copy of the conversation history to avoid modifying the original
            import copy
            messages = copy.deepcopy(conversation_history) if conversation_history else []
            
            # Add the user prompt as a new message
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            # Get the initial response
            response = self.client.messages.create(
                model=self.model,
                messages=messages,
                max_tokens=4000,
                temperature=0.0,
                tools=self.available_tools
            )
            
            # Check if the assistant is requesting to use a tool
            has_tool_use = False
            tool_use_obj = None
            content_text = ""
            
            # Process response content
            for content_item in response.content:
                if content_item.type == "text":
                    content_text += content_item.text
                elif content_item.type == "tool_use":
                    has_tool_use = True
                    tool_use_obj = content_item
            
            # Add assistant's response to the conversation
            # This preserves the exact response format including any tool_use blocks
            messages.append({
                "role": "assistant",
                "content": response.content
            })
            
            # Check if there's a tool use request
            if has_tool_use:
                self.logger.info(f"Tool use request received: {tool_use_obj.name}")
                # Process the tool use
                tool_result = self.process_tool_use(tool_use_obj)
                
                # Convert tool result to a string format
                if isinstance(tool_result, dict) and "output" in tool_result:
                    tool_result_content = tool_result["output"]
                else:
                    # Fallback for other formats
                    tool_result_content = str(tool_result)
                
                self.logger.debug(f"Tool result content: {tool_result_content}")
                
                # Add tool result to conversation
                # The tool_result must reference the tool_use_id from the assistant's message
                messages.append({
                    "role": "user", 
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": tool_use_obj.id,
                        "content": tool_result_content
                    }]
                })
                
                # Get the final response
                final_response = self.client.messages.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=4000,
                    temperature=0.0,
                    tools=self.available_tools
                )
                
                # Add the final response to the conversation
                messages.append({
                    "role": "assistant",
                    "content": final_response.content
                })
                
                # Extract final text from the response
                final_text = ""
                for content_item in final_response.content:
                    if content_item.type == "text":
                        final_text += content_item.text
                
                return True, final_text, messages
            else:
                # No tool use, just return the text response
                return True, content_text, messages
        
        except Exception as e:
            self.logger.error(f"Error during CUA action: {e}")
            return False, {"error": str(e)}, messages
        
        self.logger.warning(f'Reached max iterations ({max_iterations})')
        return False, 'Reached maximum number of iterations', messages
    
    def run_test_case(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Run a test case with the Computer Use Agent.
        
        Args:
            test_case: Test case definition containing steps, validators, etc.
            
        Returns:
            dict: Test results with steps, screenshots, and validation results.
        """
        test_name = test_case.get('name', 'Unnamed Test')
        steps = test_case.get('steps', [])
        
        self.logger.info(f'Running test case: {test_name}')
        self.logger.info(f'Test case has {len(steps)} steps')
        
        results = {
            'name': test_name,
            'start_time': time.time(),
            'steps': [],
            'screenshots': [],
            'success': True,
            'messages': []
        }
        
        conversation_history = []
        
        # Execute each step in the test case
        for i, step in enumerate(steps):
            step_num = i + 1
            step_name = step.get('name', f'Step {step_num}')
            
            self.logger.info(f'Executing step {step_num}/{len(steps)}: {step_name}')
            
            # Get the action prompt for this step
            prompt = step.get('prompt', '')
            if not prompt:
                err_msg = f'No prompt defined for step {step_num}'
                self.logger.error(err_msg)
                results['steps'].append({
                    'step_num': step_num,
                    'name': step_name,
                    'success': False,
                    'error': err_msg
                })
                results['success'] = False
                continue
            
            # Run the CUA action
            success, response, updated_history = self.run_cua_action(prompt, conversation_history)
            conversation_history = updated_history
            
            # Record step results
            step_result = {
                'step_num': step_num,
                'name': step_name,
                'success': success,
                'response': response,
                'prompt': prompt
            }
            
            # Handle validation if specified
            if 'validation' in step and success:
                validation = step['validation']
                validation_type = validation.get('type', 'none')
                validation_params = validation.get('params', {})
                
                # Add validation logic here - will be expanded in validators.py
                # For now, just record that validation was requested
                step_result['validation_requested'] = {
                    'type': validation_type,
                    'params': validation_params
                }
            
            results['steps'].append(step_result)
            
            # If step failed, mark the test as failed but continue
            if not success:
                results['success'] = False
                results['messages'].append(f'Step {step_num} failed: {step_name}')
            
        # Record end time
        results['end_time'] = time.time()
        results['duration'] = results['end_time'] - results['start_time']
        
        self.logger.info(f'Test case complete: {test_name}')
        self.logger.info(f'Success: {results["success"]}')
        
        return results

def execute_task_graph(task_graph_path, output_dir=None, log_level=logging.INFO):
    """Execute a task graph using the CUA controller.
    
    Args:
        task_graph_path (str): Path to the task graph JSON file
        output_dir (str, optional): Directory to store execution results
        log_level (int): Logging level
        
    Returns:
        dict: Execution results with details on each step's execution
    """
    # Generate a run ID based on timestamp
    run_id = f"run_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Set up output directory
    if not output_dir:
        output_dir = Path(f"data/execution/{run_id}")
    else:
        output_dir = Path(output_dir) / run_id
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Set up logging
    logger = create_run_logger(run_id, str(output_dir.parent))
    logger.info(f"Starting task graph execution: {task_graph_path}")
    
    # Load task graph
    try:
        task_graph = load_json(task_graph_path)
        logger.info(f"Loaded task graph: {task_graph.get('name', 'Unnamed Task Graph')}")
    except Exception as e:
        logger.error(f"Failed to load task graph: {e}")
        return {
            "success": False,
            "error": f"Failed to load task graph: {e}",
            "run_id": run_id
        }
    
    # Initialize controller with screenshot directory in the output directory
    screenshot_dir = output_dir / "screenshots"
    controller = ComputerUseController(
        log_level=log_level,
        log_dir=str(output_dir / "logs"),
        screenshot_dir=str(screenshot_dir)
    )
    
    # Initialize results structure
    results = {
        "run_id": run_id,
        "task_graph": task_graph.get("name", "Unnamed Task Graph"),
        "start_time": datetime.datetime.now().isoformat(),
        "steps": [],
        "success": True,
        "screenshots": [],
        "output_dir": str(output_dir)
    }
    
    # Get nodes and edges from the task graph
    nodes = task_graph.get("task_graph", {}).get("nodes", [])
    edges = task_graph.get("task_graph", {}).get("edges", [])
    
    if not nodes:
        logger.error("Task graph contains no nodes")
        results["success"] = False
        results["error"] = "Task graph contains no nodes"
        return results
    
    # Create an execution order based on edges (simple linear path for now)
    execution_order = []
    
    # Check if there are edges to determine order
    if edges:
        # Start with the first node (usually id=1)
        current_id = edges[0].get("source")
        while current_id:
            execution_order.append(current_id)
            # Find the next node
            next_edge = next((edge for edge in edges if edge.get("source") == current_id), None)
            if next_edge:
                current_id = next_edge.get("target")
            else:
                # If this is the last node in the chain
                target = next((edge.get("target") for edge in edges if edge.get("source") == current_id), None)
                if target and target not in execution_order:
                    execution_order.append(target)
                break
    else:
        # If no edges, assume sequential order based on node IDs
        execution_order = [node.get("id") for node in nodes]
    
    logger.info(f"Execution order: {execution_order}")
    
    # Execute each node in order
    # We'll use a fresh conversation history for each step to avoid tool_use/tool_result mismatches
    for node_id in execution_order:
        # Reset conversation history for each step
        conversation_history = []
        
        # Find the corresponding node
        node = next((n for n in nodes if n.get("id") == node_id), None)
        if not node:
            logger.warning(f"Node with ID {node_id} not found in task graph")
            continue
        
        node_type = node.get("type", "action")
        content = node.get("content", "")
        metadata = node.get("metadata", {})
        
        logger.info(f"Executing step {node_id}: {content[:50]}{'...' if len(content) > 50 else ''}")
        
        # Create prompt for Claude based on the node content and metadata
        prompt = controller.create_prompt_from_node(node, task_graph)
        
        # Log the prompt
        prompt_log_path = output_dir / "prompts" / f"step_{node_id}_prompt.txt"
        os.makedirs(prompt_log_path.parent, exist_ok=True)
        with open(prompt_log_path, "w") as f:
            f.write(prompt)
        
        # Run the CUA action
        step_start_time = datetime.datetime.now()
        success, response, _ = controller.run_cua_action(prompt, conversation_history)
        step_end_time = datetime.datetime.now()
        
        # Take a screenshot after the action (if implemented)
        screenshot_path = None
        try:
            if hasattr(controller, 'take_screenshot') and callable(controller.take_screenshot):
                screenshot_filename = f"step_{node_id}_screenshot.png"
                screenshot_path = controller.take_screenshot(str(screenshot_dir / screenshot_filename))
                if screenshot_path:
                    results["screenshots"].append(screenshot_path)
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            screenshot_path = None
        
        # Record step results
        step_result = {
            "step_id": node_id,
            "type": node_type,
            "content": content,
            "success": success,
            "start_time": step_start_time.isoformat(),
            "end_time": step_end_time.isoformat(),
            "duration": (step_end_time - step_start_time).total_seconds(),
            "prompt": prompt,
            "response": response,
            "screenshot": screenshot_path
        }
        
        # Log Claude's response
        response_log_path = output_dir / "responses" / f"step_{node_id}_response.json"
        os.makedirs(response_log_path.parent, exist_ok=True)
        save_json(response, str(response_log_path))
        
        results["steps"].append(step_result)
        
        # If a step fails, mark the overall execution as failed but continue
        if not success:
            results["success"] = False
            results["failure_step"] = node_id
            logger.warning(f"Step {node_id} failed: {response}")
            
            # Check if we should continue on failure (default: stop on first failure)
            # For now, we'll implement a simple linear execution that stops on failure
            logger.info("Stopping execution due to step failure")
            break
    
    # Record end time and save results
    results["end_time"] = datetime.datetime.now().isoformat()
    results["duration"] = (datetime.datetime.fromisoformat(results["end_time"]) - 
                           datetime.datetime.fromisoformat(results["start_time"])).total_seconds()
    
    # Save execution results
    results_path = output_dir / "execution_results.json"
    save_json(results, str(results_path))
    logger.info(f"Execution results saved to: {results_path}")
    
    return results

def main():
    """Main function showcasing the enhanced CUA controller."""
    try:
        # Create controller
        controller = ComputerUseController()
        
        # Simple example of running a CUA action
        prompt = "Open a web browser and navigate to https://example.com"
        success, response, _ = controller.run_cua_action(prompt)
        
        if success:
            print("CUA action completed successfully!")
        else:
            print(f"CUA action failed: {response}")
            
    except Exception as e:
        print(f"Error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
