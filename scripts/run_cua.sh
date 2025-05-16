#!/bin/bash
# Script to run the CUA tools with the correct Python path

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Add the root directory to the Python path
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"

# Check if the command is test-json-fix
if [ "$1" = "test-json-fix" ]; then
    echo "Running JSON serialization fix test..."
    python "$SCRIPT_DIR/tests/integration/test_json_fix.py"
    exit $?
fi

# Check if the command is test-pdf-processor
if [ "$1" = "test-pdf-processor" ]; then
    echo "Running PDF processor test..."
    if [ "$2" != "" ]; then
        python "$SCRIPT_DIR/tests/integration/test_pdf_processor.py" "$2"
    else
        python "$SCRIPT_DIR/tests/integration/test_pdf_processor.py"
    fi
    exit $?
fi

# Run the standard CLI with all arguments passed to this script
python "$SCRIPT_DIR/src/cli.py" "$@"
