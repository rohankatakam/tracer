# Bug Reporting and Analysis System

A system for parsing and analyzing bug reports using Anthropic's Computer Use Agent (CUA) API. This project focuses on structured bug data processing and sets the foundation for future integration with Anthropic's Computer Use Agent.

## Project Overview

This system provides robust data structures and processing capabilities for bug reports. It includes:

1. **Structured Bug Schemas**: Well-defined schemas for different bug tracking systems
2. **PDF Processing**: Extract text and images from PDF bug reports
3. **Attachment Handling**: Process various attachment types including images and text

## Getting Started

### Prerequisites

- Python 3.8+
- Anthropic API key (for future Computer Use Agent integration)

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
│   ├── outputs/              # Extracted data outputs
│   └── task_graphs/          # Task graph definition files
├── docs/                     # Documentation
├── core/                     # Core components
│   ├── agent/                # Anthropic agent interface
│   ├── ingestion/            # Data ingestion modules
│   ├── models/               # Data models and schemas
│   ├── taskgraph/            # Task graph definitions
│   └── utils/                # Utility functions
├── scripts/                  # Utility scripts
├── tests/                    # Test suites
└── requirements.txt          # Dependencies
```

## Features

- Structured bug schemas for multiple bug tracking systems
- PDF processing for bug report extraction
- Attachment handling (images, text, PDFs)
- Clean modular architecture with core components

## Using Anthropic's Computer Use Agent

This project is designed to serve as a foundation for integrating with Anthropic's Computer Use Agent (CUA). The current version focuses on robust data processing, while the actual browser automation is handled directly by Anthropic's CUA.

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Set up environment variables:
   ```
   ANTHROPIC_API_KEY=your_api_key_here
   ```

3. To use Anthropic's Computer Use Agent directly:

   ```python
   import os
   import anthropic
   
   # Set up the client
   client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
   
   # Create a message with system prompt
   response = client.messages.create(
       model="claude-3-7-sonnet-20250219",
       max_tokens=4096,
       system="You are a helpful Computer Use Agent that can use Chrome.",
       messages=[{"role": "user", "content": "Please open Chrome and search for 'Anthropic Claude API documentation'"}],
       tools=[{
           "name": "computer",
           "type": "computer_20250124",
           "display_width_px": 1280,
           "display_height_px": 800
       }]
   )
   ```

## Data Models

The system includes robust data models for bug reports from different tracking systems:

- BaseBugReport: Core schema with essential bug fields
- MozillaBugReport: Mozilla Bugzilla specific schema
- ChromiumBugReport: Chromium issue tracker schema
- OracleBugReport: Oracle bug tracking system schema

## License

[MIT](https://choosealicense.com/licenses/mit/)
