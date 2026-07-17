# Development Roadmap

> Historical planning document from the prototype sprint. It records intended work,
> not a claim that every item below is implemented. See `README.md` for current,
> verified capabilities and limitations.

**Core Goal:** Develop a Python application that uses Anthropic's CUA API to reproduce text-based bug reports, then present success/failure with evidence. Demo-ready for YC.

**Primary Development Tool:** WindSurf with Cascade Chat (using Claude 3.7 Sonnet Thinking)
**Execution Target:** Anthropic Computer Use Agent (CUA) API

---

## Day 1: Foundation, CUA Setup & Basic Input

**Overall Daily Goal:** Establish the project, connect to the Anthropic CUA, and parse simple text-based bug reports.

**Deliverables for Day 1:**

- Working local environment with Anthropic CUA quickstart successfully run.
- Core Python project structure.
- Script capable of making a basic CUA API call (e.g., navigate to a URL).
- Function to parse simple, numbered text steps from a bug report into a Python list.
- Successful execution of *one* CUA action driven by the script using a parsed step.

---

### Phase 1.1: Project Initialization & Environment Setup

- **Objective:** Create the foundational project structure and set up the Python environment.
- **Tasks:**
    1. Define and create the initial project directory structure (e.g., `src/`, `tests/`, `data/`, `scripts/`).
    2. Initialize a Git repository with a `.gitignore` file appropriate for Python projects.
    3. Create a `README.md` with a brief project description.
    4. Set up a Python virtual environment.
    5. Install initial dependencies: `anthropic`. Add them to `requirements.txt`.
- **Tools/Repos:** Git, Python, venv.
- **Checkpoint:** Basic project scaffold committed to Git.

---

### Phase 1.2: Anthropic CUA Quickstart Familiarization & First API Call

