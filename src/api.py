import os
import sys
# from flask import Flask, jsonify, abort # Remove Flask imports
# from flask_cors import CORS # Remove Flask-CORS
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse # For more control if needed, but often not necessary
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool # Add this import

from pathlib import Path
import logging
import uvicorn # Add Uvicorn import

# Add src directory to Python path to allow importing modules like task_graph_generator
project_root = Path(__file__).parent.parent.resolve() # project_root is one level up from src
sys.path.append(str(project_root))

# Now we can import from other modules in src using src.* paths
try:
    from src.ingestion.task_graph_generator import generate_task_graph_from_raw_data # TaskGraphGenerator class might not be needed here
    from src.utils.json_utils import load_json
    from src.utils.logging_utils import setup_logging
except ImportError as e:
    print(f"Error importing modules: {e}", file=sys.stderr)
    print(f"Current sys.path: {sys.path}", file=sys.stderr)
    # Fallback or re-raise, depending on how critical these are at startup
    # For now, let it proceed, but API calls will fail if these aren't loaded.
    generate_task_graph_from_raw_data = None
    load_json = None
    setup_logging = None 

# app = Flask(__name__)
# CORS(app) # Remove Flask CORS setup
app = FastAPI(title="Bug Task Graph API")

# Add FastAPI CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins. For production, restrict this to your frontend's domain.
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods.
    allow_headers=["*"],  # Allows all headers.
)

# Configure basic logging for the API (setup_logging should ideally be available)
log_dir = project_root / 'logs' / 'api' # Adjust log path relative to project_root
os.makedirs(log_dir, exist_ok=True)
logger = setup_logging("api_server", str(log_dir), logging.INFO) if setup_logging else logging.getLogger("api_server_fallback")

# Define the base directory for input data
DEFAULT_INPUT_DIR = project_root / "data" / "standardized_inputs"
DEFAULT_TASK_GRAPH_OUTPUT_DIR = project_root / "data" / "task_graphs" / "generated" # For caching
DEFAULT_TASK_GRAPH_OUTPUT_DIR.mkdir(parents=True, exist_ok=True) # Ensure it exists

