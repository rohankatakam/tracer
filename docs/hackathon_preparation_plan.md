# Hackathon Preparation Plan

## Timeline
- **Tonight**: 2-3 hours
- **Tomorrow**: 1 hour remote work + evening
- **Hackathon**: Saturday, May 17 (10:00 AM - 8:00 PM)

## System Architecture Overview
TaskGraph planning → CUA execution → Results insight

## Tonight (2-3 hours)

### 1. Codebase Refactoring (1.5 hours)
- Remove unnecessary files as per memory notes
- Focus on organizing the core components: task graph execution, CUA integration
- Create clear separation between execution, frontend, and data storage

**Priority files to keep/refactor:**
- `task_graph_executor.py`
- `run_task_graph.py`
- `taskgraph_integration/` directory
- `src/anthropic_client.py`

### 2. Execution Layer Setup (1.5 hours)
- Streamline the Anthropic Computer Use Agent integration
- Focus on the streamlit request interception approach (preferred over Selenium)
- Ensure proper logging is implemented to save chat history

## Tomorrow (1 hour + evening)

### 3. Bug Database Structure (1-2 hours)
- Create a basic PostgreSQL schema for bug storage
- Implement simple CRUD operations for bug management
- Create a migration script to convert existing JSON data to PostgreSQL

### 4. Results Page Enhancement (2-3 hours)
- Implement a classification system for bug reproduction results
- Create a template for detailed results display
- Set up the foundation for integrating with the MCP server later

## Hackathon Day (10 hours)

### 5. MCP Server Implementation (3-4 hours)
- Create skeleton for all required endpoints:
  - `/get_all_bugs`
  - `/find_bug`
  - `/reproduce_bug`
  - `/update_bug`
- Implement authentication if needed

### 6. Frontend-Backend Integration (3-4 hours)
- Connect the frontend to the new PostgreSQL database
- Implement the API calls to the MCP server
- Create UI components for displaying results and updating bug status

### 7. Testing and Debugging (2-3 hours)
- Test full integration of all components
- Fix any issues that arise
- Document the system architecture and API endpoints

## Detailed Implementation Plan

### Tonight: Refactor and Execution Layer

1. **Codebase Cleanup**:
   - Remove unneeded files per memory notes
   - Structure the project with clear boundaries between components
   - Keep focus on the MVP implementation using Anthropic's built-in capabilities

2. **Streamlit Integration**:
   - Use the existing Docker container (`reset_cua_container.sh`)
   - Implement request interception for Streamlit
   - Add logging for chat history preservation

### Tomorrow: Database and Results Page

1. **PostgreSQL Setup**:
   - Create a Docker container for PostgreSQL
   - Design schema for bug tracking
   - Implement data migration from JSON

2. **Enhanced Results Page**:
   - Design classification logic for bug statuses
   - Create templates for detailed reproduction reports
   - Implement basic UI for result viewing

### Hackathon Day: MCP and Integration

1. **MCP Implementation**:
   - Create a FastAPI or Flask server with required endpoints
   - Connect to PostgreSQL database
   - Implement authentication if needed

2. **Integration**:
   - Connect frontend to MCP endpoints
   - Implement real-time status updates
   - Add user interaction for bug status changes

## Key Focus Areas

1. **Keep the codebase lean** - Remove obsolete files, focus on essential components
2. **Improve CUA integration** - Prioritize streamlit request interception over Selenium
3. **Database first** - Build a solid data layer before enhancing the frontend
4. **MCP as the glue** - Use the MCP server as the central integration point
