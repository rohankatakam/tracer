#!/bin/bash

# Bug Tracker Startup Script
# This script starts both the FastAPI backend and Next.js frontend services

# Colors for better output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Base project directory
BASE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
BACKEND_DIR="$BASE_DIR"
FRONTEND_DIR="$BASE_DIR/bug-tracker-frontend"

# Configuration
BACKEND_PORT=8080
FRONTEND_PORT=3000
API_URL="http://localhost:$BACKEND_PORT"

# Log file
LOG_FILE="$BASE_DIR/bug_tracker_startup.log"

# Cleanup function to terminate processes on exit
cleanup() {
  echo -e "${YELLOW}Shutting down services...${NC}"
  
  # Kill the backend server if it's running
  if [ ! -z "$BACKEND_PID" ] && kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "${YELLOW}Stopping backend server (PID: $BACKEND_PID)${NC}"
    kill -TERM $BACKEND_PID
  fi
  
  # Kill the frontend server if it's running
  if [ ! -z "$FRONTEND_PID" ] && kill -0 $FRONTEND_PID 2>/dev/null; then
    echo -e "${YELLOW}Stopping frontend server (PID: $FRONTEND_PID)${NC}"
    kill -TERM $FRONTEND_PID
  fi
  
  echo -e "${GREEN}All services stopped.${NC}"
}

# Set trap for cleanup on script exit
trap cleanup EXIT INT TERM

# Clear the log file
> "$LOG_FILE"

# Function to check if a port is in use
check_port() {
  local port=$1
  if lsof -i :$port > /dev/null; then
    return 0 # Port is in use
  else
    return 1 # Port is free
  fi
}

# Check if ports are already in use
if check_port $BACKEND_PORT; then
  echo -e "${RED}ERROR: Port $BACKEND_PORT is already in use. Please stop any service using this port.${NC}"
  exit 1
fi

if check_port $FRONTEND_PORT; then
  echo -e "${RED}ERROR: Port $FRONTEND_PORT is already in use. Please stop any service using this port.${NC}"
  exit 1
fi

# Function to wait for service to be available
wait_for_service() {
  local url=$1
  local service_name=$2
  local max_attempts=30
  local attempt=1
  
  echo -e "${YELLOW}Waiting for $service_name to be available...${NC}"
  
  while [ $attempt -le $max_attempts ]; do
    if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "2[0-9][0-9]\|3[0-9][0-9]"; then
      echo -e "${GREEN}$service_name is now available!${NC}"
      return 0
    fi
    
    echo -n "."
    sleep 1
    attempt=$((attempt+1))
  done
  
  echo -e "\n${RED}ERROR: $service_name did not become available within the timeout period.${NC}"
  return 1
}

# Start the backend server
echo -e "${YELLOW}Starting backend server on port $BACKEND_PORT...${NC}"
cd "$BACKEND_DIR"

# Check if we need to run in development or production mode
if [ -f "$BACKEND_DIR/requirements.txt" ]; then
  # Check if a virtual environment exists and activate it if found
  if [ -d "$BACKEND_DIR/venv" ]; then
    echo "Activating virtual environment..."
    source "$BACKEND_DIR/venv/bin/activate"
  fi
  
  # Start the backend server with the correct port
  uvicorn api.app:app --host 0.0.0.0 --port $BACKEND_PORT --reload >> "$LOG_FILE" 2>&1 &
  BACKEND_PID=$!
  
  if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR: Failed to start backend server. Check $LOG_FILE for details.${NC}"
    exit 1
  fi
  
  echo -e "${GREEN}Backend server started with PID: $BACKEND_PID${NC}"
else
  echo -e "${RED}ERROR: Backend directory structure incorrect. Make sure you're running this script from the project root.${NC}"
  exit 1
fi

# Wait for backend to be available
wait_for_service "http://localhost:$BACKEND_PORT/health" "Backend server"
if [ $? -ne 0 ]; then
  echo -e "${RED}ERROR: Backend server failed to start properly. Check $LOG_FILE for details.${NC}"
  exit 1
fi

# Start the frontend server
echo -e "${YELLOW}Starting frontend server on port $FRONTEND_PORT...${NC}"
cd "$FRONTEND_DIR"

# Check if package.json exists
if [ -f "$FRONTEND_DIR/package.json" ]; then
  # Set environment variable for API URL if needed
  export NEXT_PUBLIC_API_BASE_URL=$API_URL
  
  # Start the frontend development server
  npm run dev >> "$LOG_FILE" 2>&1 &
  FRONTEND_PID=$!
  
  if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR: Failed to start frontend server. Check $LOG_FILE for details.${NC}"
    exit 1
  fi
  
  echo -e "${GREEN}Frontend server started with PID: $FRONTEND_PID${NC}"
else
  echo -e "${RED}ERROR: Frontend directory structure incorrect. Make sure the frontend code is in the correct location.${NC}"
  exit 1
fi

# Wait for frontend to be available
wait_for_service "http://localhost:$FRONTEND_PORT" "Frontend server"
if [ $? -ne 0 ]; then
  echo -e "${RED}ERROR: Frontend server failed to start properly. Check $LOG_FILE for details.${NC}"
  exit 1
fi

# All services started successfully
echo -e "\n${GREEN}✓ Bug Tracker application started successfully!${NC}"
echo -e "${GREEN}✓ Backend API: ${NC}http://localhost:$BACKEND_PORT"
echo -e "${GREEN}✓ Frontend: ${NC}http://localhost:$FRONTEND_PORT"
echo -e "${GREEN}✓ API Documentation: ${NC}http://localhost:$BACKEND_PORT/docs"
echo -e "\n${YELLOW}Press Ctrl+C to stop all services${NC}"

# Keep the script running until user interrupts
wait $BACKEND_PID $FRONTEND_PID
