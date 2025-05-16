# Anthropic Computer Use Taskgraph Integration: Implementation Plan

This document provides a step-by-step guide to implement the integration between your taskgraph system and Anthropic's Computer Use agent. Each step includes implementation guidance and test criteria to ensure incremental progress.

## Phase 1: Environment Setup (Already Completed)

✅ Clone the Anthropic quickstarts repository
✅ Configure environment with API key
✅ Run the Computer Use demo container
✅ Test basic functionality (as shown in your recent test with Larry Ellison search)
✅ Update task graph JSON to use Firefox instead of Chrome

## Phase 2: Building the TaskGraph Integrator

### Step 1: Create Basic Integrator Framework

```python
# File: task_graph_integrator.py

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("task_graph_integration")

class TaskGraphIntegrator:
    """Integrates task graphs with Anthropic's Computer Use reference implementation."""
    
    def __init__(self, output_dir: str, model: str = "claude-3-7-sonnet-20240620", 
                 thinking_budget: int = 1024):
        self.model = model
        self.thinking_budget = thinking_budget
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
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
```

**Test 1:** Verify the class initializes without errors and creates the expected directories

### Step 2: Implement Task Graph Loading

Add methods to load and parse task graph JSON files:

```python
def load_task_graph(self, task_graph_path: str) -> Dict[str, Any]:
    """Load a task graph from a JSON file.
    
    Args:
        task_graph_path: Path to the task graph JSON file
        
    Returns:
        Parsed task graph as a dictionary
    """
    # Load task graph
    with open(task_graph_path, 'r') as f:
        task_graph = json.load(f)
    
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
```

**Test 2:** Load your Firefox task graph JSON and verify it creates the correct execution order

### Step 3: Implement Node-to-Prompt Conversion

This is one of the key components - converting a task graph node into an effective prompt for Claude:

```python
def create_node_prompt(self, node: Dict[str, Any], state_context: List[Dict[str, Any]]) -> str:
    """Create a prompt for node execution.
    
    Args:
        node: Task graph node
        state_context: Context from previous nodes
        
    Returns:
        Prompt for the Computer Use Agent
    """
    content = node.get("content", "")
    node_type = node.get("type", "action")
    metadata = node.get("metadata", {})
    
    # Extract metadata
    ui_elements = metadata.get("ui_elements", [])
    expected_result = metadata.get("expected_result", "")
    image_refs = metadata.get("image_refs", [])
    inputs = metadata.get("inputs", [])
    
    # Create UI elements text
    ui_elements_text = ""
    if ui_elements:
        ui_elements_text = "UI Elements to interact with:\n"
        for element in ui_elements:
            ui_elements_text += f"- {element}\n"
    
    # Create inputs text
    inputs_text = ""
    if inputs:
        inputs_text = "Input values to use:\n"
        for input_value in inputs:
            inputs_text += f"- {input_value}\n"
    
    # Create verification text
    verification_text = ""
    if expected_result:
        verification_text = f"Expected Result: {expected_result}\n"
    
    # Create image references text
    image_refs_text = ""
    if image_refs:
        image_refs_text = "Reference Images (not provided directly, but mentioned for context):\n"
        for image_ref in image_refs:
            image_refs_text += f"- {image_ref}\n"
    
    # Context from previous steps
    context_text = ""
    if state_context:
        context_text = "Previously completed steps:\n"
        for ctx in state_context:
            status = "✅ Completed successfully" if ctx.get("success") else "❌ Failed"
            context_text += f"- Step {ctx.get('node_id')}: {ctx.get('content')[:50]}... - {status}\n"
    
    # Task type
    task_type = "verification task" if node_type == "verification" else "computer task"
    verification_instructions = ""
    if node_type == "verification":
        verification_instructions = "\nThis is a VERIFICATION step. Focus on checking and confirming the expected results rather than performing new actions."
    
    # Create the prompt
    prompt = f"""I need your help to complete a {task_type} using Firefox. Please follow these instructions carefully:{verification_instructions}

# Task
{content}

{ui_elements_text}
{inputs_text}
{verification_text}
{image_refs_text}
{context_text}

# Instructions
1. Break down this task into clear, specific subtasks.
2. After each subtask, take a screenshot and carefully evaluate if you've achieved the right outcome.
3. Explicitly show your thinking: "I have evaluated subtask X..."
4. If a subtask wasn't completed correctly, try again with a different approach.
5. Only when you confirm a subtask was executed correctly should you move on to the next one.
6. If you encounter dropdowns or scrollbars that are difficult to manipulate, try using keyboard shortcuts.
7. At the end, verify that the entire task has been completed successfully according to the expected result.

Please complete this task step by step, showing your work and verification at each stage.
"""
    
    # Add verification criteria for verification nodes
    if node_type == "verification":
        prompt += "\n# Verification Criteria\nBe thorough in your verification. Explicitly state whether each aspect of the expected result has been confirmed and provide evidence via screenshots."
    
    return prompt
```

