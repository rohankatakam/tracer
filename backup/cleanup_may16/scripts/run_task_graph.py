#!/usr/bin/env python3
"""
Task Graph Runner for Computer Use Agent MVP.

This script runs a task graph using Anthropic's Computer Use Agent.
"""

import os
import sys
import json
import time
import asyncio
import logging
import argparse
from pathlib import Path
from dotenv import load_dotenv

from core.taskgraph.task_graph_executor import TaskGraphExecutor
import sys
# Add project root to path to allow importing modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from taskgraph_integration.core.integrator import TaskGraphIntegrator
from taskgraph_integration.core.task_graph import TaskGraph
from taskgraph_integration.utils.helpers import validate_api_key

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
        default="../data/task_graphs/chrome_search_task_graph.json",
        help="Path to task graph JSON file"
    )
    parser.add_argument(
        "--output-dir", 
        default=None,
        help="Output directory for execution results"
    )
    parser.add_argument(
        "--model", 
        default="claude-3-opus-20240229",
        help="Anthropic model to use (must support computer_use tool)"
    )
    parser.add_argument(
        "--thinking-budget",
        type=int,
        default=1024,
        help="Token budget for thinking content"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--node-id", 
        default=None,
        help="ID of specific node to execute (if not provided, executes entire task graph)"
    )
    return parser.parse_args()

async def execute_single_node(output_dir, model, thinking_budget, task_graph_path, node_id):
    """Execute a single node from a task graph.
    
    Args:
        output_dir: Output directory
        model: Model to use
        thinking_budget: Thinking token budget
        task_graph_path: Path to task graph
        node_id: ID of node to execute
        
    Returns:
        Execution result or error code
    """
    # Create integrator
    integrator = TaskGraphIntegrator(
        output_dir=output_dir,
        model=model,
        thinking_budget=thinking_budget
    )
    
    try:
        # Load task graph and find node
        with open(task_graph_path, 'r') as f:
            task_graph_data = json.load(f)
        
        # Handle nested structure if present
        if "task_graph" in task_graph_data and isinstance(task_graph_data["task_graph"], dict):
            nodes = task_graph_data["task_graph"].get("nodes", [])
        else:
            nodes = task_graph_data.get("nodes", [])
        
        node = next((n for n in nodes if n.get("id") == node_id), None)
        
        if not node:
            logger.error(f"Node with ID {node_id} not found in task graph")
            return 1
        
        print(f"Executing single node: {node_id}")
        
        # Create the prompt for the node
        node_prompt = TaskGraph.create_node_prompt(node, [])
        
        # Execute the node
        start_time = time.time()
        result = await integrator.executor.execute_node(node, [], node_prompt)
        duration = time.time() - start_time
        
        # Add duration to result
        result["duration"] = duration
        
        print(f"\nNode execution result:")
        print(f"ID: {result.get('id')}")
        print(f"Content: {result.get('content')[:50]}...")
        print(f"Success: {result.get('success')}")
        print(f"Duration: {duration:.2f} seconds")
        
        if result.get("error"):
            print(f"Error: {result.get('error')}")
        
        print(f"\nFull response saved to: {result.get('response_file')}")
        
        # Clean up
        integrator.cleanup()
        return 0
    except Exception as e:
        logger.exception(f"Error executing node: {e}")
        return 1

async def execute_full_task_graph(output_dir, model, thinking_budget, task_graph_path):
    """Execute a full task graph.
    
    Args:
        output_dir: Output directory
        model: Model to use
        thinking_budget: Thinking token budget
        task_graph_path: Path to task graph
        
    Returns:
        Execution result or error code
    """
    # Create integrator
    integrator = TaskGraphIntegrator(
        output_dir=output_dir,
        model=model,
        thinking_budget=thinking_budget
    )
    
    try:
        # Execute task graph
        print("Executing full task graph")
        start_time = time.time()
        result = await integrator.execute_task_graph(task_graph_path)
        duration = time.time() - start_time
        
        # Add duration to result
        result["duration"] = duration
        result["output_dir"] = output_dir
        
        print(f"\nTask graph execution result:")
        print(f"Task graph: {result.get('task_graph')}")
        print(f"Success: {result.get('success')}")
        print(f"Duration: {duration:.2f} seconds")
        
        print(f"\nSteps:")
        for step in result.get("steps", []):
            status = "✅" if step.get("success") else "❌"
            content = step.get('content', '')
            truncated_content = content[:50] + "..." if len(content) > 50 else content
            print(f"  {status} {step.get('id')}: {truncated_content}")
            
            if "error" in step:
                print(f"     Error: {step.get('error')}")
        
        if not result.get("success") and "failure_node" in result:
            print(f"\nFailure at node: {result.get('failure_node')}")
        
        print(f"\nDetailed results saved to: {output_dir}")
        
        # Clean up
        integrator.cleanup()
        return 0
    except Exception as e:
        logger.exception(f"Error executing task graph: {e}")
        return 1

def main():
    """Run a task graph with Anthropic's Computer Use Agent."""
    # Parse arguments
    args = parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Check API key
    if not validate_api_key():
        return 1
    
    # Set up paths
    task_graph_path = args.task_graph
    if not os.path.exists(task_graph_path):
        logger.error(f"Task graph file not found: {task_graph_path}")
        return 1
    
    output_dir = args.output_dir or f"data/outputs/run_{int(time.time())}"
    
    # Set up logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        for module in ["taskgraph_integration", "core", "browser", "utils"]:
            logging.getLogger(module).setLevel(logging.DEBUG)
    
    # Run the appropriate async function
    if args.node_id:
        return asyncio.run(execute_single_node(
            output_dir=output_dir,
            model=args.model,
            thinking_budget=args.thinking_budget,
            task_graph_path=task_graph_path,
            node_id=args.node_id
        ))
    else:
        return asyncio.run(execute_full_task_graph(
            output_dir=output_dir,
            model=args.model,
            thinking_budget=args.thinking_budget,
            task_graph_path=task_graph_path
        ))

if __name__ == "__main__":
    sys.exit(main())