# @app.route('/api/bugs/<string:bug_id>/task_graph', methods=['GET'])
@app.get("/api/bugs/{bug_id}/task_graph") # FastAPI route decorator
async def get_task_graph(bug_id: str): # Use async def for FastAPI routes if they involve I/O
    logger.info(f"Received request for task graph for bug_id: {bug_id}")

    if not generate_task_graph_from_raw_data or not load_json:
         logger.error("Core generation/loading functions not imported correctly.")
         raise HTTPException(status_code=500, detail="Internal server error: Core functions not available.")

    # # --- Caching Logic --- 
    # cached_graph_file_name = f"{bug_id}_task_graph.json"
    # cached_graph_path = DEFAULT_TASK_GRAPH_OUTPUT_DIR / cached_graph_file_name

    # if cached_graph_path.is_file():
    #     try:
    #         logger.info(f"Returning cached task graph for {bug_id} from {cached_graph_path}")
    #         cached_data = load_json(str(cached_graph_path))
    #         # Ensure the cached data is the task_graph part itself, or adjust as needed.
    #         # If generate_task_graph_from_raw_data saves the whole result object, 
    #         # then the API should return result.get("task_graph") from cache too.
    #         # For now, assuming the file IS the task_graph.
    #         # Let's assume the file contains the direct task_graph object as expected by frontend
    #         return cached_data 
    #     except Exception as e:
    #         logger.warning(f"Error loading cached task graph for {bug_id} from {cached_graph_path}: {e}. Will regenerate.")
    # # --- End Caching Logic ---

    input_file_name = f"{bug_id}_standard.json"
    input_file_path = DEFAULT_INPUT_DIR / input_file_name
    logger.info(f"Looking for input file: {input_file_path}")

    if not input_file_path.is_file():
        logger.error(f"Input file not found: {input_file_path}")
        raise HTTPException(status_code=404, detail=f"Standardized input file not found for bug ID: {bug_id}")

    try:
        result = await run_in_threadpool(
            generate_task_graph_from_raw_data,
            raw_data_package_path=str(input_file_path),
            output_dir=str(DEFAULT_TASK_GRAPH_OUTPUT_DIR) # Ensure generator saves to cache location
        )
        task_graph = result.get("task_graph")

        if not task_graph or task_graph.get("status") == "failed":
            error_message = task_graph.get("error", "Unknown error during generation")
            logger.error(f"Task graph generation failed for {bug_id}: {error_message}")
            raise HTTPException(status_code=500, detail=f"Task graph generation failed: {error_message}")

        logger.info(f"Successfully generated and cached task graph for {bug_id}")
        return task_graph # FastAPI handles JSON conversion
    except FileNotFoundError: # Should be caught by the earlier check, but as a safeguard
         logger.error(f"Input file disappeared (race condition?): {input_file_path}")
         raise HTTPException(status_code=404, detail=f"Input file not found for bug ID: {bug_id}")
    except ImportError as e: # Should also be caught early
         logger.critical(f"Import error during runtime: {e}")
         raise HTTPException(status_code=500, detail="Internal server error: Failed to load necessary modules.")
    except Exception as e:
        logger.error(f"Unexpected error generating task graph for {bug_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

# @app.route('/api/bugs', methods=['GET'])
@app.get("/api/bugs")
async def list_bugs():
    logger.info("Received request to list bugs.")
    bugs_list = []
    try:
        if not DEFAULT_INPUT_DIR.is_dir():
            logger.error(f"Standardized input directory not found: {DEFAULT_INPUT_DIR}")
            return [] # Return empty list

        logger.info(f"Scanning for *.json files in {DEFAULT_INPUT_DIR}")
        # Convert glob to list to avoid issues with async iteration if any
        input_files = list(DEFAULT_INPUT_DIR.glob("*_standard.json"))
        
        for input_file_path in input_files:
            current_bug_id = input_file_path.name.replace("_standard.json", "")
            bug_info = {"id": current_bug_id}
            try:
                file_data = await run_in_threadpool(load_json, str(input_file_path))
                metadata = file_data.get('bug_metadata', {})
                bug_info['title'] = metadata.get('bug_title', f'Title N/A for {current_bug_id}')
                bug_info['severity'] = metadata.get('severity', {}).get('description', 'Severity N/A')
                status_obj = metadata.get('status', {})
                bug_info['status'] = status_obj.get('description', 'Status N/A') if isinstance(status_obj, dict) else status_obj
                bug_info['product'] = metadata.get('product', {}).get('name', 'Product N/A')
            except Exception as e:
                logger.warning(f"Could not load/parse metadata for {current_bug_id} from {input_file_path}: {e}")
                bug_info.setdefault('title', f'Error Loading Title for {current_bug_id}')
                bug_info.setdefault('severity', 'N/A')
                bug_info.setdefault('status', 'N/A')
                bug_info.setdefault('product', 'N/A')
            bugs_list.append(bug_info)

        logger.info(f"Found {len(bugs_list)} bugs: {bugs_list}")
        bugs_list.sort(key=lambda x: x['id'])
        return bugs_list
    except Exception as e:
        logger.error(f"Error scanning bug directory {DEFAULT_INPUT_DIR}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list available bugs.")

# @app.route('/api/bugs/<string:bug_id>', methods=['GET'])
@app.get("/api/bugs/{bug_id}")
async def get_bug_details(bug_id: str):
    logger.info(f"Received request for details for bug_id: {bug_id}")
    input_file_name = f"{bug_id}_standard.json"
    input_file_path = DEFAULT_INPUT_DIR / input_file_name
    logger.info(f"Looking for input file: {input_file_path}")

    if not input_file_path.is_file():
        logger.error(f"Input file not found for details: {input_file_path}")
        raise HTTPException(status_code=404, detail=f"Standardized input file not found for bug ID: {bug_id}")

    try:
        bug_data = await run_in_threadpool(load_json, str(input_file_path))
        logger.info(f"Successfully loaded details for bug_id: {bug_id}")
        return bug_data
    except Exception as e:
        logger.error(f"Error loading bug details for {bug_id} from {input_file_path}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to load bug details: {str(e)}")

# if __name__ == '__main__':
#     logger.info("Starting Flask development server...")
#     app.run(host='0.0.0.0', port=5001, debug=True)

if __name__ == "__main__":
    logger.info("Starting Uvicorn server for FastAPI...")
    # When running with uvicorn CLI, use "src.api:app" --reload
    # For programmatic start:
    uvicorn.run(app, host="0.0.0.0", port=5001, log_level="info") 