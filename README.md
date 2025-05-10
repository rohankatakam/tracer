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
5. Configure your Anthropic API key as an environment variable: `export ANTHROPIC_API_KEY=your_api_key_here`

## Project Structure

- `src/`: Source code for the project
- `tests/`: Test files
- `data/`: Storage for bug reports, screenshots, and execution logs
- `scripts/`: Utility scripts

## License

[MIT](https://choosealicense.com/licenses/mit/)
