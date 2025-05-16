#!/usr/bin/env python3

import os
import asyncio
from pathlib import Path
from selenium.webdriver.chrome.options import Options
from task_graph_integrator import TaskGraphIntegrator

async def main():
    # Verify API key is set in environment
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable is not set.")
        print("Please set it or use the run_firefox_test.sh script which loads it from .env")
        return
    
    # Create output directory with timestamp
    timestamp = int(asyncio.get_event_loop().time())
    output_dir = Path(f"data/outputs/firefox_search_{timestamp}")
    
    # Initialize the integrator with web UI URL pointing to your Docker container
    # For better UI interaction, use Chrome in non-headless mode
    options = Options()
    # Uncomment the following line to make the browser visible (helpful for debugging)
    # options.add_argument("--headless=new")  # Comment this line to see the browser
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    integrator = TaskGraphIntegrator(
        output_dir=str(output_dir),
        model="claude-3-7-sonnet-20240620",  # Using the latest Claude model
        thinking_budget=1024,
        web_ui_url="http://localhost:8080"  # This is the Docker container's web UI
    )
    
    # Set options to driver after initialization
    integrator.options = options
    
    # Path to your task graph
    task_graph_path = "data/task_graphs/firefox_search_task_graph.json"
    
    print(f"Starting task graph execution from {task_graph_path}")
    print(f"Results will be saved to {output_dir}")
    
    try:
        # Execute task graph
        result = await integrator.execute_task_graph(task_graph_path)
        
        # Print summary of execution
        print("\n--- Execution Summary ---")
        print(f"Task Graph: {result.get('task_graph')}")
        print(f"Success: {'✅' if result.get('success') else '❌'}")
        
        if not result.get("success") and "failure_node" in result:
            print(f"Failed at node: {result.get('failure_node')}")
        
        print("\n--- Execution Steps ---")
        for step in result.get("steps", []):
            status = "✅" if step.get("success") else "❌"
            print(f"{status} Node {step.get('id')}: {step.get('content')[:50]}...")
        
        print(f"\nDetailed results saved to {output_dir / 'execution_results.json'}")
        
    except Exception as e:
        print(f"Error executing task graph: {e}")
    finally:
        # Clean up the browser session
        if hasattr(integrator, 'driver') and integrator.driver is not None:
            print("Closing browser session...")
            integrator.driver.quit()

if __name__ == "__main__":
    asyncio.run(main())
