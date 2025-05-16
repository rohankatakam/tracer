#!/bin/bash
# Cleanup script for Computer Use Agent codebase
# Based on previous cleanup notes

# Create backup directory
mkdir -p /Users/rohankatakam/Documents/cu/backup/old_files

# Files to delete based on previous cleanup notes
echo "Moving debug and test files to backup..."
# Debug and test files
mv /Users/rohankatakam/Documents/cu/test_chrome_search.py /Users/rohankatakam/Documents/cu/backup/old_files/ 2>/dev/null
mv /Users/rohankatakam/Documents/cu/test_firefox_search.py /Users/rohankatakam/Documents/cu/backup/old_files/ 2>/dev/null
mv /Users/rohankatakam/Documents/cu/test_enhanced_task_graph.py /Users/rohankatakam/Documents/cu/backup/old_files/ 2>/dev/null
mv /Users/rohankatakam/Documents/cu/debug_selenium.py /Users/rohankatakam/Documents/cu/backup/old_files/ 2>/dev/null
mv /Users/rohankatakam/Documents/cu/debug_chrome_agent.py /Users/rohankatakam/Documents/cu/backup/old_files/ 2>/dev/null
mv /Users/rohankatakam/Documents/cu/debug_task_execution.py /Users/rohankatakam/Documents/cu/backup/old_files/ 2>/dev/null
mv /Users/rohankatakam/Documents/cu/search_google.py /Users/rohankatakam/Documents/cu/backup/old_files/ 2>/dev/null
mv /Users/rohankatakam/Documents/cu/run_chrome_search.py /Users/rohankatakam/Documents/cu/backup/old_files/ 2>/dev/null
mv /Users/rohankatakam/Documents/cu/test_improved_agent.py /Users/rohankatakam/Documents/cu/backup/old_files/ 2>/dev/null
mv /Users/rohankatakam/Documents/cu/test_simple_task.py /Users/rohankatakam/Documents/cu/backup/old_files/ 2>/dev/null

# Clean up debug output directories
echo "Cleaning debug output directories..."
mkdir -p /Users/rohankatakam/Documents/cu/backup/debug_outputs
mv /Users/rohankatakam/Documents/cu/debug_output/* /Users/rohankatakam/Documents/cu/backup/debug_outputs/ 2>/dev/null
mv /Users/rohankatakam/Documents/cu/test_output/* /Users/rohankatakam/Documents/cu/backup/debug_outputs/ 2>/dev/null

# Clean up image and large data files
echo "Cleaning up image and large data files..."
mkdir -p /Users/rohankatakam/Documents/cu/backup/images
mv /Users/rohankatakam/Documents/cu/*.png /Users/rohankatakam/Documents/cu/backup/images/ 2>/dev/null
mv /Users/rohankatakam/Documents/cu/*.html /Users/rohankatakam/Documents/cu/backup/images/ 2>/dev/null

# Clean up unnecessary browser-related files
echo "Cleaning up browser-related files..."
mkdir -p /Users/rohankatakam/Documents/cu/backup/browser_files
mv /Users/rohankatakam/Documents/cu/src/chrome_browser_agent.py /Users/rohankatakam/Documents/cu/backup/browser_files/ 2>/dev/null
mv /Users/rohankatakam/Documents/cu/src/anthropic_client_image.py /Users/rohankatakam/Documents/cu/backup/browser_files/ 2>/dev/null
mv /Users/rohankatakam/Documents/cu/run_firefox_test.sh /Users/rohankatakam/Documents/cu/backup/browser_files/ 2>/dev/null

# Clean up large data directories
echo "Cleaning up large data directories..."
mkdir -p /Users/rohankatakam/Documents/cu/backup/data
mv /Users/rohankatakam/Documents/cu/data/chrome_search_test /Users/rohankatakam/Documents/cu/backup/data/ 2>/dev/null
mv /Users/rohankatakam/Documents/cu/data/outputs /Users/rohankatakam/Documents/cu/backup/data/ 2>/dev/null
mv /Users/rohankatakam/Documents/cu/data/temp /Users/rohankatakam/Documents/cu/backup/data/ 2>/dev/null

echo "Cleanup completed. Old files moved to /Users/rohankatakam/Documents/cu/backup"
