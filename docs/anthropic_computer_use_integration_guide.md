# Anthropic Computer Use Integration Guide

This guide outlines the steps to implement Anthropic's Computer Use Agent MVP using their reference implementation and integrating it with our task graph system.

## Overview

Instead of implementing the computer use capabilities from scratch, we'll leverage Anthropic's official reference implementation and then integrate it with our task graph execution system. This approach has several advantages:

1. **Reliability**: The reference implementation has been built and tested by Anthropic
2. **Completeness**: Includes all necessary tools and setup for browser automation
3. **Containerization**: Provides a controlled environment with all dependencies

## Phase 1: Setting Up the Reference Implementation

### 1. Clone the Repository

```bash
git clone https://github.com/anthropics/anthropic-quickstarts.git
cd anthropic-quickstarts/computer-use-demo
```

### 2. Environment Setup

Make sure you have Docker installed on your system. Then create a `.env` file in the `computer-use-demo` directory:

```
ANTHROPIC_API_KEY=your_api_key_here
```

### 3. Build and Run the Container

```bash
docker compose up --build
```

This will:
- Build the Docker container with all necessary dependencies
- Set up the environment for computer use
- Start a web interface (typically available at http://localhost:3000)

### 4. Test the Reference Implementation

- Open the web interface in your browser
- Try a simple computer use task to verify everything is working
- Review the logs to understand how the system is processing requests

## Phase 2: Understanding the Key Components

Before integrating with our task graph system, let's understand the key components of the reference implementation:

### Agent Loop (`loop.py`)

The core component that:
- Handles communication with the Anthropic API
- Processes tool requests from the model
- Executes the appropriate tools
- Returns results back to the model

### Tool Implementations

Located in the `tools` directory:
- `computer.py`: Handles browser automation and screenshots
- `text_editor.py`: Provides text editing capabilities
- `bash.py`: Executes command-line operations

### Web Interface

Provides a user-friendly way to:
- Enter prompts
- View the model's responses
- See tool executions in real-time
- Debug interactions

## Phase 3: Integration Strategy

We have two main options for integrating the reference implementation with our task graph system:

### Option 1: Task Graph Executor Inside Container

1. Copy our task graph executor into the container
2. Modify it to use the agent loop directly
3. Run tasks within the containerized environment

### Option 2: External Communication

1. Keep our task graph executor outside the container
2. Set up an API or communication channel between our system and the container
3. Send task nodes to the container for execution and receive results

For the MVP, we'll use Option 1 as it's simpler to implement.

## Phase 4: Implementation Steps

### 1. Prepare Task Graph Files

Place task graph JSON files in a directory that will be mounted to the container:

```bash
mkdir -p data/task_graphs
# Copy your existing task graph files here
cp /path/to/your/task_graphs/*.json data/task_graphs/
```

### 2. Create Task Graph Integration Script

Create a file called `task_graph_integration.py` in the `computer-use-demo` directory:

```python
#!/usr/bin/env python3
"""
Task Graph Integration with Anthropic's Computer Use Agent.

This script integrates the task graph executor with Anthropic's
reference implementation for computer use.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any

from computer_use_demo.loop import sampling_loop

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("task_graph_integration")

class TaskGraphIntegrator:
    """Integrates task graphs with Anthropic's Computer Use reference implementation."""
    
    def __init__(self, output_dir: str, model: str = "claude-3-7-sonnet-20240620", 
                 thinking_budget: int = 1024):
        """Initialize the Task Graph Integrator.
        
        Args:
            output_dir: Directory to store execution results
            model: Anthropic model to use
            thinking_budget: Token budget for thinking content
        """
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
    
    def execute_task_graph(self, task_graph_path: str) -> Dict[str, Any]:
        """Execute a task graph using Anthropic's Computer Use Agent.
        
        Args:
            task_graph_path: Path to the task graph JSON file
            
        Returns:
            Execution results
        """
        # Load task graph
        with open(task_graph_path, 'r') as f:
            task_graph = json.load(f)
        
        logger.info(f"Loaded task graph: {task_graph.get('name', 'Unnamed Task Graph')}")
        
        # Get nodes and edges
        nodes = task_graph.get("task_graph", {}).get("nodes", [])
        edges = task_graph.get("task_graph", {}).get("edges", [])
        
        if not nodes:
            logger.error("Task graph contains no nodes")
            return {"success": False, "error": "Task graph contains no nodes"}
        
        # Create execution order
        execution_order = self._create_execution_order(nodes, edges)
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
            node_result = self._execute_node(node, state_context)
            
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
    
    def _create_execution_order(self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> List[str]:
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
    
    def _execute_node(self, node: Dict[str, Any], state_context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute a task graph node using the Computer Use Agent.
        
        Args:
            node: Task graph node
            state_context: Context from previous nodes
            
        Returns:
            Node execution result
        """
        node_id = node.get("id", "unknown")
        prompt = self._create_node_prompt(node, state_context)
        
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
            
            # Run the agent loop from the reference implementation
            final_messages = sampling_loop(
                model=self.model,
                messages=messages,
                api_key=self.api_key,
                thinking_budget=self.thinking_budget,
                tool_version=tool_version,
                max_iterations=15  # Limit iterations to prevent runaway loops
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
    
    def _create_node_prompt(self, node: Dict[str, Any], state_context: List[Dict[str, Any]]) -> str:
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
        prompt = f"""I need your help to complete a {task_type} using Chrome. Please follow these instructions carefully:{verification_instructions}

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

def main():
    """Run a task graph with Anthropic's Computer Use Agent."""
    import argparse
    import time
    
    # Parse arguments
    parser = argparse.ArgumentParser(description="Run a task graph with Anthropic's Computer Use Agent")
    parser.add_argument(
        "--task-graph",
        default="data/task_graphs/chrome_search_task_graph.json",
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
            with open(args.task_graph, 'r') as f:
                task_graph = json.load(f)
            
            # Find node
            nodes = task_graph.get("task_graph", {}).get("nodes", [])
            node = next((n for n in nodes if n.get("id") == args.node_id), None)
            
            if not node:
                print(f"Node with ID {args.node_id} not found in task graph")
                return 1
            
            # Execute node
            print(f"Executing single node: {args.node_id}")
            result = integrator._execute_node(node, [])
            
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
            result = integrator.execute_task_graph(args.task_graph)
            
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
    import sys
    sys.exit(main())
```

### 3. Update the Docker Configuration

Modify the `docker-compose.yml` file to mount your task graph directory:

```yaml
volumes:
  - ./data:/app/data
```

### 4. Run the Integration

```bash
# Start the container
docker compose up -d

# Execute a task graph
docker exec -it computer-use-demo python task_graph_integration.py --task-graph data/task_graphs/chrome_search_task_graph.json --verbose
```

## Phase 5: Observing and Debugging

### 1. View the Results

Results will be saved to the `data/outputs` directory with:
- Prompts for each node
- Responses from the model
- Execution results JSON

### 2. Watch the Execution

You can observe the execution through:
- The terminal output
- The web interface at http://localhost:3000
- Logs from the container: `docker logs -f computer-use-demo`

### 3. Debug Issues

If you encounter problems:
1. Check the response files for error messages
2. Review the execution_results.json file for failure details
3. Adjust the prompts or task graph nodes as needed

## Next Steps for Enhancement

After the basic integration is working, you can enhance the system:

1. **Refine Prompts**: Adjust the prompts based on observed performance
2. **Extend Tool Usage**: Add text editor and bash tool support
3. **Improve Error Handling**: Add retry mechanisms for failed nodes
4. **Build Task Graph Libraries**: Create reusable templates for common tasks
5. **Add Metrics Collection**: Track performance to guide optimization

## Conclusion

This integration approach leverages Anthropic's reference implementation for computer use while maintaining the flexibility and organization of your task graph system. The containerized environment ensures consistency and reliability, while the task graph structure enables complex task organization and execution.

By following this guide, you can create a robust implementation of the Anthropic Computer Use Agent MVP that's ready for further development and enhancement.
