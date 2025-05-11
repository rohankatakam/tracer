# AI-Powered Bug Reproduction MVP

AI-Powered Bug Reproduction MVP using Anthropic's Computer Use Agent (CUA) API. This project aims to reproduce software bugs by parsing reports and driving browser actions with AI.

## Project Overview

This system parses bug reports in a structured format and uses Anthropic's Claude (via the Computer Use Agent API) to reproduce the reported bug steps in a browser environment. The system captures evidence of the bug reproduction process through screenshots and structured logs.

## Getting Started

### Prerequisites

- Python 3.8+
- Anthropic API key

### Installation

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`  
   - macOS/Linux: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`

## Project Structure

```
/
├── data/                     # Data storage directory
│   ├── chrome_search_test/   # Test results for Chrome search tasks
│   ├── outputs/              # Extracted data outputs
│   ├── task_graphs/          # Task graph definition files
│   └── test_output/          # General test output data
├── docs/                     # Documentation
├── src/                      # Source code
│   ├── extraction/           # Content extraction modules
│   ├── ingestion/            # Data ingestion modules
│   ├── reporting/            # Reporting utilities
│   ├── test_cases/           # Test case definitions
│   ├── test_framework/       # Test framework components
│   └── utils/                # Utility functions
├── tests/                    # Test suites
└── requirements.txt          # Dependencies
```

## Features

- Task graph-based automation using Claude API
- Browser automation for web interactions
- Content extraction from web pages
- Comprehensive logging and reporting
- Enhanced bug data schema support

## Getting Started

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Set up environment variables:
   ```
   ANTHROPIC_API_KEY=your_api_key_here
   ```

3. Run a sample test:
   ```
   python test_chrome_search.py
   ```

## Task Graphs

Task graphs define a sequence of steps to be executed by the automation framework. Each step includes:

- Action to be performed
- Verification of the action
- Success and failure paths

See `data/task_graphs/chrome_search_task_graph.json` for an example.
- `data/`: Storage for bug reports, execution logs, and outputs
  - `test_inputs/`: Input files for testing (PDFs, etc.)
  - `test_outputs/`: Output files generated during testing
- `logs/`: Application and test logs
- `run_cua.sh`: Main script for running the application and tests

## License

[MIT](https://choosealicense.com/licenses/mit/)