**Test 3:** Generate prompts for a few different nodes and verify they include all necessary context and instructions

### Step 4: Integrate with Anthropic's Agent Loop

This is where we connect to the Anthropic Computer Use agent loop:

```python
# IMPORTANT: Import these at the top of your file
import sys
import httpx
from pathlib import Path

# Add the computer_use_demo package to the Python path
computer_use_demo_path = Path('/path/to/anthropic-quickstarts/computer-use-demo')
sys.path.append(str(computer_use_demo_path))

from computer_use_demo.loop import sampling_loop
from computer_use_demo.tools import TOOL_GROUPS_BY_VERSION, ToolCollection

async def execute_node(self, node: Dict[str, Any], state_context: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Execute a task graph node using the Computer Use Agent.
    
    Args:
        node: Task graph node
        state_context: Context from previous nodes
        
    Returns:
        Node execution result
    """
    node_id = node.get("id", "unknown")
    prompt = self.create_node_prompt(node, state_context)
    
    # Save prompt
    prompt_path = self.prompts_dir / f"node_{node_id}_prompt.txt"
    with open(prompt_path, 'w') as f:
        f.write(prompt)
    
    # Initialize messages for the agent loop
    messages = [{"role": "user", "content": prompt}]
    
    # Run the agent loop
    try:
        # Version and tool settings
        tool_version = "20250124"  # For Claude 3.7 Sonnet
        
        # Track messages and outputs
        output_messages = []
        
        def output_callback(block):
            output_messages.append(block)
        
        def tool_output_callback(result, tool_use_id):
            # Log tool outputs to help with debugging
            logger.debug(f"Tool output for {tool_use_id}: {result}")
        
        def api_response_callback(request, response, error):
            # Log API interactions
            if error:
                logger.error(f"API error: {error}")
        
        # Run the agent loop from the reference implementation
        final_messages = await sampling_loop(
            model=self.model,
            provider="anthropic",  # Using direct Anthropic API
            system_prompt_suffix="",  # No additional system prompt
            messages=messages,
            output_callback=output_callback,
            tool_output_callback=tool_output_callback,
            api_response_callback=api_response_callback,
            api_key=self.api_key,
            thinking_budget=self.thinking_budget,
            tool_version=tool_version,
            max_tokens=4096
        )
        
        # Extract the final response
        response_text = ""
        for msg in final_messages:
            if msg.get("role") == "assistant" and isinstance(msg.get("content"), list):
                for content_item in msg.get("content", []):
                    if isinstance(content_item, dict) and content_item.get("type") == "text":
                        response_text += content_item.get("text", "")
        
        # Save response
        response_path = self.responses_dir / f"node_{node_id}_response.json"
        with open(response_path, 'w') as f:
            json.dump({"response": response_text, "full_messages": final_messages}, f, indent=2)
        
        # Determine success based on response
        success_phrases = [
            "successfully completed",
            "task complete",
            "completed successfully",
            "successfully",
            "task has been completed"
        ]
        success = any(phrase in response_text.lower() for phrase in success_phrases)
        
        return {
            "id": node_id,
            "content": node.get("content", ""),
            "success": success,
            "response": response_text,
            "prompt_file": str(prompt_path),
            "response_file": str(response_path)
        }
        
    except Exception as e:
        logger.error(f"Error executing node {node_id}: {e}")
        return {
            "id": node_id,
            "content": node.get("content", ""),
            "success": False,
            "error": str(e),
            "prompt_file": str(prompt_path)
        }
```

