# Building Dynamic Task Graph Execution with Computer Use

## Implementation Overview

Our approach to enhancing the Computer Use Agent's task graph execution capabilities involves:

1. Creating a **separate and robust EnhancedTaskGraphExecutor** to maintain stability while developing new features
2. Leveraging Claude's vision capabilities to **analyze screenshots** for better context awareness
3. Implementing **subtask generation and verification** with visual evidence
4. Building a **debugging framework** to test and validate the new functionality

## Implementation Architecture

We implemented a new approach that creates a parallel, enhanced task graph execution system while preserving the existing functionality:

### Key Components

1. **EnhancedTaskGraphExecutor**
   - Dedicated class for improved task graph execution
   - Built with extensive logging and debugging capabilities
   - Handles screenshots, subtask generation, and verification

2. **EnhancedAnthropicClient**
   - Extends the existing AnthropicClient with image handling
   - Provides methods for generating responses based on screenshots
   - Includes retry logic and error handling

3. **Debug Framework**
   - Command-line tool for testing task graph execution
   - Supports executing individual nodes or entire task graphs
   - Generates detailed logs and output for analysis

### Dependencies

The implementation requires the following dependencies:

```bash
pip install python-dotenv anthropic pillow pyscreenshot
```

## Implementation Details

### Enhanced Task Graph Executor

The `EnhancedTaskGraphExecutor` is the core component of our implementation. It provides the following key functionality:

1. **Task Graph Execution**: Executes a task graph by processing nodes in the correct order based on dependencies.
2. **Subtask Generation**: Breaks down complex tasks into smaller, manageable subtasks using Claude's vision capabilities.
3. **Subtask Execution**: Provides guidance for executing each subtask based on the current screen state.
4. **Verification**: Verifies subtask completion using visual evidence.
5. **Detailed Logging**: Maintains comprehensive logs of the execution process.

### Key Methods

#### 1. Subtask Generation

The `_generate_subtasks` method uses Claude to analyze a screenshot of the current state and generate specific, detailed subtasks.

#### 2. Subtask Verification

The `_verify_subtask_completion` method verifies if a subtask was completed successfully using visual evidence.

#### 3. Screenshot Handling

The `_take_screenshot` method captures the current screen state with multiple fallback mechanisms for different platforms.

### Enhanced Anthropic Client

The `EnhancedAnthropicClient` extends the base client with image handling capabilities:

```python
def generate_with_image(self, prompt: str, image_base64: str, system_prompt: str = None) -> str:
    """Generate a response from Claude using a text prompt and an image."""
    # Sends both text and image to Claude and returns the response
```

## Usage Guide

### Setting Up the Environment

1. **Install required dependencies**:
   ```bash
   pip install python-dotenv anthropic pillow pyscreenshot
   ```

2. **Set your Anthropic API key**:
   ```bash
   export ANTHROPIC_API_KEY="your-api-key-here"
   ```
   Or create a `.env` file with your API key:
   ```
   ANTHROPIC_API_KEY=your-api-key-here
   ```

4. **Add a helper method to convert images to base64**

   ```python
   def _get_image_base64(self, image_path: str) -> str:
       """Convert an image to base64 encoding.
       
       Args:
           image_path: Path to the image.
           
       Returns:
           Base64-encoded image data.
       """
       try:
           with open(image_path, 'rb') as image_file:
               return base64.b64encode(image_file.read()).decode('utf-8')
       except Exception as e:
           self.logger.error(f"Error encoding image to base64: {e}")
           return ""
   ```

### Phase 3: Update the Node Execution Logic

