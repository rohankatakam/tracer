#!/bin/bash

# Script to run the firefox search test with proper Docker container setup
# This script will:
# 1. Stop and remove existing Docker container if it exists
# 2. Start a new Docker container with the API key from .env
# 3. Run the test_firefox_search.py script

# Set script to exit immediately if any command fails
set -e

echo "=== Computer Use Demo TaskGraph Integration Test ==="
echo "Starting test sequence..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found. Please create one with your ANTHROPIC_API_KEY."
    exit 1
fi

# Load API key from .env file
export $(grep -v '^#' .env | xargs)

# Verify API key is loaded
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "Error: ANTHROPIC_API_KEY not found in .env file."
    exit 1
fi

echo "API key loaded successfully."

# Check if Docker container exists and remove it
echo "Checking for existing Docker container..."
if [ "$(docker ps -a -q -f name=anthropic-computer-use)" ]; then
    echo "Stopping and removing existing container..."
    docker stop anthropic-computer-use
    docker rm anthropic-computer-use
fi

# Start new Docker container
echo "Starting new Docker container with API key..."
docker run -d -p 5900:5900 -p 6080:6080 -p 8080:8080 -p 8501:8501 \
    -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
    --name anthropic-computer-use \
    ghcr.io/anthropics/anthropic-quickstarts:computer-use-demo-latest

# Wait for container to fully initialize
echo "Waiting for container to initialize (10 seconds)..."
sleep 10

# Run the test script
echo "Running Firefox search test..."
source venv/bin/activate
python test_firefox_search.py

echo "Test complete!"
