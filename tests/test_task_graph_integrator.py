#!/usr/bin/env python3

import os
import json
from pathlib import Path
import unittest
from task_graph_integrator import TaskGraphIntegrator

class TestTaskGraphIntegrator(unittest.TestCase):
    """Test the TaskGraphIntegrator class."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create test output directory
        self.test_output_dir = Path("test_output")
        
        # Create a test task graph
        self.test_task_graph_path = self.test_output_dir / "test_task_graph.json"
        
        # Ensure test directory exists
        self.test_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a simple test task graph
        self.test_task_graph = {
            "name": "Test Task Graph",
            "nodes": [
                {"id": "start", "type": "start", "content": "Start the task"},
                {"id": "task1", "type": "task", "content": "Do task 1", "verification": {"criteria": "Task 1 is done"}},
                {"id": "task2", "type": "task", "content": "Do task 2", "ui_elements": ["Button 1", "Input Field"]},
                {"id": "task3", "type": "task", "content": "Do task 3", "inputs": {"query": "test query"}},
                {"id": "end", "type": "end", "content": "End the task"}
            ],
            "edges": [
                {"source": "start", "target": "task1"},
                {"source": "task1", "target": "task2"},
                {"source": "task2", "target": "task3"},
                {"source": "task3", "target": "end"}
            ]
        }
        
        # Write the test task graph to a file
        with open(self.test_task_graph_path, 'w') as f:
            json.dump(self.test_task_graph, f, indent=2)
        
        # Create the integrator
        self.integrator = TaskGraphIntegrator(str(self.test_output_dir))
    
    def tearDown(self):
        """Clean up after the test."""
        # Remove test files
        if self.test_task_graph_path.exists():
            self.test_task_graph_path.unlink()
    
    def test_initialization(self):
        """Test that the integrator initializes correctly."""
        # Check that directories were created
        self.assertTrue((self.test_output_dir / "prompts").exists())
        self.assertTrue((self.test_output_dir / "responses").exists())
        
        # Check that the model was set correctly
        self.assertEqual(self.integrator.model, "claude-3-7-sonnet-20240620")
    
    def test_load_task_graph(self):
        """Test loading a task graph."""
        # Load the task graph
        task_graph = self.integrator.load_task_graph(str(self.test_task_graph_path))
        
        # Check that the task graph was loaded correctly
        self.assertEqual(task_graph["name"], "Test Task Graph")
        self.assertEqual(len(task_graph["nodes"]), 5)
        self.assertEqual(len(task_graph["edges"]), 4)
    
    def test_create_execution_order(self):
        """Test creating an execution order."""
        # Create the execution order
        execution_order = self.integrator.create_execution_order(
            self.test_task_graph["nodes"],
            self.test_task_graph["edges"]
        )
        
        # Check that the execution order is correct
        self.assertEqual(execution_order, ["start", "task1", "task2", "task3", "end"])
    
    def test_create_node_prompt(self):
        """Test creating a prompt for a node."""
        # Get a node
        node = self.test_task_graph["nodes"][2]  # task2
        
        # Create state context
        state_context = [
            {"id": "start", "content": "Start the task", "success": True},
            {"id": "task1", "content": "Do task 1", "success": True}
        ]
        
        # Create the prompt
        prompt = self.integrator.create_node_prompt(node, state_context)
        
        # Check that the prompt contains the expected content
        self.assertIn("Do task 2", prompt)
        self.assertIn("UI Elements to interact with", prompt)
        self.assertIn("Button 1", prompt)
        self.assertIn("Input Field", prompt)
        self.assertIn("Previously completed steps", prompt)
        self.assertIn("start: Start the task", prompt)
        self.assertIn("task1: Do task 1", prompt)
        self.assertIn("Firefox", prompt)

if __name__ == "__main__":
    unittest.main()