1. **Modify the `_execute_node` method to use dynamic subtasks**

   ```python
   def _execute_node(self, node: Dict[str, Any], previous_steps: List[Dict[str, Any]]) -> Dict[str, Any]:
       """Execute a task graph node with subtask generation and verification.
       
       Args:
           node: Task graph node to execute.
           previous_steps: List of previous step results.
           
       Returns:
           Node execution result.
       """
       node_id = node["id"]
       node_content = node["content"]
       
       self.logger.info(f"Executing node {node_id}: {node_content}")
       
       # Create state context from previous steps
       state_context = self._create_state_context(previous_steps)
       
       # Generate subtasks for this node
       subtasks = self._generate_subtasks(node, state_context)
       
       if not subtasks:
           self.logger.warning(f"No subtasks generated for node {node_id}")
           subtasks = [{
               "id": 1,
               "description": node_content,
               "verification": "Task has been completed",
               "ui_elements": []
           }]
       
       # Save subtasks for reference
       subtasks_file = self.subtasks_dir / f"node_{node_id}_subtasks.json"
       save_json({"node_id": node_id, "subtasks": subtasks}, str(subtasks_file))
       
       # Create prompt for this node with subtasks
       prompt = self._create_node_prompt(node, subtasks, state_context)
       
       # Save the prompt
       prompt_file = self.prompts_dir / f"node_{node_id}_prompt.txt"
       with open(prompt_file, "w") as f:
           f.write(prompt)
       
       # Take a screenshot before execution
       screenshot_path = self.screenshots_dir / f"node_{node_id}_before.png"
       self._take_screenshot(str(screenshot_path))
       
       # Execute the node
       result = self._execute_agent_loop(node_id, prompt)
       
       # Save the result
       response_file = self.responses_dir / f"node_{node_id}_response.json"
       save_json(result, str(response_file))
       
       # Take a screenshot after execution
       screenshot_path = self.screenshots_dir / f"node_{node_id}_after.png"
       self._take_screenshot(str(screenshot_path))
       
       # Verify each subtask
       all_subtasks_completed = True
       verified_subtasks = []
       
       for subtask in subtasks:
           # Take a screenshot for verification
           screenshot_path = self.screenshots_dir / f"node_{node_id}_subtask_{subtask['id']}_verification.png"
           self._take_screenshot(str(screenshot_path))
           
           # Verify the subtask
           is_completed = self._verify_subtask_completion(subtask, node_id, str(screenshot_path))
           
           subtask_result = {
               "id": subtask["id"],
               "description": subtask["description"],
               "completed": is_completed
           }
           verified_subtasks.append(subtask_result)
           
           if not is_completed:
               all_subtasks_completed = False
       
       # Determine overall success
       success = self._check_task_completion(result) and all_subtasks_completed
       
       # Save extracted content if successful
       if success:
           self._save_extracted_content(node_id, node_content, result)
       
       return {
           "step_id": node_id,
           "content": node_content,
           "success": success,
           "subtasks": verified_subtasks,
           "thinking": result.get("thinking", None)
       }
   ```

2. **Update the prompt creation method for better subtask handling**

   ```python
   def _create_node_prompt(self, node: Dict[str, Any], subtasks: List[Dict[str, Any]], state_context: str) -> str:
       """Create a prompt for node execution with subtasks.
       
       Args:
           node: Task graph node.
           subtasks: List of subtasks for the node.
           state_context: State context from previous steps.
           
       Returns:
           Prompt for node execution.
       """
       node_id = node["id"]
       node_content = node["content"]
       node_type = node.get("type", "action")
       
       # Get metadata
       metadata = node.get("metadata", {})
       image_refs = metadata.get("image_refs", [])
       ui_elements = metadata.get("ui_elements", [])
       inputs = metadata.get("inputs", [])
       expected_result = metadata.get("expected_result", "")
       
       # Construct prompt
       prompt = f"""# Task Execution: Node {node_id}

       ## Main Task
       {node_content}

       ## Current Environment State
       {state_context}

       ## Subtasks to Complete
       """
       
       # Add subtasks
       for subtask in subtasks:
           prompt += f"""
       ### Subtask {subtask['id']}: {subtask['description']}
       - Verification: {subtask['verification']}
       """
           if 'ui_elements' in subtask and subtask['ui_elements']:
               prompt += f"- UI Elements: {', '.join(subtask['ui_elements'])}\n"
       
       # Add additional metadata if available
       if expected_result:
           prompt += f"""
       ## Expected Result
       {expected_result}
       """
       
       if ui_elements:
           prompt += f"""
       ## UI Elements to Interact With
       {', '.join(ui_elements)}
       """
       
       if inputs:
           prompt += f"""
       ## Inputs to Provide
       {', '.join(inputs)}
       """
       
       # Add instructions
       prompt += """
       ## Instructions
       1. Execute each subtask in order.
       2. After each subtask, verify it was completed successfully.
       3. Report any issues or difficulties encountered.
       4. Take screenshots at key points to document the execution.
       5. When all subtasks are complete, report the overall completion status.
       
       Let's start executing these subtasks one by one.
       """
       
       return prompt
   ```

