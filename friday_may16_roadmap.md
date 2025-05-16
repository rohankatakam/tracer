# Roadmap for Bug-to-Task-Graph Pipeline Implementation (Friday, May 16th)

Given your time constraints and the desire to make meaningful progress by the end of today, I've structured this roadmap into a series of achievable tasks organized by component, with estimated time frames.

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

## 3. Database Layer Implementation (2-2.5 hours)

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

## 4. Attachment Processor Refinement (2 hours)

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

## 5. Basic Multimodal Reasoning Chain (2-3 hours)

- **Enhance Task Graph Generator**
  - Modify `working_task_graph_generator.py` to pull data from PostgreSQL
  - Update user prompt creation to include processed attachment data
  - Improve JSON structure alignment with target schema

- **Implement Basic Context Management**
  - Add methods to retrieve relevant attachments from database
  - Create simple priority system for including attachment data
  - Implement token counting to manage context size

- **Improve Response Handling**
  - Enhance JSON extraction and validation
  - Add basic error recovery mechanisms

## 6. Integration Testing (1.5-2 hours)

- **Create Test Bug Instances**
  - Prepare sample bugs with text, image, and PDF attachments
  
- **Build Integration Script**
  - Create `scripts/run_enhanced_pipeline.py` to test the full flow:
    1. Process attachments
    2. Store in PostgreSQL
    3. Generate task graph
    4. Export result to JSON

- **Test and Debug**
  - Execute with sample data
  - Verify database entries
  - Examine generated task graphs

## 7. Documentation Updates (30-45 min)

- **Update README.md**
  - Document new PostgreSQL requirement
  - Add setup instructions

- **Update Code Documentation**
  - Ensure all new methods have docstrings
  - Add comments for complex logic

## Timeline (Estimated)

| Time | Task |
|------|------|
| 3:30 PM - 4:15 PM | Version Control |
| 4:15 PM - 5:45 PM | PostgreSQL Setup & DB Layer Implementation |
| 5:45 PM - 6:30 PM | Dinner Break |
| 6:30 PM - 8:30 PM | Attachment Processor Refinement |
| 8:30 PM - 11:00 PM | Basic Multimodal Reasoning Chain & Integration Testing |
| 11:00 PM - 11:30 PM | Documentation Updates |

## Priority Order (If Time Becomes Limited)

1. Version Control (essential)
2. PostgreSQL Setup (essential)
3. Database Layer Implementation (essential)
4. Text Processor Enhancement (high priority)
5. Image Processor Enhancement (medium priority)
6. PDF Processor Enhancement (medium priority)
7. Basic Multimodal Reasoning Chain (high priority)
8. Integration Testing (essential)
9. Documentation Updates (if time permits)

This roadmap should be achievable with focused work into the evening, and delivers the core functionality you're targeting while leaving video processing for future development.
