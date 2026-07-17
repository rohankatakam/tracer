#!/bin/bash
# Script to run the CUA tools with the correct Python path

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Add the root directory to the Python path
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"

# Use Python 3 by default; allow callers to override it when needed.
PYTHON_BIN="${PYTHON_BIN:-python3}"

# Check if the command is test-json-fix
if [ "$1" = "test-json-fix" ]; then
    echo "Running JSON serialization fix test..."
    "$PYTHON_BIN" "$SCRIPT_DIR/tests/test_json_utils.py"
    exit $?
fi

# Check if the command is test-pdf-processor
if [ "$1" = "test-pdf-processor" ]; then
    echo "Running PDF processor test..."
    if [ "$2" != "" ]; then
        "$PYTHON_BIN" "$SCRIPT_DIR/tests/integration/test_pdf_processor.py" "$2"
    else
        "$PYTHON_BIN" "$SCRIPT_DIR/tests/integration/test_pdf_processor.py"
    fi
    exit $?
fi

if [ "$1" = "direct-example" ]; then
    "$PYTHON_BIN" "$SCRIPT_DIR/src/main_controller.py"
    exit $?
fi

echo "Usage: $0 {test-json-fix|test-pdf-processor [pdf-path]|direct-example}"
exit 2
