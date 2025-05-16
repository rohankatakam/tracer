# Anthropic Computer Use Agent MVP Implementation Guide

## Overview

This guide outlines the steps to implement an MVP using Anthropic's built-in computer use agent capabilities instead of a custom implementation. This approach leverages Claude 3.7's advanced computer use tools to accelerate development and improve performance while maintaining compatibility with our existing task graph schema.

Refer to the `task_graph_schema.md` document for a detailed explanation of the task graph format used in this implementation.

## Benefits of Using Anthropic's Computer Use Agent

1. **Simplified Architecture**: No need to build custom screenshot, browser interaction, or verification logic
2. **Faster Development**: Reduced development time by using pre-built, optimized components
3. **Better Performance**: Anthropic has optimized their agent specifically for computer use tasks
4. **Lower Maintenance**: Automatic updates and improvements from Anthropic
5. **Advanced Features**: Built-in thinking capabilities and optimized prompting

## Implementation Steps

### 1. Set Up Environment

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install required packages
pip install anthropic python-dotenv
```

### 2. Create .env File

```
ANTHROPIC_API_KEY=your_api_key_here
```

### 3. Implement Task Graph Executor

Create a file named `task_graph_executor.py`:

```python
#!/usr/bin/env python3
"""
Task Graph Executor using Anthropic's Computer Use Agent.

This module executes task graphs by leveraging Anthropic's built-in
computer use tools in Claude 3.7 models.
"""

import os
import json
import time
import logging
import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

import anthropic
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("task_graph_executor")

