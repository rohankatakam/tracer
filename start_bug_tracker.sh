#!/bin/bash

# Bug Tracker Startup Script
# This script starts both the FastAPI backend and Next.js frontend services
# It can also start just the frontend, just the backend, or stop all processes

# Colors for better output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
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
VERBOSE_LOGGING=false

# Display help information
show_help() {
  echo -e "\n${BLUE}Bug Tracker Startup Script${NC}"
  echo -e "Usage: $0 [options]"
  echo -e "\nOptions:"
  echo -e "  ${GREEN}--all${NC}            Start both backend and frontend (default)"
  echo -e "  ${GREEN}--backend${NC}        Start only the backend server"
  echo -e "  ${GREEN}--frontend${NC}       Start only the frontend server"
  echo -e "  ${GREEN}--stop${NC}           Stop all running services"
  echo -e "  ${GREEN}--verbose${NC}        Enable detailed logging"
  echo -e "  ${GREEN}--help${NC}           Display this help message"
  echo -e "\nExamples:"
  echo -e "  $0                  # Start both services"
  echo -e "  $0 --backend        # Start only the backend"
  echo -e "  $0 --frontend       # Start only the frontend"
  echo -e "  $0 --stop           # Stop all services"
  echo -e "  $0 --all --verbose  # Start all with verbose logging"
  echo -e ""
}

# Function for logging
log() {
  local level=$1
  local message=$2
  local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
  
  # Always log to file
  echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
  
  # Format console output based on level
  case $level in
    "INFO")
      echo -e "${GREEN}[INFO]${NC} $message"
      ;;
    "WARN")
      echo -e "${YELLOW}[WARN]${NC} $message"
      ;;
    "ERROR")
      echo -e "${RED}[ERROR]${NC} $message"
      ;;
    "DEBUG")
      if [ "$VERBOSE_LOGGING" = true ]; then
        echo -e "${BLUE}[DEBUG]${NC} $message"
      fi
      ;;
    *)
      echo -e "[$level] $message"
      ;;
  esac
}

# Terminate running services
stop_services() {
  log "INFO" "Stopping all services..."
  
  # Find and stop backend processes
  BACKEND_PROCESSES=$(lsof -i :$BACKEND_PORT -t 2>/dev/null)
  if [ ! -z "$BACKEND_PROCESSES" ]; then
    log "INFO" "Stopping backend server(s) on port $BACKEND_PORT (PIDs: $BACKEND_PROCESSES)"
    kill -15 $BACKEND_PROCESSES 2>/dev/null
    sleep 2
    # Force kill if still running
    REMAINING=$(lsof -i :$BACKEND_PORT -t 2>/dev/null)
    if [ ! -z "$REMAINING" ]; then
      log "WARN" "Force killing remaining backend processes (PIDs: $REMAINING)"
      kill -9 $REMAINING 2>/dev/null
    fi
  else
    log "INFO" "No backend processes found running on port $BACKEND_PORT"
  fi
  
  # Find and stop frontend processes
  FRONTEND_PROCESSES=$(lsof -i :$FRONTEND_PORT -t 2>/dev/null)
  if [ ! -z "$FRONTEND_PROCESSES" ]; then
    log "INFO" "Stopping frontend server(s) on port $FRONTEND_PORT (PIDs: $FRONTEND_PROCESSES)"
    kill -15 $FRONTEND_PROCESSES 2>/dev/null
    sleep 2
    # Force kill if still running
    REMAINING=$(lsof -i :$FRONTEND_PORT -t 2>/dev/null)
    if [ ! -z "$REMAINING" ]; then
      log "WARN" "Force killing remaining frontend processes (PIDs: $REMAINING)"
      kill -9 $REMAINING 2>/dev/null
    fi
  else
    log "INFO" "No frontend processes found running on port $FRONTEND_PORT"
  fi
  
  # Verify all are stopped
  if [ -z "$(lsof -i :$BACKEND_PORT -t 2>/dev/null)" ] && [ -z "$(lsof -i :$FRONTEND_PORT -t 2>/dev/null)" ]; then
    log "INFO" "All services successfully stopped"
    return 0
  else
    log "ERROR" "Failed to stop all services"
    return 1
  fi
}

