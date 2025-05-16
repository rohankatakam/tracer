#!/usr/bin/env python3

import os
import asyncio
import argparse
from pathlib import Path
from task_graph_integrator import TaskGraphIntegrator

async def main():
    parser = argparse.ArgumentParser(description="Execute a task graph using Anthropic's Computer Use")
    parser.add_argument("--task-graph", required=True, help="Path to task graph JSON file")
    parser.add_argument("--output-dir", default="data/outputs/run_" + str(int(asyncio.get_event_loop().time())), 
                        help="Output directory for execution results")
    parser.add_argument("--model", default="claude-3-7-sonnet-20240620", help="Claude model to use")
    parser.add_argument("--thinking-budget", type=int, default=1024, help="Thinking budget for Claude")
    parser.add_argument("--api-base-url", default="http://localhost:8080", help="Computer Use API base URL")
    parser.add_argument("--node-id", help="Execute only a specific node ID (optional)")
    args = parser.parse_args()
    
    # Create the integrator
    integrator = TaskGraphIntegrator(
        output_dir=args.output_dir,
        model=args.model,
        thinking_budget=args.thinking_budget,
        api_base_url=args.api_base_url
    )
    
    # Check if API key is set
    if not os.environ.get("ANTHROPIC_API_KEY"):
        api_key = input("ANTHROPIC_API_KEY environment variable is not set. Enter your API key: ")
        os.environ["ANTHROPIC_API_KEY"] = api_key
    
    if args.node_id:
        # Execute a single node
        task_graph = integrator.load_task_graph(args.task_graph)
        nodes = task_graph.get("nodes", [])
        node = next((n for n in nodes if n.get("id") == args.node_id), None)
        
        if not node:
            print(f"Node with ID {args.node_id} not found in task graph")
            return
        
        result = await integrator.execute_node(node, [])
        print(f"Node execution {'succeeded' if result.get('success') else 'failed'}")
        print(f"Response saved to {result.get('response_file')}")
    else:
        # Execute entire task graph
        result = await integrator.execute_task_graph(args.task_graph)
        print(f"Task graph execution {'succeeded' if result.get('success') else 'failed'}")
        
        if not result.get("success") and "failure_node" in result:
            print(f"Failed at node: {result.get('failure_node')}")

if __name__ == "__main__":
    asyncio.run(main())
