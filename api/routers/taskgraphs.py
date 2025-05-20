"""
Task Graph Router

This module provides API endpoints for generating task graphs from bug data.
"""

import os
import time
import json
import subprocess
from sqlalchemy.orm import Session
from fastapi import Depends
from api.dependencies import get_db_session
from core.repositories.bug_repository import BugRepository
from core.repositories.attachment_repository import AttachmentRepository
import shlex
import multiprocessing
from fastapi import APIRouter, HTTPException, BackgroundTasks, status, Request
from fastapi.responses import JSONResponse
from pathlib import Path
import logging
from datetime import datetime
import uuid
from pydantic import BaseModel
from typing import Dict, Any, Optional, List, Union
import traceback
import asyncio
from datetime import datetime
from multiprocessing import Queue
import queue

# Get the project root directory for resolving paths
PROJECT_ROOT = Path(os.path.dirname(os.path.abspath(__file__))).parent.parent
LLM_PROCESS_TIMEOUT = int(os.getenv("LLM_PROCESS_TIMEOUT", "120")) # Default to 120 seconds

# Configure logging - use a specific logger for taskgraphs with file output
logger = logging.getLogger('taskgraphs')
logger.setLevel(logging.DEBUG)

# Add file handler to keep detailed logs
log_file = os.path.join(PROJECT_ROOT, 'taskgraph_generation.log')
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Also add console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

router = APIRouter(
    prefix="/taskgraphs",
    tags=["taskgraphs"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"},
        504: {"description": "Timeout error"}
    },
)

# Store task graph generation results
TASK_GRAPH_RESULTS = {}  # id -> result mapping

class TaskGraphStatus(BaseModel):
    id: str
    bug_id: str
    status: str
    created_at: str
    completed_at: Optional[str] = None
    error: Optional[str] = None

class TaskGraphResponse(BaseModel):
    id: str
    bug_id: str
    status: str
    message: str
    task_graph: Optional[Dict[str, Any]] = None

def _format_bug_data_for_llm(bug_data_dict: dict) -> str:
    """
    Formats the bug data dictionary into a concise string for LLM consumption.
    """
    if not bug_data_dict:
        return "No bug data provided."

    details = []
    
    # Helper to safely access and format datetime objects
    def format_datetime_val(dt_obj):
        # Assumes 'from datetime import datetime' is present at the top of the file
        if isinstance(dt_obj, datetime): 
            return dt_obj.isoformat()
        elif isinstance(dt_obj, str): # If already string, return as is
            return dt_obj
        return "N/A"

    details.append(f"Bug ID: {bug_data_dict.get('id', 'N/A')}")
    details.append(f"Name: {bug_data_dict.get('name', 'N/A')}")
    details.append(f"Description: {bug_data_dict.get('description', 'N/A')}")
    details.append(f"Status: {bug_data_dict.get('status', 'N/A')}")
    details.append(f"Priority: {bug_data_dict.get('priority', 'N/A')}")
    details.append(f"Severity: {bug_data_dict.get('severity', 'N/A')}")
    details.append(f"Created At: {format_datetime_val(bug_data_dict.get('created_at'))}")
    details.append(f"Updated At: {format_datetime_val(bug_data_dict.get('updated_at'))}")
    details.append(f"Attachment Count: {bug_data_dict.get('attachment_count', 0)}")

    extra_data = bug_data_dict.get("extra_data", {})
    if isinstance(extra_data, dict):
        details.append(f"Summary (from extra_data): {extra_data.get('summary', 'N/A')}")
        details.append(f"Reproduction Steps (from extra_data): {extra_data.get('reproduction_steps', 'N/A')}")
        details.append(f"Environment (from extra_data): {extra_data.get('environment', 'N/A')}")
        details.append(f"Expected Result (from extra_data): {extra_data.get('expected_result', 'N/A')}")
        details.append(f"Actual Result (from extra_data): {extra_data.get('actual_result', 'N/A')}")
    else: 
        # Assuming logger is defined and imported in the file scope (e.g., logger = logging.getLogger(__name__))
        logger.warning(f"extra_data for bug {bug_data_dict.get('id')} is not a dictionary. Skipping extra_data fields.")

    return "\n".join(details)