# Cleanup function to terminate processes on exit
cleanup() {
  log "INFO" "Shutting down services..."
  
  # Kill the backend server if it's running
  if [ ! -z "$BACKEND_PID" ] && kill -0 $BACKEND_PID 2>/dev/null; then
    log "INFO" "Stopping backend server (PID: $BACKEND_PID)"
    kill -TERM $BACKEND_PID
  fi
  
  # Kill the frontend server if it's running
  if [ ! -z "$FRONTEND_PID" ] && kill -0 $FRONTEND_PID 2>/dev/null; then
    log "INFO" "Stopping frontend server (PID: $FRONTEND_PID)"
    kill -TERM $FRONTEND_PID
  fi
  
  log "INFO" "All services stopped."
}

# Function to check if a port is in use
check_port() {
  local port=$1
  if lsof -i :$port > /dev/null; then
    return 0 # Port is in use
  else
    return 1 # Port is free
  fi
}

# Parse command line arguments
START_BACKEND=false
START_FRONTEND=false
STOP_SERVICES=false

# If no arguments, start both services by default
if [ $# -eq 0 ]; then
  START_BACKEND=true
  START_FRONTEND=true
fi

# Parse arguments
while [ $# -gt 0 ]; do
  case "$1" in
    --help)
      show_help
      exit 0
      ;;
    --all)
      START_BACKEND=true
      START_FRONTEND=true
      ;;
    --backend)
      START_BACKEND=true
      ;;
    --frontend)
      START_FRONTEND=true
      ;;
    --stop)
      STOP_SERVICES=true
      ;;
    --verbose)
      VERBOSE_LOGGING=true
      ;;
    *)
      log "ERROR" "Unknown option: $1"
      show_help
      exit 1
      ;;
  esac
  shift
done

# Set trap for cleanup on script exit - only if we're starting services
if [ "$START_BACKEND" = true ] || [ "$START_FRONTEND" = true ]; then
  trap cleanup EXIT INT TERM
fi

# Initialize or rotate logs
if [ -f "$LOG_FILE" ] && [ $(stat -f%z "$LOG_FILE") -gt 1048576 ]; then
  # If log file is larger than 1MB, rotate it
  mv "$LOG_FILE" "${LOG_FILE}.old"
fi

# Create new log file with header
echo "=== Bug Tracker Startup Log ($(date)) ===" > "$LOG_FILE"

# Stop services if requested
if [ "$STOP_SERVICES" = true ]; then
  log "INFO" "Stopping all services as requested"
  stop_services
  exit $?
fi

# Check if ports are already in use if we're starting services
if [ "$START_BACKEND" = true ] && check_port $BACKEND_PORT; then
  log "ERROR" "Port $BACKEND_PORT is already in use. Please stop any service using this port."
  exit 1
fi

if [ "$START_FRONTEND" = true ] && check_port $FRONTEND_PORT; then
  log "ERROR" "Port $FRONTEND_PORT is already in use. Please stop any service using this port."
  exit 1
fi

# Function to wait for service to be available
wait_for_service() {
  local url=$1
  local service_name=$2
  local max_attempts=30
  local attempt=1
  
  log "INFO" "Waiting for $service_name to be available..."
  
  while [ $attempt -le $max_attempts ]; do
    log "DEBUG" "Attempt $attempt/$max_attempts: Checking $url"
    if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "2[0-9][0-9]\|3[0-9][0-9]"; then
      log "INFO" "$service_name is now available!"
      return 0
    fi
    
    echo -n "."
    sleep 1
    attempt=$((attempt+1))
  done
  
  log "ERROR" "$service_name did not become available within the timeout period"
  return 1
}

# Start the backend server if requested
start_backend() {
  log "INFO" "Starting backend server on port $BACKEND_PORT..."
  cd "$BACKEND_DIR"

  # Check if we need to run in development or production mode
  if [ -f "$BACKEND_DIR/requirements.txt" ]; then
    # Check if a virtual environment exists and activate it if found
    if [ -d "$BACKEND_DIR/venv" ]; then
      log "INFO" "Activating virtual environment..."
      source "$BACKEND_DIR/venv/bin/activate"
    fi
    
    # Start the backend server with the correct port
    log "DEBUG" "Starting uvicorn with command: uvicorn api.app:app --host 0.0.0.0 --port $BACKEND_PORT --reload"
    uvicorn api.app:app --host 0.0.0.0 --port $BACKEND_PORT --reload >> "$LOG_FILE" 2>&1 &
    BACKEND_PID=$!
    
    if [ $? -ne 0 ]; then
      log "ERROR" "Failed to start backend server. Check $LOG_FILE for details."
      return 1
    fi
    
    log "INFO" "Backend server started with PID: $BACKEND_PID"
  else
    log "ERROR" "Backend directory structure incorrect. Make sure you're running this script from the project root."
    return 1
  fi

  # Wait for backend to be available
  wait_for_service "http://localhost:$BACKEND_PORT/health" "Backend server"
  if [ $? -ne 0 ]; then
    log "ERROR" "Backend server failed to start properly. Check $LOG_FILE for details."
    return 1
  fi
  
  return 0
}

