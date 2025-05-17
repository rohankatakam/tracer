# Roadmap for Bug-to-Task-Graph Pipeline Implementation (Friday, May 16th)

Given your time constraints and the desire to make meaningful progress, I've structured this roadmap into a series of achievable tasks organized by component, with estimated time frames. **Note**: With the requested additions, completing all tasks will likely extend significantly beyond a single day.

## 1. Version Control (30-45 min)

- **Create and switch to a new branch**
  ```bash
  git checkout -b feature/multimodal-pipeline-phase1
  ```
- **Commit cleaned codebase**
  ```bash
  git add .
  git commit -m "Clean up codebase, remove broken execution components"
  ```
- **Push to remote**
  ```bash
  git push -u origin feature/multimodal-pipeline-phase1
  ```

## 2. PostgreSQL Setup (1-1.5 hours)

- **Install PostgreSQL** (if not already installed)
  ```bash
  brew install postgresql
  ```
- **Start PostgreSQL service**
  ```bash
  brew services start postgresql
  ```
- **Create database and user**
  ```bash
  createdb bug_attachment_db
  createuser -P bug_processor  # With appropriate password
  ```
- **Add database configuration**
  - Create `config/database.py` with connection details
  - Update `.env.example` and `.env` with DB credentials

## 3. Database Layer Implementation (SQLAlchemy) (2-2.5 hours)

- **Install SQLAlchemy**
  ```bash
  pip install sqlalchemy psycopg2-binary alembic
  pip freeze > requirements.txt
  ```
- **Create migration framework**
  ```bash
  mkdir -p core/database/migrations
  alembic init core/database/migrations
  ```
- **Define SQLAlchemy Models**
  - Update `core/models/attachment_schema.py` with SQLAlchemy base classes
  - Define tables for Bug, Attachment, TextContent, ImageContent, PDFContent
- **Implement DB Connection**
  - Create `core/database/engine.py` with SQLAlchemy engine setup
- **Create Migrations**
  ```bash
  alembic revision --autogenerate -m "Initial schema setup"
  alembic upgrade head
  ```
- **Refactor Database CRUD Operations**
  - Replace pickle-based approach in `attachment_db.py` with SQLAlchemy ORM

## 4. API Layer for Database Interaction (1.5-2 hours)