**Test 4:** Execute a single simple node and verify it completes successfully with the agent

### Step 5: Implement Full Task Graph Execution

Now tie everything together to execute the entire task graph:

```python
async def execute_task_graph(self, task_graph_path: str) -> Dict[str, Any]:
    """Execute a task graph using Anthropic's Computer Use Agent.
    
    Args:
        task_graph_path: Path to the task graph JSON file
        
    Returns:
        Execution results
    """
    # Load task graph
    task_graph = self.load_task_graph(task_graph_path)
    
    # Get nodes and edges
    nodes = task_graph.get("task_graph", {}).get("nodes", [])
    edges = task_graph.get("task_graph", {}).get("edges", [])
    
    if not nodes:
        logger.error("Task graph contains no nodes")
        return {"success": False, "error": "Task graph contains no nodes"}
    
    # Create execution order
    execution_order = self.create_execution_order(nodes, edges)
    logger.info(f"Execution order: {execution_order}")
    
    # Execute each node
    results = {
        "task_graph": task_graph.get("name", "Unnamed Task Graph"),
        "steps": [],
        "success": True
    }
    
    # Track context
    state_context = []
    
    for node_id in execution_order:
        # Find node
        node = next((n for n in nodes if n.get("id") == node_id), None)
        if not node:
            logger.warning(f"Node with ID {node_id} not found in task graph")
            continue
        
        # Execute node
        logger.info(f"Executing node {node_id}: {node.get('content', '')[:50]}...")
        node_result = await self.execute_node(node, state_context)
        
        # Add to results
        results["steps"].append(node_result)
        
        # Update context
        state_context.append({
            "node_id": node_id,
            "content": node.get("content", ""),
            "success": node_result.get("success", False)
        })
        
        # Check for failure
        if not node_result.get("success", False):
            results["success"] = False
            results["failure_node"] = node_id
            break
    
    # Save results
    results_path = self.output_dir / "execution_results.json"
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Task graph execution completed. Results saved to: {results_path}")
    return results
```

**Test 5:** Execute the Firefox search task graph and verify it works end-to-end

## Phase 3: Enhanced Features and Improvements

### Step 6: Add Improved Verification Logic

Enhance the success detection with more sophisticated verification:

```python
def determine_success(self, response_text: str, expected_result: str, screenshot_count: int) -> bool:
    """
    More sophisticated success detection based on response analysis.
    
    Args:
        response_text: Claude's response text
        expected_result: Expected result from node metadata
        screenshot_count: Number of screenshots taken
        
    Returns:
        Boolean indicating success
    """
    # Basic success phrases
    success_phrases = [
        "successfully completed",
        "task complete",
        "completed successfully",
        "successfully",
        "task has been completed",
        "verification successful",
        "verified successfully"
    ]
    
    # Check if any success phrase is in the response
    phrase_match = any(phrase in response_text.lower() for phrase in success_phrases)
    
    # Check if expected result is mentioned
    result_keywords = [kw.lower() for kw in expected_result.split() if len(kw) > 3]
    result_match = all(kw in response_text.lower() for kw in result_keywords)
    
    # Check for screenshots (verification should include visual evidence)
    has_screenshots = screenshot_count > 0
    
    # Check for failure indicators
    failure_phrases = [
        "unable to complete",
        "could not complete",
        "failed to",
        "was not successful",
        "verification failed"
    ]
    has_failure = any(phrase in response_text.lower() for phrase in failure_phrases)
    
    # Logic to determine success
    if has_failure:
        return False
    
    if phrase_match and result_match and has_screenshots:
        return True
    
    if phrase_match and has_screenshots:
        return True
    
    return False
```

**Test 6:** Verify the enhanced success detection with different node responses