### Phase 4: Test and Debug the Implementation

1. **Update `run_chrome_search.py` to use the enhanced executor**

   ```python
   # Use debug logging to see detailed execution steps
   executor = TaskGraphExecutor(
       output_dir=str(output_dir),
       api_key=os.environ.get("ANTHROPIC_API_KEY"),
       model=args.model,
       log_level=logging.DEBUG
   )
   ```

2. **Add a new test script for step-by-step debugging**

   Create a new file `debug_task_execution.py`:

   ```python
   #!/usr/bin/env python3
   """
   Debug script for task graph execution with detailed logging.
   
   This script runs a task graph with maximum verbosity to help debug
   any issues with subtask generation and verification.
   """
   
   import os
   import sys
   import logging
   from pathlib import Path
   from dotenv import load_dotenv
   
   from src.task_execution import TaskGraphExecutor
   
   # Set up logging
   logging.basicConfig(
       level=logging.DEBUG,
       format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
       handlers=[
           logging.FileHandler("debug_execution.log"),
           logging.StreamHandler()
       ]
   )
   
   logger = logging.getLogger("debug_execution")
   
   def main():
       """Debug task graph execution."""
       # Load environment variables
       load_dotenv()
       
       # Check API key
       if "ANTHROPIC_API_KEY" not in os.environ:
           logger.error("ANTHROPIC_API_KEY environment variable is not set")
           sys.exit(1)
       
       # Set up paths
       task_graph_path = "data/task_graphs/chrome_search_task_graph.json"
       output_dir = f"data/outputs/debug_execution_{int(time.time())}"
       
       # Create executor with debug logging
       executor = TaskGraphExecutor(
           output_dir=output_dir,
           model="claude-3-sonnet-20240229",  # Use stable model for debugging
           log_level=logging.DEBUG
       )
       
       # Execute one node at a time
       try:
           # Load task graph
           task_graph = json.loads(Path(task_graph_path).read_text())
           nodes = task_graph.get("task_graph", {}).get("nodes", [])
           
           if not nodes:
               logger.error("Task graph contains no nodes")
               return 1
           
           # Execute just the first node
           first_node = nodes[0]
           logger.info(f"Executing only first node: {first_node['id']}")
           
           result = executor._execute_node(first_node, [])
           
           # Print result
           print("\nNode execution result:")
           print(f"Success: {result['success']}")
           print(f"Subtasks: {len(result['subtasks'])}")
           
           for subtask in result['subtasks']:
               status = "✅" if subtask['completed'] else "❌"
               print(f"  {status} {subtask['description']}")
           
           return 0
       
       except Exception as e:
           logger.exception(f"Error debugging task execution: {e}")
           return 1
   
   if __name__ == "__main__":
       sys.exit(main())
   ```

3. **Run the debug script to test the implementation**

   ```bash
   python debug_task_execution.py
   ```

### Phase 5: Final Integration and Clean-up

1. **Update any remaining hardcoded values**

   - Ensure all tool versions are properly mapped to models
   - Check for hardcoded paths and replace with configuration
   - Review and update any prompt templates

2. **Document the enhanced solution**

   - Create a `README.md` with usage instructions
   - Document the subtask generation and verification process
   - Include example task graphs and expected outputs

3. **Create a comprehensive test framework**

   - Test with different task graphs
   - Test with different models
   - Test with different verification criteria
   - Report metrics on success rates

## Summary of Modifications

The key enhancements we're making to the existing codebase are:

1. **Dynamic subtask generation** using Claude with visual context
2. **Structured subtask parsing** with verification criteria
3. **Visual verification of subtask completion** after each step
4. **Improved prompt engineering** for better agent guidance
5. **Comprehensive debugging and logging** for easier troubleshooting

This approach gives you the benefits of:
- Leveraging the existing stable task graph structure
- Reusing the proven rate limit handling
- Adding the missing dynamic subtask generation
- Implementing visual verification for each step
- Maintaining a structured output for analysis

These changes will transform your current system into a fully dynamic task graph execution engine that can adapt to different environments and provide verified completion of each subtask.