- **Design and Implement RESTful API Endpoints**
  - Framework: FastAPI (recommended for modern Python APIs)
  - Key Endpoints for Bugs:
    - `POST /bugs` (Create a new bug)
    - `GET /bugs` (List all bugs)
    - `GET /bugs/{bug_id}` (Retrieve a specific bug)
    - `PUT /bugs/{bug_id}` (Update a specific bug)
    - `DELETE /bugs/{bug_id}` (Delete a specific bug)
  - Key Endpoints for Attachments:
    - `POST /bugs/{bug_id}/attachments` (Upload an attachment for a bug)
    - `GET /attachments/{attachment_id}` (Retrieve a specific attachment's metadata)
    - `GET /attachments/{attachment_id}/content` (Retrieve processed content if applicable)
- **Implement Request/Response Models**
  - Use Pydantic models for data validation and serialization.
- **Basic Authentication/Authorization** (Optional, if time permits)
  - Consider a simple API key mechanism.

## 5. Frontend for Bug Creation and Management (COMPLETED ✅)

- **Technology Choice**: Next.js with React (for a more robust solution with better API integration).
- **Core Functionality Implemented**:
  - Form to input bug details:
    - Title (text input)
    - Description (textarea)
    - Reporter (text input)
    - Severity (dropdown: Low, Medium, High, Critical)
    - File Upload for attachments (multiple types supported)
  - React components for form handling and API integration
  - API client service with Axios for interacting with the FastAPI backend
  - UI feedback for success/error states with modern components
  - Bug listing page to view all bugs with filtering options
  - Detail view for individual bugs with attachment management
  - Attachment previews for images, PDFs, and text files
- **Structure**:
  - Next.js app with TypeScript for better type safety
  - API integration layer with Axios
  - Component-based architecture for reusability
  - Styling with Tailwind CSS
  
## 5.1 Frontend Enhancements (TODO)

- **Editable Fields**:
  - Add ability to edit bug descriptions and details inline
  - Implement saving changes through the API
  - Add UI feedback for edit operations
- **Attachment Enhancements**:
  - Add support for referencing attachments within bug messages
  - Implement UI for selecting and linking to attachments
  - Track attachment references for taskgraph planning algorithm
- **Bug Status Management**:
  - Add ability to view and edit bug status on the detail page
  - Implement status workflow (New → In Progress → Resolved → Closed)
  - Add visual indicators for bug status
- **Comments System**:
  - Add ability to create and view comments on bugs
  - Implement threaded replies for deeper discussions
  - Allow attachments in comments
- **UI/UX Improvements**:
  - Add dark mode support
  - Implement responsive design improvements
  - Add keyboard shortcuts for power users

## 6. Attachment Processor Refinement (2-2.5 hours) (Previously Step 4)

- **Enhance Text Processor**
  - Complete `text_processor.py` implementation
  - Add metadata extraction for text files
  - Update integration with PostgreSQL storage
- **Enhance Image Processor**
  - Complete `image_processor.py` implementation
  - Improve OCR capabilities using Tesseract or similar
  - Add metadata extraction (dimensions, format)
  - Update integration with PostgreSQL storage
- **Enhance PDF Processor**
  - Complete `pdf_processor.py` implementation
  - Add text extraction for text-based PDFs
  - Implement basic OCR for image-based content
  - Extract basic metadata (pages, title, author)
  - Update integration with PostgreSQL storage
- **Update Main Attachment Processor**
  - Update `attachment_processor.py` to use enhanced processors
  - Improve handling of processing results
  - Ensure proper database integration

## 7. LLM Multimodal Reasoning Chain (2-3 hours) (Previously Step 5)

- **Enhance Task Graph Generator**
  - Modify `working_task_graph_generator.py` to pull all necessary bug data (title, description, processed attachment content) from PostgreSQL via the bug_id.
  - Update user prompt creation to effectively incorporate multimodal information.
  - Improve JSON structure alignment with target schema.
- **Implement Basic Context Management**
  - Add methods to retrieve relevant attachments and their processed content from the database.
  - Create a simple priority system or summarization strategy for including attachment data if it's too large for the LLM context window.
  - Implement token counting to manage context size.
- **Improve Response Handling**
  - Enhance JSON extraction and validation from LLM output.
  - Add basic error recovery mechanisms or retry logic for LLM calls.

## 8. External Bug Data Ingestion (2.5-3.5 hours)

- **8.1. Bugzilla API Client (1-1.5 hours)**
  - Identify target Bugzilla instance (e.g., public Mozilla instance for testing).
  - Use Python `requests` library to interact with the Bugzilla REST API (e.g., `GET /rest/bug`).
  - Fetch bug data (ID, summary, description, status, product, component, attachments).
  - Implement a script/module `core/ingestion/bugzilla_client.py`.
- **8.2. Chromium Issues Web Crawler (1.5-2 hours)**
  - **Disclaimer**: Web scraping can be fragile and might violate terms of service. Proceed with caution and respect `robots.txt`.
  - Target: Chromium issue tracker (e.g., issues.chromium.org).
  - Libraries: `requests` for fetching HTML, `BeautifulSoup4` for parsing.
  - Identify key HTML elements containing bug information (title, description, comments, metadata).
  - Implement a script/module `core/ingestion/chromium_crawler.py`.
  - Focus on extracting a few key fields initially.
- **8.3. Data Transformation & Loading (0.5-1 hour)**
  - Create mapping functions to transform Bugzilla and Chromium data structures into your application's Bug and Attachment schema.
  - Develop scripts to:
    - Read data fetched by the client/crawler.
    - Transform it.
    - Use the API layer (`POST /bugs` and `POST /bugs/{bug_id}/attachments`) to load the data into PostgreSQL. This ensures data validation and consistent processing.

## 9. Integration Testing & Task Graph API (2-3 hours) (Previously Step 6, expanded)

- **9.1. Task Graph Generation API Endpoint (1-1.5 hours)**
  - Create an API endpoint (e.g., `POST /bugs/{bug_id}/generate_taskgraph` or `POST /taskgraphs` with `bug_id` in body) using FastAPI.
  - This endpoint will:
    1. Accept a `bug_id`.
    2. Retrieve the full bug data (including description and references to processed attachment content) from PostgreSQL using the database layer or API layer.
    3. Invoke the `TaskGraphGenerator` with this data.
    4. Return the generated task graph (JSON response).
- **9.2. End-to-End Testing (1-1.5 hours)**
  - **Test Case 1: Bug Creation & Task Graph Generation via API**
    - Use the frontend to create a new bug with various attachments.
    - Verify it's stored in PostgreSQL.
    - Call the new Task Graph Generation API endpoint with the new `bug_id`.
    - Validate the generated task graph.
  - **Test Case 2: Imported Bug Data & Task Graph Generation**
    - Ingest sample data from Bugzilla or Chromium.
    - Verify storage in PostgreSQL.
    - Call the Task Graph Generation API for an imported bug.
    - Validate the output.
  - **Test Script**: Update `scripts/run_enhanced_pipeline.py` or create a new script to automate these API-driven tests.

## 10. Computer Use Agent (CUA) Integration & Execution (3-4 hours)

- **10.1. CUA Networking API Layer Design:**
  - Define API endpoints for the CUA to receive individual task nodes for execution (e.g., `POST /cua/execute_task`).
  - Specify the data format for task nodes (e.g., task description, type, parameters) and CUA responses (e.g., status, results, errors, screenshots/artifacts if applicable).
  - Consider security aspects: how will the main application authenticate with the CUA API?
- **10.2. Implement CUA Task Receiver:**
  - Modify your existing Anthropic Computer Use Agent to expose these API endpoints.
    - This might involve adding a lightweight web server (e.g., Flask or FastAPI) to the CUA's Python environment.
  - Ensure the CUA can receive a task node, trigger its internal execution logic (as per `TaskGraphExecutor`), and return the result.
  - Refer to CUA container management scripts (e.g., `reset_cua_container.sh`) if it's containerized.
- **10.3. Task Graph Executor Service (Main Application Side):**
  - Create a new service or module within your main application (e.g., `core/execution/cua_executor_service.py`).
  - This service will:
    1. Accept a complete task graph (likely in JSON format, as generated by Step 9.1).
    2. Parse the task graph to understand nodes and their dependencies.
    3. Iterate through task nodes in the correct order.
    4. For each executable task node, construct and send an API request to the CUA's `/cua/execute_task` endpoint.
    5. Receive and process the CUA's response (success, failure, output data).
    6. Manage the overall state of the task graph execution (e.g., which tasks are done, pending, failed).
    7. Handle errors and potential retries for CUA tasks.
- **10.4. End-to-End CUA Integration Testing:**
  - Update the integration testing phase (or create new tests) to cover the full loop:
    1. Create/Ingest a bug.
    2. Generate its task graph via the API (Step 9.1).
    3. Pass this task graph to the new Task Graph Executor Service.
    4. Verify that the CUA receives tasks, executes them (can be mocked or observed), and results are correctly reported back.
  - This could involve extending `scripts/run_enhanced_pipeline.py` or creating a new script like `scripts/run_full_cua_pipeline.py`.

## 11. Documentation Updates (1.5-2 hours) (Previously Step 10, expanded)

- **Update README.md**
  - Document new PostgreSQL requirement, API layer, frontend, data ingestion modules, task graph API, and CUA integration.
  - Add setup and usage instructions for all new components, including CUA API interaction.
  - Detail environment variables needed for Bugzilla API, CUA API endpoint, etc.
- **Update Code Documentation**
  - Ensure all new methods, classes, and API endpoints (including CUA-related ones) have docstrings.
  - Add comments for complex logic in crawlers, data transformers, CUA executor service, etc.
- **API Documentation** (if using FastAPI, Swagger/OpenAPI docs are auto-generated)
  - Review and enhance auto-generated API documentation for all services.

## Timeline (Estimated)

**Note**: The estimated times are aggressive and assume focused work. Completing all these tasks thoroughly will likely span multiple days.

| Time Block        | Task                                               | Estimated Hours | Cumulative Hours |
|-------------------|----------------------------------------------------|-----------------|------------------|
| Day 1 Afternoon   | 1. Version Control                                 | 0.75            | 0.75             |
|                   | 2. PostgreSQL Setup                              | 1.5             | 2.25             |
| Day 1 Evening     | 3. Database Layer Implementation (SQLAlchemy)      | 2.5             | 4.75             |
|                   | Break                                              | 0.5             | 5.25             |
|                   | 4. API Layer for Database Interaction              | 2               | 7.25             |
| Day 2 Morning     | 5. Frontend for Bug Creation (Next.js/React)      | 3.5             | 10.75            |
|                   | 5.1 Frontend Enhancements                         | 2.0             | 12.75            |
| Day 2 Afternoon   | 6. Attachment Processor Refinement                | 2.5             | 15.25            |
|                   | Break                                              | 0.5             | 15.75            |
| Day 2 Evening     | 7. LLM Multimodal Reasoning Chain                 | 3.0             | 18.75            |
| Day 3 Morning     | 8. External Bug Data Ingestion                    | 3.5             | 22.25            |
| Day 3 Afternoon   | 9. Integration Testing & Task Graph API           | 3.0             | 25.25            |
| Day 3 Evening     | 10. Computer Use Agent (CUA) Integration & Execution | 3.5             | 28.75            |
| Day 4 Morning     | 11. Documentation Updates                          | 1.5             | 30.25            |

**Total Estimated Hours: ~29.5 hours**

## Priority Order (If Time Becomes Limited - Staged Approach)

**Stage 1: Core End-to-End Pipeline (Focus for initial push)**
1.  Version Control (Done)
2.  PostgreSQL Setup (Essential)
3.  Database Layer Implementation (SQLAlchemy) (Essential)
4.  API Layer for Database Interaction (Essential for decoupling)
5.  Frontend for Bug Creation (COMPLETED ✅) 
6.  Attachment Processor Refinement (Text, Image, PDF - core to multimodal)
7.  LLM Multimodal Reasoning Chain (Core to generating task graphs)
8.  Integration Testing & Task Graph API (Essential for verifying task graph generation)
9.  Computer Use Agent (CUA) Integration & Execution (Essential for executing tasks)

**Stage 2: User Input & External Ingestion**
10. Frontend Enhancements (Editable fields, comments, attachment references)
11. External Bug Data Ingestion (Bugzilla Client and Chromium Crawler)
12. Documentation Updates (For completed stages)

**Stage 3: Polish & Refinements**
13. UI/UX Improvements (Dark mode, responsive design, keyboard shortcuts)
14. Further Documentation & Refinements

This expanded roadmap provides a more detailed and realistic plan for the comprehensive Bug-to-Task-Graph pipeline you envision.