### Step 7: Implement Retry Logic for Failed Nodes

Add the ability to retry failed nodes with modified prompts:

```python
async def execute_node_with_retries(self, node: Dict[str, Any], state_context: List[Dict[str, Any]], 
                               max_retries: int = 2) -> Dict[str, Any]:
    """Execute a node with retry logic.
    
    Args:
        node: Task graph node
        state_context: Context from previous nodes
        max_retries: Maximum number of retry attempts
        
    Returns:
        Node execution result
    """
    node_id = node.get("id", "unknown")
    
    for attempt in range(max_retries + 1):
        if attempt > 0:
            logger.info(f"Retry attempt {attempt} for node {node_id}")
            
        # Execute node
        result = await self.execute_node(node, state_context)
        
        if result.get("success", False):
            return result
        
        # If this was the last attempt, return the result
        if attempt == max_retries:
            return result
        
        # Modify the node to create a better prompt for retry
        # Add information about the previous failure
        if "metadata" not in node:
            node["metadata"] = {}
        
        if "retry_info" not in node["metadata"]:
            node["metadata"]["retry_info"] = []
            
        node["metadata"]["retry_info"].append({
            "attempt": attempt + 1,
            "previous_error": result.get("error", "Unknown error")
        })
    
    # This should never be reached, but just in case
    return {"id": node_id, "success": False, "error": "Max retries exceeded"}
```

**Test 7:** Verify retry logic works by intentionally interrupting a node execution

### Step 8: Command Line Interface

Create a CLI for easy execution of task graphs:

```python
async def main():
    """Run a task graph with Anthropic's Computer Use Agent."""
    import argparse
    import time
    import asyncio
    
    # Parse arguments
    parser = argparse.ArgumentParser(description="Run a task graph with Anthropic's Computer Use Agent")
    parser.add_argument(
        "--task-graph",
        default="data/task_graphs/firefox_larry_ellison_search.json",
        help="Path to task graph JSON file"
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory for execution results"
    )
    parser.add_argument(
        "--model",
        default="claude-3-7-sonnet-20240620",
        help="Anthropic model to use (must support computer_use)"
    )
    parser.add_argument(
        "--thinking-budget",
        type=int,
        default=1024,
        help="Token budget for thinking content"
    )
    parser.add_argument(
        "--node-id",
        default=None,
        help="ID of specific node to execute (if not provided, executes entire task graph)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Set up logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Set output directory
    output_dir = args.output_dir or f"data/outputs/run_{int(time.time())}"
    
    # Create integrator
    integrator = TaskGraphIntegrator(
        output_dir=output_dir,
        model=args.model,
        thinking_budget=args.thinking_budget
    )
    
    try:
        # Execute task graph or specific node
        if args.node_id:
            # Load task graph
            task_graph = integrator.load_task_graph(args.task_graph)
            
            # Find node
            nodes = task_graph.get("task_graph", {}).get("nodes", [])
            node = next((n for n in nodes if n.get("id") == args.node_id), None)
            
            if not node:
                print(f"Node with ID {args.node_id} not found in task graph")
                return 1
            
            # Execute node
            print(f"Executing single node: {args.node_id}")
            result = await integrator.execute_node(node, [])
            
            # Print result
            print(f"\nNode execution result:")
            print(f"ID: {result.get('id')}")
            print(f"Content: {result.get('content')[:50]}...")
            print(f"Success: {result.get('success')}")
            
            if "error" in result:
                print(f"Error: {result.get('error')}")
            
            print(f"\nFull response saved to: {result.get('response_file')}")
            
        else:
            # Execute full task graph
            print("Executing full task graph")
            result = await integrator.execute_task_graph(args.task_graph)
            
            # Print result
            print(f"\nTask graph execution result:")
            print(f"Task graph: {result.get('task_graph')}")
            print(f"Success: {result.get('success')}")
            
            print(f"\nSteps:")
            for step in result.get("steps", []):
                status = "✅" if step.get("success") else "❌"
                print(f"  {status} {step.get('id')}: {step.get('content')[:50]}...")
                
                if "error" in step:
                    print(f"     Error: {step.get('error')}")
            
            if not result.get("success") and "failure_node" in result:
                print(f"\nFailure at node: {result.get('failure_node')}")
            
            print(f"\nDetailed results saved to: {output_dir}")
        
        return 0
        
    except Exception as e:
        logger.exception(f"Error running task graph: {e}")
        return 1

if __name__ == "__main__":
    import asyncio
    sys.exit(asyncio.run(main()))
```