def _fetch_bug_details_from_db(bug_id: str, db: Session) -> dict:
    """
    Fetch bug details directly from the database.
    Mirrors logic from api.routers.bugs.get_bug.
    """
    logger.info(f"Fetching bug details from DB for bug_id: {bug_id}")
    try:
        repo = BugRepository(db)
        bug_data = repo.get_bug_by_id(bug_id)
        if not bug_data:
            # Not raising HTTPException here as this is an internal function.
            # The caller (main endpoint) should handle this.
            logger.error(f"Bug with ID {bug_id} not found in DB.")
            return None

        # bug_data is already a dictionary from get_bug_by_id
        
        # Add attachment count
        attachment_repo = AttachmentRepository(db)
        attachments = attachment_repo.get_attachments_by_bug_id(bug_id)
        bug_data["attachment_count"] = len(attachments)
        
        # Ensure extra_data is a dictionary (it should be if coming from BugRepository)
        if "extra_data" in bug_data and isinstance(bug_data["extra_data"], str):
            try:
                bug_data["extra_data"] = json.loads(bug_data["extra_data"])
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse extra_data for bug {bug_id}. Defaulting to empty dict.")
                bug_data["extra_data"] = {}
        elif bug_data.get("extra_data") is None:
             bug_data["extra_data"] = {}

        logger.info(f"Successfully fetched bug details from DB for bug_id: {bug_id}")
        return bug_data
    except Exception as e:
        logger.error(f"Error fetching bug details from DB for {bug_id}: {str(e)}\n{traceback.format_exc()}")
        # Propagate error to be handled by the caller
        raise

def call_llm_generate_process(bug_data_text: str, schema_file: str, system_instruction_file: str, prompt_template_file: str) -> dict:
    """
    Calls the LLM generation process using pre-fetched and formatted bug data (as a string).
    This function is intended to be run in a separate process.
    """
    logger.info("Inside call_llm_generate_process with pre-fetched and formatted bug data string")
    try:
        # Using the core generator directly, not the bug_api_generator
        from core.gemini.bug_reproduction.generator import generate_bug_reproduction_graph
        from dotenv import load_dotenv, find_dotenv

        load_dotenv(find_dotenv()) # Ensure .env is loaded for API keys if generator relies on it.
        
        logger.info(f"Schema file: {schema_file}")
        logger.info(f"System instruction file: {system_instruction_file}")
        logger.info(f"Prompt template file: {prompt_template_file}")

        if not os.path.exists(schema_file):
            raise FileNotFoundError(f"Schema file not found: {schema_file}")
        if not os.path.exists(system_instruction_file):
            raise FileNotFoundError(f"System instruction file not found: {system_instruction_file}")
        if not os.path.exists(prompt_template_file):
            raise FileNotFoundError(f"Prompt template file not found: {prompt_template_file}")

        logger.info("Calling core.gemini.bug_reproduction.generator.generate_bug_reproduction_graph")
        # The core generator expects 'github_issue_json' which is our bug_data_json_str
        task_graph_str = generate_bug_reproduction_graph(
            bug_data_text=bug_data_text, # This will match the updated generator.py parameter
            schema_file=schema_file,
            system_instruction_file=system_instruction_file,
            prompt_template_file=prompt_template_file
        )
        
        logger.info("Raw task_graph_str from LLM (first 500 chars):")
        logger.info(task_graph_str[:500] + "...")

        task_graph = json.loads(task_graph_str)
        logger.info("Successfully generated and parsed task graph.")
        return task_graph

    except json.JSONDecodeError as e:
        llm_output_snippet = task_graph_str[:500] + "..." if 'task_graph_str' in locals() and task_graph_str else "[LLM output was empty or None]"
        error_msg = f"Failed to parse JSON from LLM: {str(e)}. LLM Output: {llm_output_snippet}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    except FileNotFoundError as e:
        logger.error(f"File not found in call_llm_generate_process: {str(e)}")
        raise
    except Exception as e:
        error_msg = f"Error in LLM generation process: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)


