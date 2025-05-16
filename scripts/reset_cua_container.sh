#!/bin/bash

# Anthropic CUA Container Manager
# Commands: start, restart, reset, stop

# Set variables
CONTAINER_NAME="anthropic-computer-use"
DOCKER_IMAGE="ghcr.io/anthropics/anthropic-quickstarts:computer-use-demo-latest"

# Display usage info
show_usage() {
  echo "Usage: $0 [start|restart|reset|stop]"
  echo "  start   - Start if doesn't exist"
  echo "  restart - Restart existing container"
  echo "  reset   - Remove and start new (default)"
  echo "  stop    - Stop and remove container"
}

# Check if container exists
container_exists() {
  [ "$(docker ps -a -q -f name=$CONTAINER_NAME)" ] && return 0 || return 1
}

# Check if container is running
container_running() {
  [ "$(docker ps -q -f name=$CONTAINER_NAME)" ] && return 0 || return 1
}

# Load API key
load_api_key() {
  if [ ! -f .env ]; then
    echo "❌ Error: .env file not found with ANTHROPIC_API_KEY."
    exit 1
  fi
  export $(grep -v '^#' .env | xargs)
  if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ Error: ANTHROPIC_API_KEY not found in .env file."
    exit 1
  fi
  echo "🔑 API key loaded successfully."
}

# Show access information
show_access_info() {
  echo ""
  echo "📋 Anthropic Computer Use Agent Information:"
  echo "------------------------------------------"
  echo "🌐 Chat Interface:    http://localhost:8501"
  echo "💻 Desktop View:      http://localhost:6080"
  echo "🔧 VNC Access:        localhost:5900"
  echo "------------------------------------------"
  echo ""
}

# Start container
start_container() {
  echo "🚀 Starting new Docker container with API key..."
  docker run -d -p 5900:5900 -p 6080:6080 -p 8080:8080 -p 8501:8501 \
    -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
    --name $CONTAINER_NAME \
    $DOCKER_IMAGE > /dev/null
  echo "✅ Container started successfully!"
  show_access_info
}

# Command handlers
cmd_start() {
  echo "=== Starting Anthropic Computer Use Agent ==="
  
  if container_running; then
    echo "ℹ️ Container is already running."
    show_access_info
    return
  fi
  
  if container_exists; then
    echo "🔄 Container exists but is not running. Starting it..."
    docker start $CONTAINER_NAME > /dev/null
    echo "✅ Container started successfully!"
    show_access_info
    return
  fi
  
  load_api_key
  start_container
}

cmd_restart() {
  echo "=== Restarting Anthropic Computer Use Agent ==="
  
  if ! container_exists; then
    echo "ℹ️ Container doesn't exist. Creating a new one..."
    load_api_key
    start_container
    return
  fi
  
  echo "🔄 Restarting container..."
  docker restart $CONTAINER_NAME > /dev/null
  echo "✅ Container restarted successfully!"
  show_access_info
}

cmd_reset() {
  echo "=== Resetting Anthropic Computer Use Agent ==="
  
  if container_exists; then
    echo "🗑️ Stopping and removing existing container..."
    docker stop $CONTAINER_NAME > /dev/null
    docker rm $CONTAINER_NAME > /dev/null
  fi
  
  load_api_key
  start_container
}

cmd_stop() {
  echo "=== Stopping Anthropic Computer Use Agent ==="
  
  if ! container_exists; then
    echo "ℹ️ No container found. Nothing to stop."
    return
  fi
  
  echo "🛑 Stopping and removing container..."
  docker stop $CONTAINER_NAME > /dev/null
  docker rm $CONTAINER_NAME > /dev/null
  echo "✅ Container stopped and removed successfully!"
}

# Main script logic
COMMAND=${1:-reset}  # Default to reset if no command provided

case "$COMMAND" in
  start)
    cmd_start
    ;;
  restart)
    cmd_restart
    ;;
  reset)
    cmd_reset
    ;;
  stop)
    cmd_stop
    ;;
  *)
    echo "❌ Error: Unknown command '$COMMAND'"
    show_usage
    exit 1
    ;;
esac