class TaskGraphExecutor:
    """Executes task graphs using Anthropic's Computer Use Agent."""
    
    def __init__(self, output_dir: str, model: str = "claude-3-sonnet-20240229", 
                 thinking_budget: int = 1024, log_level: int = logging.INFO):
        """Initialize the Task Graph Executor.
        
        Args:
            output_dir: Directory to store execution results.
            model: Anthropic model to use (should support computer_use tool).
            thinking_budget: Token budget for thinking content.
            log_level: Logging level.
        """
        # Set up logging
        self.logger = logging.getLogger("task_graph_executor")
        self.logger.setLevel(log_level)
        
        # Load environment variables
        load_dotenv()
        
        # Set up API client
        self.client = anthropic.Anthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY")
        )
        
        # Set parameters
        self.model = model
        self.thinking_budget = thinking_budget
        
        # Set up output directory
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up subdirectories
        self.prompts_dir = self.output_dir / "prompts"
        self.responses_dir = self.output_dir / "responses"
        
        for directory in [self.prompts_dir, self.responses_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Task Graph Executor initialized with model: {model}")
    
    def execute_task_graph(self, task_graph_path: str) -> Dict[str, Any]:
        """Execute a task graph using Anthropic's Computer Use Agent.
        
        Args:
            task_graph_path: Path to the task graph JSON file.
            
        Returns:
            Execution results.
        """
        # Record start time
        start_time = datetime.datetime.now()
        
        # Load task graph
        try:
            with open(task_graph_path, 'r') as f:
                task_graph = json.load(f)
            
            self.logger.info(f"Loaded task graph: {task_graph.get('name', 'Unnamed Task Graph')}")
        except Exception as e:
            self.logger.error(f"Failed to load task graph: {e}")
            return {
                "success": False,
                "error": f"Failed to load task graph: {e}",
                "output_dir": str(self.output_dir)
            }
        
        # Get nodes and edges from the task graph
        nodes = task_graph.get("task_graph", {}).get("nodes", [])
        edges = task_graph.get("task_graph", {}).get("edges", [])
        
        if not nodes:
            self.logger.error("Task graph contains no nodes")
            return {
                "success": False,
                "error": "Task graph contains no nodes",
                "output_dir": str(self.output_dir)
            }
        
        # Create execution order based on edges
        execution_order = self._create_execution_order(nodes, edges)
        
        # Initialize results
        results = {
            "task_graph": task_graph.get("name", "Unnamed Task Graph"),
            "start_time": start_time.isoformat(),
            "steps": [],
            "success": True,
            "output_dir": str(self.output_dir)
        }
        
        # Keep track of state context
        state_context = []
        
        # Execute each node in order
        for node_id in execution_order:
            # Find the corresponding node
            node = next((n for n in nodes if n.get("id") == node_id), None)
            if not node:
                self.logger.warning(f"Node with ID {node_id} not found in task graph")
                continue
            
            # Execute the node
            self.logger.info(f"Executing node: {node_id}")
            node_result = self._execute_node(node, state_context)
            
            # Add node result to results
            results["steps"].append(node_result)
            
            # Update state context with this node's result
            state_context.append({
                "node_id": node_id,
                "content": node.get("content", ""),
                "success": node_result.get("success", False)
            })
            
            # Check if node execution failed
            if not node_result.get("success", False):
                self.logger.warning(f"Node {node_id} failed: {node_result.get('error')}")
                results["success"] = False
                results["failure_node"] = node_id
                break
        
        # Record end time
        end_time = datetime.datetime.now()
        results["end_time"] = end_time.isoformat()
        
        # Calculate duration
        results["duration"] = (end_time - start_time).total_seconds()
        
        # Save results
        results_path = self.output_dir / "execution_results.json"
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        self.logger.info(f"Task graph execution completed. Results saved to: {results_path}")
        
        return results
    
    def _create_execution_order(self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> List[str]:
        """Create execution order based on nodes and edges.
        
        Args:
            nodes: List of node dictionaries.
            edges: List of edge dictionaries.
            
        Returns:
            List of node IDs in execution order.
        """
        # Create a dictionary mapping node IDs to their dependencies
        dependencies = {node.get("id"): [] for node in nodes}
        
        # Add dependencies based on edges
        for edge in edges:
            source = edge.get("source")
            target = edge.get("target")
            if source and target:
                dependencies[target].append(source)
        
        # Execute nodes without dependencies first
        execution_order = []
        completed = set()
        
        # Function to recursively add nodes to the execution order
        def add_node(node_id):
            if node_id in completed:
                return
            
            node_deps = dependencies.get(node_id, [])
            for dep in node_deps:
                if dep not in completed:
                    add_node(dep)
            
            execution_order.append(node_id)
            completed.add(node_id)
        
        # Add all nodes to the execution order
        for node_id in dependencies.keys():
            add_node(node_id)
        
        self.logger.info(f"Execution order: {execution_order}")
        return execution_order
    
    def _execute_node(self, node: Dict[str, Any], state_context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute a task graph node using Anthropic's Computer Use Agent.
        
        Args:
            node: Task graph node to execute.
            state_context: Context from previously executed nodes.
            
        Returns:
            Node execution result.
        """
        node_id = node.get("id", "unknown")
        node_type = node.get("type", "action")
        content = node.get("content", "")
        metadata = node.get("metadata", {})
        
        self.logger.info(f"Executing node {node_id}: {content[:50]}{'...' if len(content) > 50 else ''}")
        
        # Record start time
        start_time = datetime.datetime.now()
        
        # Create state context text
        context_text = ""
        if state_context:
            context_text = "Previously completed steps:\n"
            for ctx in state_context:
                status = "✅ Completed successfully" if ctx.get("success") else "❌ Failed"
                context_text += f"- Step {ctx.get('node_id')}: {ctx.get('content')[:50]}... - {status}\n"
        
        # Create prompt
        prompt = self._create_node_prompt(node, context_text)
        
        # Save prompt for reference
        prompt_path = self.prompts_dir / f"node_{node_id}_prompt.txt"
        with open(prompt_path, 'w') as f:
            f.write(prompt)
        
        try:
            # Call the Anthropic API with computer use tool
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                system="You are a helpful computer use assistant that follows instructions precisely.",
                messages=[{"role": "user", "content": prompt}],
                tools=["computer_use"],
                thinking={"type": "enabled", "budget_tokens": self.thinking_budget}
            )
            
            # Parse response
            response_text = response.content[0].text if response.content else ""
            thinking_text = response.thinking.thinking if hasattr(response, "thinking") else ""
            
            # Save response for reference
            response_path = self.responses_dir / f"node_{node_id}_response.json"
            with open(response_path, 'w') as f:
                json.dump({
                    "response": response_text,
                    "thinking": thinking_text,
                    "tool_use": [str(tool) for tool in response.tool_use]
                }, f, indent=2)
            
            # Determine success based on response content
            success = "successfully completed" in response_text.lower() or "task complete" in response_text.lower()
            
            # Record end time
            end_time = datetime.datetime.now()
            
            # Create result
            result = {
                "id": node_id,
                "type": node_type,
                "content": content,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration": (end_time - start_time).total_seconds(),
                "success": success,
                "response": response_text,
                "thinking": thinking_text,
                "prompt": prompt,
                "prompt_file": str(prompt_path),
                "response_file": str(response_path)
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error executing node {node_id}: {e}")
            
            # Record end time
            end_time = datetime.datetime.now()
            
            # Create error result
            result = {
                "id": node_id,
                "type": node_type,
                "content": content,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration": (end_time - start_time).total_seconds(),
                "success": False,
                "error": str(e),
                "prompt": prompt,
                "prompt_file": str(prompt_path)
            }
            
            return result
    
    def _create_node_prompt(self, node: Dict[str, Any], context_text: str) -> str:
        """Create a prompt for node execution.
        
        Args:
            node: Task graph node.
            context_text: Context from previously executed nodes.
            
        Returns:
            Prompt for Anthropic's Computer Use Agent.
        """
        content = node.get("content", "")
        node_type = node.get("type", "action")
        metadata = node.get("metadata", {})
        
        # Extract metadata fields
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
        
        # Adjust instruction based on node type
        task_type = "verification task" if node_type == "verification" else "computer task"
        verification_instructions = ""
        if node_type == "verification":
            verification_instructions = "\nThis is a VERIFICATION step. Focus on checking and confirming the expected results rather than performing new actions. Take screenshots to document the verification."
        
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
        
        # Further customize prompt based on node type
        if node_type == "verification":
            prompt += "\n# Verification Criteria\nBe thorough in your verification. Explicitly state whether each aspect of the expected result has been confirmed and provide evidence via screenshots."

```python
#!/usr/bin/env python3
"""
Task Graph Runner for Computer Use Agent MVP.

This script runs a task graph using Anthropic's Computer Use Agent.
"""

import os
import sys
import time
import logging
import argparse
from pathlib import Path
from dotenv import load_dotenv

from task_graph_executor import TaskGraphExecutor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("task_runner")

def parse_args():
    """Parse command line arguments."""
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
        default="claude-3-sonnet-20240229",
        help="Anthropic model to use (must support computer_use tool)"
    )
    parser.add_argument(
        "--node-id", 
        default=None,
        help="ID of specific node to execute (if not provided, executes entire task graph)"
    )
    return parser.parse_args()

def main():
    """Run a task graph with Anthropic's Computer Use Agent."""
    # Parse arguments
    args = parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Check API key
    if "ANTHROPIC_API_KEY" not in os.environ:
        logger.error("ANTHROPIC_API_KEY environment variable is not set")
        return 1
    
    # Set up paths
    task_graph_path = args.task_graph
    if not os.path.exists(task_graph_path):
        logger.error(f"Task graph file not found: {task_graph_path}")
        return 1
    
    output_dir = args.output_dir or f"data/outputs/run_{int(time.time())}"
    
    # Create executor
    executor = TaskGraphExecutor(
        output_dir=output_dir,
        model=args.model
    )
    
    try:
        # Execute task graph or specific node
        if args.node_id:
            import json
            with open(task_graph_path, 'r') as f:
                task_graph = json.load(f)
            
            nodes = task_graph.get("task_graph", {}).get("nodes", [])
            node = next((n for n in nodes if n.get("id") == args.node_id), None)
            
            if not node:
                logger.error(f"Node with ID {args.node_id} not found in task graph")
                return 1
            
            print(f"Executing single node: {args.node_id}")
            result = executor._execute_node(node, [])
            
            print(f"\nNode execution result:")
            print(f"ID: {result.get('id')}")
            print(f"Content: {result.get('content')[:50]}...")
            print(f"Success: {result.get('success')}")
            print(f"Duration: {result.get('duration'):.2f} seconds")
            
            if result.get("error"):
                print(f"Error: {result.get('error')}")
            
            print(f"\nFull response saved to: {result.get('response_file')}")
            
        else:
            print("Executing full task graph")
            result = executor.execute_task_graph(task_graph_path)
            
            print(f"\nTask graph execution result:")
            print(f"Task graph: {result.get('task_graph')}")
            print(f"Success: {result.get('success')}")
            print(f"Duration: {result.get('duration'):.2f} seconds")
            
            print(f"\nSteps:")
            for step in result.get("steps", []):
                status = "✅" if step.get("success") else "❌"
                print(f"  {status} {step.get('id')}: {step.get('content')[:50]}...")
                
                if "error" in step:
                    print(f"     Error: {step.get('error')}")
            
            if not result.get("success") and "failure_node" in result:
                print(f"\nFailure at node: {result.get('failure_node')}")
            
            print(f"\nDetailed results saved to: {result.get('output_dir')}")
        
        return 0
    
    except Exception as e:
        logger.exception(f"Error running task graph: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

### 5. Run the MVP Implementation

```bash
# Run a specific node
python run_task_graph.py --node-id 1

# Run the full task graph
python run_task_graph.py

# Use a different model (Claude 3.7 Sonnet is recommended)
python run_task_graph.py --model claude-3-7-sonnet-20240307
```

## Key Design Principles

1. **Simplified Architecture**: Focus on orchestrating Anthropic's computer use agent rather than building custom logic.

2. **Task Graph Structure**: Maintain the task graph concept for organizing complex tasks into sequential steps.

3. **Explicit Verification**: Encourage Claude to verify completion of each subtask before moving to the next one.

4. **Thinking Capability**: Enable Claude's thinking capability to get insight into its reasoning process.

5. **Detailed Logging**: Maintain comprehensive logs and artifacts for debugging and improvement.

## Optimizing Model Performance

1. **Clear Instructions**: Provide explicit, step-by-step instructions in prompts.

2. **Verification Steps**: Always include verification criteria for each task.

3. **UI Element Guidance**: List specific UI elements to interact with when available.

4. **Keyboard Shortcuts**: Suggest keyboard shortcuts for challenging UI interactions like dropdowns and scrollbars.

5. **Thinking Aloud**: Encourage the model to verbalize its thinking process for better debugging.

## Next Steps

1. **Refinement**: Iterate on prompt templates based on observation of the model's performance.

2. **Task Library**: Build a library of successful task graph templates for common operations.

3. **Error Handling**: Implement more sophisticated error recovery strategies.

4. **Performance Monitoring**: Track success rates and completion times to identify areas for improvement.

## References

- [Anthropic Computer Use Documentation](https://docs.anthropic.com/en/docs/agents-and-tools/computer-use)
- [Claude API Reference](https://docs.anthropic.com/claude/reference/messages_post)
