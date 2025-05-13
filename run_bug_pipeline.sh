#!/bin/bash

# This script runs the full pipeline for converting bug reports/test cases
# to a standardized format and then generating executable task graphs from them.

# Exit immediately if a command exits with a non-zero status.
set -e

# Define source file and format (can be parameterized later if needed)
SOURCE_INPUT_FILE="academybugs_bug_reports.json"
SOURCE_FORMAT="academybugs" # or 'juice_shop' if using that file

# Define output directories
STANDARDIZED_INPUT_DIR="data/standardized_inputs"
GENERATED_TASK_GRAPHS_DIR="data/task_graphs/generated"

# Ensure the output directories exist
echo "Ensuring output directories exist..."
mkdir -p "${STANDARDIZED_INPUT_DIR}"
mkdir -p "${GENERATED_TASK_GRAPHS_DIR}"

# Step 1: Convert source bug reports to standardized JSON input
echo "----------------------------------------------------------------------"
echo "Step 1: Converting source file (${SOURCE_INPUT_FILE}) to standardized input..."
echo "----------------------------------------------------------------------"
python3 -m src.scripts.convert_to_standard_input \
    --source_file "${SOURCE_INPUT_FILE}" \
    --source_format "${SOURCE_FORMAT}" \
    --output_dir "${STANDARDIZED_INPUT_DIR}"

if [ $? -ne 0 ]; then
    echo "Error: Conversion to standard input failed. Exiting."
    exit 1
fi

echo "Conversion complete. Standardized files are in ${STANDARDIZED_INPUT_DIR}"

# Step 2: Generate executable task graphs from standardized input
echo "----------------------------------------------------------------------"
echo "Step 2: Generating task graphs from standardized inputs..."
echo "----------------------------------------------------------------------"
python3 -m src.ingestion.task_graph_generator \
    --input_dir "${STANDARDIZED_INPUT_DIR}" \
    --output_dir "${GENERATED_TASK_GRAPHS_DIR}"

if [ $? -ne 0 ]; then
    echo "Error: Task graph generation failed. Exiting."
    exit 1
fi

echo "----------------------------------------------------------------------"
echo "Pipeline complete!"
echo "Generated task graphs are in ${GENERATED_TASK_GRAPHS_DIR}"
echo "----------------------------------------------------------------------"

# To make this script executable: chmod +x run_bug_pipeline.sh
# To run it: ./run_bug_pipeline.sh 