# Start the frontend server if requested
start_frontend() {
  # Only start the frontend if the backend is running or we're explicitly only starting the frontend
  if [ "$START_BACKEND" = false ] && [ -z "$(lsof -i :$BACKEND_PORT -t 2>/dev/null)" ]; then
    log "WARN" "No backend server detected on port $BACKEND_PORT. The frontend may not function correctly."
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      log "INFO" "Frontend startup canceled by user"
      return 1
    fi
  fi

  log "INFO" "Starting frontend server on port $FRONTEND_PORT..."
  cd "$FRONTEND_DIR"

  # Check if package.json exists
  if [ -f "$FRONTEND_DIR/package.json" ]; then
    # Set environment variable for API URL if needed
    export NEXT_PUBLIC_API_BASE_URL=$API_URL
    log "DEBUG" "Setting API URL to $API_URL"
    
    # Start the frontend development server
    npm run dev >> "$LOG_FILE" 2>&1 &
    FRONTEND_PID=$!
    
    if [ $? -ne 0 ]; then
      log "ERROR" "Failed to start frontend server. Check $LOG_FILE for details."
      return 1
    fi
    
    log "INFO" "Frontend server started with PID: $FRONTEND_PID"
  else
    log "ERROR" "Frontend directory structure incorrect. Make sure the frontend code is in the correct location."
    return 1
  fi

  # Wait for frontend to be available
  wait_for_service "http://localhost:$FRONTEND_PORT" "Frontend server"
  if [ $? -ne 0 ]; then
    log "ERROR" "Frontend server failed to start properly. Check $LOG_FILE for details."
    return 1
  fi
  
  return 0
}

# Main execution logic
MAIN_RESULT=0

# Start the requested services
if [ "$START_BACKEND" = true ]; then
  start_backend
  BACKEND_RESULT=$?
  MAIN_RESULT=$((MAIN_RESULT + BACKEND_RESULT))
  
  if [ $BACKEND_RESULT -ne 0 ]; then
    log "ERROR" "Failed to start backend server. Exiting."
    exit 1
  fi
fi

if [ "$START_FRONTEND" = true ]; then
  start_frontend
  FRONTEND_RESULT=$?
  MAIN_RESULT=$((MAIN_RESULT + FRONTEND_RESULT))
  
  if [ $FRONTEND_RESULT -ne 0 ]; then
    log "ERROR" "Failed to start frontend server. Exiting."
    exit 1
  fi
fi

# All services started successfully (if any were started)
if [ "$START_BACKEND" = true ] || [ "$START_FRONTEND" = true ]; then
  # Create summary of what's running
  log "INFO" "Services started successfully!"
  echo -e "\n${GREEN}✓ Bug Tracker services summary:${NC}"
  
  if [ "$START_BACKEND" = true ]; then
    echo -e "${GREEN}✓ Backend API: ${NC}http://localhost:$BACKEND_PORT"
    echo -e "${GREEN}✓ API Documentation: ${NC}http://localhost:$BACKEND_PORT/docs"
  else
    echo -e "${YELLOW}✗ Backend: ${NC}Not started"
  fi
  
  if [ "$START_FRONTEND" = true ]; then
    echo -e "${GREEN}✓ Frontend: ${NC}http://localhost:$FRONTEND_PORT"
  else
    echo -e "${YELLOW}✗ Frontend: ${NC}Not started"
  fi
  
  echo -e "\n${BLUE}Logs:${NC} $LOG_FILE"
  echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"

  # Keep the script running until user interrupts
  if [ "$START_BACKEND" = true ] && [ "$START_FRONTEND" = true ]; then
    wait $BACKEND_PID $FRONTEND_PID
  elif [ "$START_BACKEND" = true ]; then
    wait $BACKEND_PID
  elif [ "$START_FRONTEND" = true ]; then
    wait $FRONTEND_PID
  fi
else
  # No services were started
  log "INFO" "No services were started"
  echo -e "\n${YELLOW}No services were started. Use --help to see available options.${NC}"
fi