- **Objective:** Understand the Anthropic CUA quickstart example and replicate a basic CUA API call from our project's script.
- **Tasks:**
    1. Review and run the [Anthropic Computer Use quickstart repo/examples](https://github.com/anthropics/anthropic-sdk-python/tree/main/examples/computer_use).
    2. Develop a Python script (`src/main_controller.py` or similar) that:
        - Initializes the Anthropic API client.
        - Makes a single, hardcoded CUA tool call (e.g., `Maps_to_url` to "[https://example.com](https://example.com/)").
    3. Verify the browser action occurs as expected.
- **Tools/Repos:** Anthropic Python SDK.
- **Scope Minimization:** Focus on a single, direct CUA call. Do not implement dynamic behavior yet.
- **Feedback Logging (Initial):** Print the CUA API call details and the raw response to the console.
- **Checkpoint:** Script successfully executes one CUA action; code committed.

---

### Phase 1.3A: Comprehensive Bug Data Extraction

- **Objective:** Implement a system to extract and structure comprehensive bug data from various sources, while preserving our proven PDF processing technology for attachment handling.
- **Tasks:**
    1. Maintain the existing PDF processor module (`src/ingestion/pdf_processor.py`) for extracting text and images from PDF files.
    2. Enhance attachment processing to support both PDF and image attachments:
       - PDF attachments: Process using existing PDF processor (folder with JSON, raw text, images)
       - Image attachments: Create dedicated folders with the original image and a JSON extraction result from Gemini 2.5 Pro
    3. Design a comprehensive bug data schema to include:
       - Bug metadata (ID, title, severity, status)
       - Customer and product information
       - Detailed bug content (description, steps to reproduce, expected outcome)
       - Attachments with content extraction (maintaining existing structure for each attachment)
       - Stakeholder comments and history
    4. Ensure each attachment maintains its own folder structure with extracted content, similar to our existing PDF processing approach.
    5. Develop adapters for importing data from common bug tracking systems into the enhanced schema.
    6. Save extracted data in the enhanced schema as structured JSON while preserving attachment-specific processing.
    7. Develop unit tests for the data extraction and processing components.
- **Scope Minimization:** Preserve proven PDF processing technology while extending to other attachment types and metadata sources.
- **Validate Outputs:** Ensure all extracted data maintains proper structure and relationships across the enhanced schema.
- **Checkpoint:** Bug data extraction system successfully processes information into the enhanced schema with proper attachment handling; code committed.

---

### Phase 1.3B: Enhanced Task Graph Generation

- **Objective:** Implement a system using Gemini 2.5 Pro to convert comprehensive bug data into a structured task graph of actionable steps, leveraging all available information while maintaining the existing output schema.
- **Tasks:**
    1. Integrate Google's Generative AI Python SDK for Gemini 2.5 Pro.
    2. Enhance the TaskGraphGenerator to process the comprehensive bug data schema:
       - Process bug metadata, content, and comments
       - Process all attachments (PDFs and images) using their extracted content
       - Maintain the existing task graph output schema structure
    3. Design sophisticated prompts that utilize all available information sources:
       - Core bug description and steps to reproduce
       - PDF attachment content (text and images) from our existing extraction
       - Image attachment content with Gemini 2.5 Pro analysis
       - Metadata and stakeholder comments
    4. Implement intelligent context aggregation to combine information from multiple sources.
    5. Ensure backward compatibility with legacy data formats.
    6. Implement validation and error handling for LLM-generated task graphs.
    7. Create mechanisms to handle conflicting information across multiple sources.
    8. Develop unit tests for the enhanced task graph generator.
- **Scope Minimization:** Handle only clear, well-structured content. Build in fallbacks for cases where the LLM cannot parse reliably.
- **Validate Outputs:** Ensure the generated task graphs accurately represent the steps described in the bug reports.
- **Checkpoint:** Task graph generator implemented and tested; code committed.

---

## Day 2: Core Execution Loop & Output Capture

**Overall Daily Goal:** Execute a sequence of parsed bug report steps via CUA, capture visual evidence (screenshots), and begin structured logging of the process.

**Deliverables for Day 2:**

- System that iterates through parsed steps, constructing prompts for Anthropic's Claude (to be executed by CUA) for each step.
- Screenshots saved to disk after key CUA actions.
- A preliminary JSON structure logging intended steps and Claude's CUA tool call requests.

---

### Phase 2.1: Sequential CUA Action Execution Loop

- **Objective:** Implement logic to iterate through parsed bug report steps and trigger corresponding CUA actions via Anthropic's Claude.
- **Tasks:**
    1. Modify `src/main_controller.py` to:
        - Take the list of parsed steps as input.
        - Loop through each step.
        - For each step, construct a prompt for Anthropic's Claude. The prompt should instruct Claude to generate the appropriate CUA tool call(s) to perform the action described in the step text. (e.g., "Please generate the CUA tool call to: [parsed step text]").
        - Execute the CUA tool call(s) returned by Anthropic's Claude.
- **Scope Minimization:** Linear execution. If a step's CUA call fails (as reported by the CUA API), stop and log the error. No complex error recovery or retry logic yet.
- **Feedback Logging:** Log the prompt sent to Anthropic's Claude for each step and the direct JSON response (tool use request) from Claude.
- **Checkpoint:** Script attempts to execute a sequence of 2-3 actions from a parsed bug report; code committed.

---

### Phase 2.2: Screenshot Capture via CUA

- **Objective:** Integrate CUA's screenshot capability to capture visual evidence during bug reproduction.
- **Tasks:**
    1. In `src/main_controller.py`, after each significant CUA action is executed (or as specified), use the CUA `screenshot` tool.
    2. Save screenshots to a designated directory (e.g., `data/run_[timestamp]/screenshots/`).
    3. Name screenshots meaningfully (e.g., `step_1_action_navigate.png`, `step_2_action_click.png`).
- **Validate Outputs:** Manually review saved screenshots to confirm they accurately reflect the browser state at each intended capture point.
- **Checkpoint:** Screenshots are captured and saved during the execution flow; code committed.

---

### Phase 2.3: Proto Task Graph (JSON Logging)

- **Objective:** Implement initial structured logging of the reproduction attempt into a JSON format. This will evolve into the "Task Graph."
- **Tasks:**
    1. Define a basic JSON schema for the run log. Key fields per step:
        - `step_index` (integer)
        - `original_instruction` (string from parsed bug report)
        - `prompt_to_claude` (string)
        - `claude_tool_calls_requested` (JSON object/array from Claude's response)
        - `cua_execution_status` (e.g., "SUCCESS", "FAILURE_API_ERROR", "FAILURE_TOOL_ERROR")
        - `screenshot_path` (string, if applicable)
    2. Implement functionality in `src/main_controller.py` (or a new `src/logger.py`) to populate this JSON structure during a run.
    3. Save the complete JSON log to a file at the end of each run (e.g., `data/run_[timestamp]/task_log.json`).
- **Scope Minimization:** Focus on capturing information. This is primarily for logging and debugging at this stage.
- **Checkpoint:** A JSON log file is generated for each reproduction attempt; code committed.

---

## Day 3: Verification, Enhanced Logging & Prompt Engineering

**Overall Daily Goal:** Implement basic success/failure verification for the bug reproduction, create comprehensive execution logs, and refine prompts to Anthropic's Claude for more reliable CUA control.

**Deliverables for Day 3:**

- A basic mechanism to determine if the bug was reproduced (e.g., checking for specific text on the final page).
- Comprehensive execution log file incorporating all relevant details.
- Refined JSON task graph/log that includes actual CUA outcomes and screenshot paths.

---

### Phase 3.1: Basic Result Verification

- **Objective:** Add a simple check to determine if the final step of the bug report achieved the expected outcome.
- **Tasks:**
    1. For the bug reports being tested, define a simple, verifiable expected outcome for the *final step* (e.g., "Text 'Welcome, TestUser!' should be visible on the page").
    2. After the final step's CUA actions, use CUA's `read_page_content` tool to get the current page's text content.
    3. Implement logic in `src/main_controller.py` to check if the expected text exists in the content retrieved.
    4. Record a `final_verification_status` ("PASSED", "FAILED") in the JSON log.
- **Scope Minimization:** Verify only one key piece of text on the final page. Avoid complex DOM parsing or image-based verification for the MVP.
- **Validate Outputs:** Manually confirm if the system's "PASSED"/"FAILED" status aligns with the actual browser state.
- **Checkpoint:** System reports a basic pass/fail status for the overall bug reproduction; code committed.

---

### Phase 3.2: Comprehensive Feedback Logging System

- **Objective:** Establish a detailed and structured logging system using Python's `logging` module for robust debugging and iterative improvement.
- **Tasks:**
    1. Integrate Python's `logging` module into the application.
    2. Configure logging to output to both console (INFO level) and a file (DEBUG level, e.g., `data/run_[timestamp]/execution.log`).
    3. Ensure the following are logged with appropriate context (e.g., step number):
        - Input bug report details.
        - Prompt sent to Anthropic's Claude for each step.
        - Anthropic Claude's full JSON response (including tool selection and arguments).
        - Details of CUA tool calls being executed.
        - CUA's response/result for each tool call (success, failure, data returned).
        - Paths to any screenshots taken.
        - Outcome of the final verification step.
        - Any errors or exceptions encountered.
- **Feedback Logging (for improvement):** This detailed file log is critical for diagnosing issues and refining prompts to Anthropic's Claude.
- **Checkpoint:** Comprehensive log files are generated for each run, aiding in debugging; code committed.

---

### Phase 3.3: Refining Prompts to Anthropic's Claude & Enriching Task Graph

- **Objective:** Improve the reliability of CUA actions by iteratively refining the prompts sent to Anthropic's Claude, and ensure the JSON task graph/log is complete.
- **Tasks:**
    1. Analyze execution logs and JSON task logs from previous runs to identify common failure points or unreliable CUA actions.
    2. Experiment with and refine the prompt structure provided to Anthropic's Claude. Consider:
        - Clarity of action verbs.
        - Specificity in identifying UI elements (e.g., "Click the button with exact text 'Submit Order'" vs. "Click submit").
        - Providing context from previous steps if necessary.
    3. Update the JSON task graph/log (`task_log.json`) to ensure it captures:
        - `cua_tool_call_actual_outcome` (detailed success/error message from CUA execution for each tool call).
        - Timestamps for key events.
- **Scope Minimization:** Focus on improving reliability for the types of actions in your demo bug reports. Don't aim for universal understanding.
- **Checkpoint:** Prompts to Anthropic's Claude are more robust for target scenarios. JSON task graph is comprehensive; code committed.

---

## Day 4: Integration, Polishing & YC Demo Preparation

**Overall Daily Goal:** Ensure all components are smoothly integrated, create a compelling demo script with 1-2 examples, and polish the CLI and output artifacts.

**Deliverables for Day 4:**

- A polished end-to-end demo flow: input bug report -> CUA execution -> clear success/failure report (console summary, detailed logs, screenshots, JSON artifact).
- A well-documented demo script for 1-2 compelling bug reproduction examples.
- Cleaned-up codebase with comments and basic documentation.

---

### Phase 4.1: End-to-End System Integration & CLI

- **Objective:** Integrate all developed components into a cohesive application controlled by a simple Command Line Interface (CLI).
- **Tasks:**
    1. Ensure `src/main_controller.py` (or a main script in `scripts/`) orchestrates the entire flow:
        - Parses input bug report (from a file specified via CLI).
        - Executes steps via CUA/Anthropic Claude.
        - Performs verification.
        - Handles logging (console summary and detailed file logs).
        - Saves all artifacts (JSON task graph, screenshots) to a run-specific directory.
    2. Implement a CLI using `argparse` in Python:
        - Accept a path to a text file containing the bug report steps.
        - Optionally, an output directory for run artifacts.
    3. Display a concise summary of the run (e.g., "Bug report [name]: Reproduced [SUCCESS/FAILURE]. Artifacts saved to [path].").
- **Scope Minimization:** Keep CLI arguments simple.
- **Checkpoint:** System runs end-to-end via CLI command; code committed.

---

### Phase 4.2: Demo Script & Example Preparation

- **Objective:** Prepare and rehearse 1-2 compelling demo scenarios for the YC presentation.
- **Tasks:**
    1. Select 1-2 bug reports that:
        - Are described by simple text steps.
        - Are visually clear when reproduced/failed in a browser.
        - The system can reliably handle.
        - Demonstrate the "wow" factor (AI understanding and acting in a browser).
    2. Write a detailed demo script:
        - What you will say.
        - What you will show (the input bug report file, the CLI command, the browser window during CUA execution, the console output, key parts of the log file, screenshots, and the final JSON task graph).
    3. Practice the demo multiple times for smoothness and timing.
- **Validate Outputs:** Ensure the demo runs flawlessly and effectively communicates the product's value.
- **Checkpoint:** Demo scripts finalized and rehearsed.

---

### Phase 4.3: Final Code Polish & Documentation (`README.md`)

- **Objective:** Clean the codebase, add necessary comments/docstrings, and update the `README.md` for clarity and future reference.
- **Tasks:**
    1. Review all Python code for clarity, consistency, and add comments/docstrings where needed.
    2. Ensure error handling is reasonable (e.g., graceful exits on critical errors).
    3. Update the main `README.md` file to include:
        - A brief overview of the project.
        - Setup instructions (Python version, dependencies, environment variables if any for Anthropic API key).
        - Instructions on how to run the bug reproduction script via the CLI.
        - Description of the output artifacts (logs, JSON task graph, screenshots).
    4. Organize the `data/` directory if needed, perhaps with example bug reports.
- **Scope Minimization:** Focus on making the existing MVP code understandable and runnable. No new features.
- **Checkpoint:** Code is clean, commented. `README.md` provides essential information. Project is demo-ready; final commit.

---

### Optional Stretch Goals (Consider if ahead of schedule on any given day)

- **Day 1 Stretch:** Implement a mechanism for Anthropic's Claude/CUA to provide a simple "element not found" or "action failed" structured response that your script can interpret beyond just a generic error.
- **Day 2 Stretch:** Develop a very simple HTML report generator (Python script creating basic HTML) that takes the JSON task log and screenshots to display a more user-friendly summary of a run.
- **Day 3 Stretch:** If a bug report involves checking for the *absence* of an element/text as a success condition, add support for this in the verification phase.
- **Day 4 Stretch:** Parameterize a common target website/URL in a configuration file instead of hardcoding it if used frequently in demos.