**Test 8:** Verify the CLI works for both full task graph execution and single node execution

## Phase 4: Advanced Enhancements

### Step 9: Web Interface for Monitoring

You can create a simple Streamlit app to monitor task graph execution:

```python
# monitoring_app.py
import streamlit as st
import json
import os
from pathlib import Path
import time

def main():
    st.title("Task Graph Execution Monitor")
    
    # Find output directories
    outputs_dir = Path("data/outputs")
    output_dirs = sorted([d for d in outputs_dir.glob("run_*")], key=lambda x: x.stat().st_mtime, reverse=True)
    
    if not output_dirs:
        st.warning("No task graph executions found. Run a task graph first.")
        return
    
    # Select an execution to view
    selected_run = st.selectbox(
        "Select run to view:",
        options=output_dirs,
        format_func=lambda x: f"{x.name} - {time.ctime(x.stat().st_mtime)}"
    )
    
    if not selected_run:
        return
    
    # Load execution results
    results_path = selected_run / "execution_results.json"
    if not results_path.exists():
        st.error(f"Results file not found at {results_path}")
        return
    
    with open(results_path, 'r') as f:
        results = json.load(f)
    
    # Display execution summary
    st.header("Execution Summary")
    status = "✅ Success" if results.get("success") else "❌ Failed"
    st.subheader(f"Task Graph: {results.get('task_graph')} - {status}")
    
    if not results.get("success") and "failure_node" in results:
        st.error(f"Failed at node: {results.get('failure_node')}")
    
    # Display steps
    st.header("Steps")
    for step in results.get("steps", []):
        with st.expander(f"Node {step.get('id')}: {step.get('content')[:50]}..."):
            status = "✅ Success" if step.get("success") else "❌ Failed"
            st.write(f"Status: {status}")
            
            # Display prompt
            st.subheader("Prompt")
            prompt_file = step.get("prompt_file")
            if prompt_file and os.path.exists(prompt_file):
                with open(prompt_file, 'r') as f:
                    st.code(f.read())
            
            # Display response
            st.subheader("Response")
            response_file = step.get("response_file")
            if response_file and os.path.exists(response_file):
                with open(response_file, 'r') as f:
                    response_data = json.load(f)
                    st.write(response_data.get("response", ""))
            
            # Display error if any
            if "error" in step:
                st.error(f"Error: {step.get('error')}")

if __name__ == "__main__":
    main()
```

**Test 9:** Run the monitoring app to visualize task graph execution results

### Step 10: Integration with Existing Task Graph System

This step depends on your specific task graph system, but the approach would be:

1. Import your task graph executor
2. Use its API to load and manage task graphs
3. Call the Anthropic Computer Use agent using the methods above for node execution

## Testing Guidelines

For each step:

1. **Unit Tests**: Test individual functions with known inputs
2. **Integration Tests**: Test the interaction between your components
3. **System Tests**: Run complete task graphs in the Docker environment
4. **Error Handling Tests**: Deliberately introduce errors to test recovery

## Important Notes

1. **Dockerized Environment**: Remember that the code is running in a Docker container with Firefox installed
2. **Asynchronous Execution**: The Anthropic agent loop uses asyncio, so maintain async patterns
3. **API Key Security**: Keep your API key secure, especially in logs
4. **Error Handling**: Computer use sessions may fail for various reasons, so robust error handling is critical
5. **Prompt Engineering**: The quality of node-to-prompt conversion greatly affects success rate

By following this plan and testing at each step, you'll build a robust integration between your taskgraph system and Anthropic's Computer Use capabilities.