# Custom JSON serializer for datetime objects
def json_datetime_serializer(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

def _generate_task_graph_process_wrapper(formatted_bug_string: str, task_id: str, original_bug_id: str, result_queue: Queue, schema_file: str, system_instruction_file: str, prompt_template_file: str):
    """
    Runs the generation script in a separate process to ensure the API server doesn't hang.
    This function is designed to be run in a separate process.
    """
    logger.info(f"Process wrapper started for task ID: {task_id}, original bug ID: {original_bug_id}")
    try:
        # formatted_bug_string is now passed directly.
        logger.info(f"Calling LLM generate process with formatted bug data string for task ID: {task_id}")
        task_graph = call_llm_generate_process(
            bug_data_text=formatted_bug_string,  # Pass the formatted string with new arg name
            schema_file=schema_file,
            system_instruction_file=system_instruction_file,
            prompt_template_file=prompt_template_file
        )
        logger.info(f"LLM process completed for task ID: {task_id}. Sending result to queue.")
        result_queue.put({"status": "completed", "task_graph": task_graph, "error": None})

    # Keep existing specific error handling for errors from call_llm_generate_process
    except ValueError as e: # Handles JSONDecodeError from call_llm_generate_process or json.dumps issues
        logger.error(f"Data or LLM output processing error in process for task ID {task_id}: {e}")
        result_queue.put({"status": "failed", "task_graph": None, "error": str(e)})
    except FileNotFoundError as e:
        logger.error(f"Configuration file not found in process for task ID {task_id}: {e}")
        result_queue.put({"status": "failed", "task_graph": None, "error": f"Configuration file missing: {e}"})
    except RuntimeError as e: # Catches generic errors from call_llm_generate_process
        logger.error(f"Runtime error from LLM generation in process for task ID {task_id}: {e}")
        result_queue.put({"status": "failed", "task_graph": None, "error": str(e)})
    except Exception as e:
        error_detail = f"Unhandled exception in generation process for task ID {task_id}: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_detail)
        result_queue.put({"status": "failed", "task_graph": None, "error": error_detail})

async def _generate_task_graph_async(formatted_bug_string: str, task_id: str, original_bug_id: str):
    logger.info(f"Starting background task for task ID: {task_id}, original bug ID: {original_bug_id}")
    # Initialize task result with created_at timestamp
    created_at_iso = datetime.now().isoformat()
    TASK_GRAPH_RESULTS[task_id] = {
        "id": task_id,
        "bug_id": original_bug_id,
        "status": "processing", 
        "created_at": created_at_iso,
        "task_graph": None,
        "error": None
    }
    
    p = None # Initialize process variable
    final_status = "error" # Default final status
    error_message = "An unexpected error occurred in the async task manager."
    task_graph_result = None

    try:
        # Base path for Gemini assets, assuming a subfolder structure
        base_path = os.path.join(PROJECT_ROOT, "core", "gemini")
        schema_file = os.path.abspath(os.path.join(base_path, "schemas", "bug_reproduction_graph_schema_v2.json"))
        system_instruction_file = os.path.abspath(os.path.join(base_path, "templates", "system_instructions", "system_instruction_bug_graph_v2.md"))
        prompt_template_file = os.path.abspath(os.path.join(base_path, "templates", "prompt_templates", "chat_prompt_template_bug_graph_v2.md"))

        # Verify paths
        for f_path, f_name in [(schema_file, "Schema"), (system_instruction_file, "System instruction"), (prompt_template_file, "Prompt template")]:
            if not os.path.exists(f_path):
                raise FileNotFoundError(f"{f_name} file not found: {f_path}")

        result_queue = Queue() # Uses 'from multiprocessing import Queue'
        
        p = multiprocessing.Process(
            target=_generate_task_graph_process_wrapper,
            args=(formatted_bug_string, task_id, original_bug_id, result_queue, schema_file, system_instruction_file, prompt_template_file)
        )
        p.start()
        logger.info(f"Process {p.pid} started for task ID: {task_id}")

        try:
            # Blocking get with timeout
            result = result_queue.get(timeout=LLM_PROCESS_TIMEOUT) 
            final_status = result.get("status", "failed")
            task_graph_result = result.get("task_graph")
            error_message = result.get("error")
            if final_status == "completed":
                 logger.info(f"LLM process completed successfully for task ID: {task_id}")
                 error_message = None # Clear error on success
            else:
                 logger.error(f"LLM process failed for task ID: {task_id}. Error: {error_message}")

        except queue.Empty: # Handle timeout for queue.get() - needs 'import queue'
            logger.error(f"Timeout ({LLM_PROCESS_TIMEOUT}s) waiting for LLM process for task ID: {task_id}. Terminating process.")
            final_status = "timeout"
            error_message = f"LLM generation process timed out after {LLM_PROCESS_TIMEOUT} seconds."
            if p.is_alive():
                logger.warning(f"Terminating process {p.pid} for task ID {task_id} due to timeout.")
                p.terminate() # Send SIGTERM
                p.join(timeout=5) # Wait for graceful termination
                if p.is_alive():
                    logger.warning(f"Process {p.pid} for task ID {task_id} still alive after SIGTERM. Sending SIGKILL.")
                    p.kill() # Force kill
                    p.join(timeout=2) # Wait for kill confirmation
        finally:
            # Ensure process is cleaned up
            if p and p.is_alive(): 
                logger.warning(f"Process {p.pid} for task ID {task_id} might still be alive at end of try/except block. Ensuring termination.")
                if not p.exitcode: # Only terminate if not already exited
                    p.terminate()
                    p.join(timeout=2)
                if p.is_alive(): 
                    p.kill()
                    p.join(timeout=1)
            if p: # Ensure p is not None
                p.join() # Final join to clean up resources if process exited or was killed

    except FileNotFoundError as e:
        final_status = "failed"
        error_message = str(e)
        logger.error(f"Configuration file error for task ID {task_id}: {error_message}")
    except Exception as e:
        final_status = "error" 
        error_message = f"Unhandled exception in async task manager for task {task_id}: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_message)
    finally:
        # Update TASK_GRAPH_RESULTS with the final outcome
        update_data = {
            "status": final_status,
            "task_graph": task_graph_result,
            "completed_at": datetime.now().isoformat()
        }
        
        # Only include error_message if it's not None
        if error_message is not None:
            update_data["error"] = error_message
        
        TASK_GRAPH_RESULTS[task_id].update(update_data)
        logger.info(f"Async task processing finished for task ID: {task_id} (original bug ID: {original_bug_id}) with status: {final_status}")

@router.post("/generate/{bug_id}", response_model=TaskGraphResponse)
async def generate_task_graph(bug_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db_session)):
    """
    Generate a task graph for the specified bug.
    
    Args:
        bug_id: The ID of the bug to generate a task graph for
        background_tasks: FastAPI background tasks
        db: SQLAlchemy database session
        
    Returns:
        JSON response with the generated task graph
    """
    try:
        # Fetch bug data directly from the database
        logger.info(f"Attempting to fetch bug data from DB for bug ID: {bug_id} before starting background task.")
        bug_data_dict = _fetch_bug_details_from_db(bug_id, db)

        if not bug_data_dict:
            logger.error(f"Failed to fetch bug data from DB for bug_id: {bug_id}. Cannot start task graph generation.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bug with ID {bug_id} not found, cannot generate task graph."
            )
        
        logger.info(f"Successfully fetched bug data from DB for bug ID: {bug_id}.")

        # NEW: Format bug data for LLM
        formatted_bug_string = _format_bug_data_for_llm(bug_data_dict)
        logger.info(f"Formatted bug data string for LLM for bug ID: {bug_id}")

        # Generate a unique task ID
        task_id = str(uuid.uuid4())
        logger.info(f"Initiating task graph generation for bug ID: {bug_id}, new task ID: {task_id}")
        
        # Add the task to background tasks, passing the fetched bug_data_dict
        # Also pass original_bug_id for tracking/logging in the async task and process wrapper
        background_tasks.add_task(_generate_task_graph_async, formatted_bug_string, task_id, bug_id)
        
        # Return immediate response with task ID
        return TaskGraphResponse(
            id=task_id,
            bug_id=bug_id, # Original bug_id
            status="pending",
            message="Task graph generation has been started. Check status endpoint for results.",
            task_graph=None
        )
    except Exception as e:
        error_msg = f"Error initiating task graph generation: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/status/{task_id}", response_model=TaskGraphResponse)
async def get_task_graph_status(task_id: str):
    """
    Get the status of a task graph generation task.
    
    Args:
        task_id: The ID of the task to check status for
        
    Returns:
        JSON response with the task status and result if available
    """
    try:
        logger.info(f"Checking status for task ID: {task_id}")
        
        # Check if the task exists
        if task_id not in TASK_GRAPH_RESULTS:
            raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
        
        # Get the task result
        result = TASK_GRAPH_RESULTS[task_id]
        
        # Return the result
        status = result.get('status', 'unknown')
        
        # Prepare a default message based on status if error is not present
        if 'error' in result and result['error'] is not None:
            message = result['error']
        elif status == 'completed':
            message = 'Task completed successfully'
        else:
            message = f'Task is {status}'
        
        return TaskGraphResponse(
            id=task_id,
            bug_id=result.get('bug_id', ''),
            status=status,
            message=message,
            task_graph=result.get('task_graph')
        )
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Error checking task status: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
