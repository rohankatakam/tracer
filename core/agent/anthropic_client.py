#!/usr/bin/env python3
"""
Anthropic API client for Computer Use Agent interactions.

This module provides a client for interacting with the Anthropic API
with proper configuration for Computer Use Agent features.
"""

import os
import json
import time
import logging
import anthropic
import random
from typing import Dict, List, Any, Optional, Union

class AnthropicClient:
    """Client for interacting with the Anthropic API with Computer Use Agent support."""
    
    def __init__(self, api_key=None, model="claude-3-7-sonnet-20250219", 
                 max_tokens=4096, thinking_budget=1024, log_level=logging.INFO):
        """Initialize the Anthropic API client with Computer Use Agent support.
        
        Args:
            api_key: Anthropic API key. If None, will load from environment.
            model: Anthropic model to use.
            max_tokens: Maximum tokens to generate in response.
            thinking_budget: Token budget for thinking steps (for 3.7 models).
            log_level: Logging level.
        """
        self.logger = logging.getLogger("anthropic_client")
        self.logger.setLevel(log_level)
        
        # Set up API key
        if not api_key:
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                raise ValueError("No API key provided or found in environment.")
        
        # Set up Anthropic client and parameters
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.thinking_budget = thinking_budget
        
        # Determine the appropriate tool versions and features based on model
        self.thinking_enabled = False
        
        # Map models to appropriate tool versions
        if "3-7" in model:
            # Claude 3.7 models (newest)
            self.beta_flag = "computer-use-2025-01-24"
            self.computer_tool_type = "computer_20250124"
            self.bash_tool_type = "bash_20250124"
            self.text_editor_tool_type = "text_editor_20250124"
            self.thinking_enabled = True
        elif "claude-3-sonnet-20240229" in model or "claude-3-opus-20240229" in model:
            # Claude 3 Sonnet/Opus from Feb 2024
            self.beta_flag = "computer-use-2024-10-22"
            self.computer_tool_type = "computer_20241022"
            self.bash_tool_type = "bash_20241022"
            self.text_editor_tool_type = "text_editor_20241022"
        elif "claude-3-haiku" in model:
            # Claude 3 Haiku
            self.beta_flag = "computer-use-2024-10-22"
            self.computer_tool_type = "computer_20241022"
            self.bash_tool_type = "bash_20241022"
            self.text_editor_tool_type = "text_editor_20241022"
        else:
            # Default to older versions for any other model
            self.beta_flag = "computer-use-2024-10-22"
            self.computer_tool_type = "computer_20241022"
            self.bash_tool_type = "bash_20241022"
            self.text_editor_tool_type = "text_editor_20241022"
            
        self.logger.info(f"Anthropic client initialized with model {model} and beta flag {self.beta_flag}")
    
    def get_available_tools(self, display_width=1280, display_height=800, display_number=None):
        """Get the available tools for the current model.
        
        Args:
            display_width: Width of the display in pixels.
            display_height: Height of the display in pixels.
            display_number: X11 display number (if applicable).
            
        Returns:
            List of tool definitions.
        """
        # Create the computer tool definition
        computer_tool = {
            "type": self.computer_tool_type,
            "name": "computer",
            "display_width_px": display_width,
            "display_height_px": display_height
        }
        
        # Add display number if specified
        if display_number is not None:
            computer_tool["display_number"] = display_number
        
        # Create other tool definitions
        bash_tool = {
            "type": self.bash_tool_type,
            "name": "bash"
        }
        
        text_editor_tool = {
            "type": self.text_editor_tool_type,
            "name": "str_replace_editor"
        }
        
        # Return all tool definitions
        # NOTE: Currently returning only bash_tool since computer_tool is not available
        # for the user's API access. Uncomment the computer_tool when available.
        return [
            # computer_tool,  # Uncomment when computer_tool is available 
            bash_tool,
            # text_editor_tool  # Uncomment if needed
        ]
    
    def send_message(self, messages, system_prompt=None):
        """Send a message to the Anthropic API.
        
        Args:
            messages: List of message objects to send.
            system_prompt: Optional system prompt to include.
            
        Returns:
            The API response.
        """
        # Configure request parameters
        request_params = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": messages,
            "tools": self.get_available_tools(),
            "betas": [self.beta_flag]
        }
        
        # Add system prompt if provided
        if system_prompt:
            request_params["system"] = system_prompt
            
        # Add thinking if supported by the model
        if self.thinking_enabled and self.thinking_budget:
            request_params["thinking"] = {
                "type": "enabled",
                "budget_tokens": self.thinking_budget
            }
        
        # Send the request
        self.logger.info(f"Sending message to {self.model} with {len(messages)} messages")
        try:
            response = self.client.messages.create(**request_params)
            return response
        except Exception as e:
            self.logger.error(f"Error sending message to Anthropic API: {e}")
            raise
    
    def agent_loop(self, initial_prompt, system_prompt=None, max_iterations=10, tool_executor=None, tools=None, verbose=False, request_delay=3.0):
        """Run the agent loop with the Anthropic API.
        
        Args:
            initial_prompt: The initial prompt to send to the API.
            system_prompt: Optional system prompt to include.
            max_iterations: Maximum number of iterations to run.
            tool_executor: Function to execute tools.
            tools: List of tools to make available to the model. If None, uses default tools.
            verbose: Whether to print verbose logs.
            request_delay: Delay in seconds between API requests to avoid rate limiting.
            
        Returns:
            The final conversation and response.
        """
        if tool_executor is None:
            raise ValueError("Tool executor is required for agent loop.")
        
        # Initialize the conversation
        messages = [{"role": "user", "content": initial_prompt}]
        
        # Get tools to use
        if tools is None:
            tools = self.get_available_tools()
        
        # Track iterations and tool use
        total_tools_used = 0
        tool_success_count = 0
        tool_error_count = 0
        
        # Run the agent loop
        for i in range(max_iterations):
            self.logger.info(f"Agent loop iteration {i+1}/{max_iterations}")
            
            # Send the message with tools
            try:
                request_params = {
                    "messages": messages,
                    "tools": tools,
                    "model": self.model,
                    "max_tokens": self.max_tokens
                }
                
                # Add system prompt if provided
                if system_prompt:
                    request_params["system"] = system_prompt
                    
                # Add thinking if supported by the model
                if self.thinking_enabled and self.thinking_budget:
                    request_params["thinking"] = {
                        "type": "enabled",
                        "budget_tokens": self.thinking_budget
                    }
                
                # Set beta flag for computer use - commented out as newer SDK doesn't use this
                # The Computer Use capability is now built into the base API
                # if hasattr(self.client, 'beta') and self.beta_flag:
                #     request_params["beta"] = self.beta_flag
                
                # Add a small random delay to avoid rate limiting
                delay = request_delay + random.uniform(0.1, 0.5)
                if verbose:
                    self.logger.info(f"Waiting {delay:.2f} seconds before sending API request to avoid rate limits...")
                time.sleep(delay)
                
                # Send the request
                if verbose:
                    self.logger.info(f"Sending message to {self.model} with {len(messages)} messages")
                
                # Try the request with retry logic for rate limiting
                max_retries = 5  # Increased from 3 to 5
                retry_count = 0
                
                while retry_count < max_retries:
                    try:
                        response = self.client.messages.create(**request_params)
                        # Successfully got a response - wait a moment before continuing to avoid rapid requests
                        if i > 0:  # Not the first request
                            cool_down = 1.0 + random.uniform(0, 0.5)
                            if verbose:
                                self.logger.info(f"Request successful, cooling down for {cool_down:.2f} seconds")
                            time.sleep(cool_down)
                        break
                    except Exception as e:
                        error_str = str(e).lower()
                        if "429" in error_str or "too many requests" in error_str or "rate limit" in error_str:
                            retry_count += 1
                            if retry_count >= max_retries:
                                self.logger.error(f"Exhausted all {max_retries} retries due to rate limiting")
                                raise  # Re-raise if we've exhausted retries
                            
                            # Exponential backoff with jitter
                            # Start with longer backoff and add randomness
                            base_backoff = 5.0 * (2 ** retry_count)  # 10, 20, 40, 80, 160 seconds
                            jitter = random.uniform(0, base_backoff * 0.2)  # Add up to 20% random jitter
                            backoff_time = base_backoff + jitter
                            
                            self.logger.warning(f"Rate limited by API, backing off for {backoff_time:.2f} seconds (retry {retry_count}/{max_retries})")
                            time.sleep(backoff_time)
                        else:
                            # If it's another type of error, log it and re-raise
                            self.logger.error(f"API error (not rate limiting): {e}")
                            raise
            except Exception as e:
                self.logger.error(f"Error in agent loop iteration {i+1}: {e}")
                break
            
            # Extract content from response
            response_content = response.content
            
            # Check for thinking output
            thinking_content = None
            if hasattr(response, 'thinking') and response.thinking:
                thinking_content = response.thinking
                if verbose:
                    self.logger.info(f"Thinking content: {thinking_content}")
            
            # Add the response to the conversation
            messages.append({"role": "assistant", "content": response_content})
            
            # Check if any tools were used
            tool_uses = []
            for block in response_content:
                if hasattr(block, 'type') and block.type == "tool_use":
                    tool_uses.append({
                        "id": block.id,
                        "name": block.name,
                        "input": block.input
                    })
            
            # Update tool use count
            total_tools_used += len(tool_uses)
            
            # If no tools were used, we're done
            if not tool_uses:
                self.logger.info("No tools used, agent loop complete.")
                break
            
            # Execute the tools
            tool_results = []
            for tool_use in tool_uses:
                tool_name = tool_use.get('name', 'unknown_tool')
                self.logger.info(f"Executing tool {tool_name}")
                
                try:
                    # Execute the tool
                    result = tool_executor(tool_use)
                    
                    # Format the result for the API
                    # Ensure tool_result.content is a string or list of content blocks
                    if isinstance(result, dict):
                        # Convert dict to string for API compatibility
                        result_str = json.dumps(result)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_use["id"],
                            "content": result_str
                        })
                    elif isinstance(result, str):
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_use["id"],
                            "content": result
                        })
                    else:
                        # For any other type, convert to string
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_use["id"],
                            "content": str(result)
                        })
                    
                    # Check for errors in the result
                    if isinstance(result, dict) and 'error' in result:
                        self.logger.warning(f"Tool {tool_name} returned error: {result['error']}")
                        tool_error_count += 1
                    else:
                        self.logger.info(f"Tool {tool_name} executed successfully")
                        tool_success_count += 1
                        
                        # Log screenshot content if present
                        if isinstance(result, dict) and 'screenshot' in result:
                            self.logger.info(f"Tool {tool_name} returned screenshot")
                            
                except Exception as e:
                    self.logger.error(f"Error executing tool {tool_name}: {e}")
                    tool_error_count += 1
                    # Format error as a string to comply with API requirements
                    error_message = json.dumps({"error": str(e)})
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use["id"],
                        "content": error_message
                    })
            
            # Add the tool results to the conversation
            if tool_results:
                messages.append({"role": "user", "content": tool_results})
        
        # Prepare final response with metrics
        final_response = None
        if messages and messages[-1]["role"] == "assistant":
            final_response = messages[-1]
        
        return {
            "messages": messages,
            "final_response": final_response,
            "iterations": i + 1,
            "max_iterations": max_iterations,
            "tools_used": total_tools_used,
            "tool_success_count": tool_success_count,
            "tool_error_count": tool_error_count,
            "success": total_tools_used > 0 and tool_error_count < total_tools_used,
            "thinking": thinking_content
        }
