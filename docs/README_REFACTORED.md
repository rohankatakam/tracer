# Computer Use Agent - Refactored

This is the refactored codebase for the Computer Use Agent (CUA) for the upcoming hackathon on May 17. The code has been reorganized to improve maintainability while preserving the core functionality.

## Directory Structure

```
cu/
├── config/               # Configuration files
│   ├── .env              # Environment variables (API keys)
│   └── settings.py       # Global settings
├── core/                 # Core components
│   ├── agent/            # Agent implementation
│   │   └── anthropic_client.py
│   ├── execution/        # Task graph execution
│   │   ├── executor.py
│   │   └── task_graph_executor.py
│   └── taskgraph/        # Task graph models
│       ├── integrator.py
│       └── task_graph.py
├── scripts/              # Helper scripts
│   ├── cleanup.sh        # Cleanup script
│   ├── reset_cua_container.sh  # Docker management
│   └── run_task_graph.py      # Legacy runner
├── utils/                # Utility functions
│   ├── helpers.py        # General helpers
│   └── logging_utils.py  # Enhanced logging
├── run_cua.py            # Main entry point
└── task_graph.json       # Sample task graph
```

## Setup

1. Ensure your Anthropic API key is in the `.env` file in the `config` directory.
2. Ensure Docker is running for the Computer Use Agent container.
3. Reset/start the container when needed:
   ```bash
   ./scripts/reset_cua_container.sh
   ```

## Running the Computer Use Agent

Use the main entry point script to run the Computer Use Agent with a task graph:

```bash
python run_cua.py --task-graph path/to/task_graph.json --output-dir output
```

### Command Line Options

- `--task-graph`, `-t`: Path to task graph JSON file (default: task_graph.json)
- `--model`, `-m`: Anthropic model to use (default: claude-3-7-sonnet-20250219)
- `--output-dir`, `-o`: Directory for execution outputs (default: output/)
- `--thinking-budget`: Token budget for thinking steps (default: 1024)
- `--verbose`, `-v`: Enable verbose logging

## Next Steps

1. **Database Integration**: Implement PostgreSQL schema for bug storage
2. **Results Page Enhancement**: Create classification system for bug reproduction results
3. **Streamlit Request Interception**: Replace Selenium approach with Streamlit
4. **MCP Server Implementation**: Create required endpoints for the hackathon

## Notes

- This refactored version preserves all core functionality while making the codebase more maintainable
- Legacy files have been moved to backup directory
- Selenium-based approaches have been removed as they were not working reliably
