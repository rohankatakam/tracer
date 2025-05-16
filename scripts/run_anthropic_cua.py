#!/usr/bin/env python3
"""
Direct Anthropic Computer Use Agent Example

This script provides a simple example of using Anthropic's Computer Use Agent directly,
without any custom integration layer. This allows you to leverage the full power of
Claude's computer use capabilities out of the box.
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

import anthropic
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("anthropic_cua")

def run_computer_use_agent(
    prompt: str,
    system_prompt: Optional[str] = None,
    model: str = "claude-3-7-sonnet-20250219",
    max_tokens: int = 4096,
    display_width: int = 1280,
    display_height: int = 800
) -> Dict[str, Any]:
    """
    Run Anthropic's Computer Use Agent with the given prompt.
    
    Args:
        prompt: The prompt to send to the agent
        system_prompt: Optional system prompt to use
        model: Anthropic model to use (must support computer use)
        max_tokens: Maximum tokens to generate
        display_width: Width of the display in pixels
        display_height: Height of the display in pixels
    
    Returns:
        The API response
    """
    # Load environment variables from .env file
    load_dotenv()
    
    # Get API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")
    
    # Initialize the client
    client = anthropic.Anthropic(api_key=api_key)
    
    # Default system prompt if none provided
    if not system_prompt:
        system_prompt = """You are a helpful Computer Use Agent that can use web browsers and desktop applications. 
You have access to a computer and can perform tasks as requested by the user.
When using a browser, navigate carefully and always check your work at each step.
Take screenshots frequently to document your progress."""
    
    # Prepare the tools definition
    tools = [{
        "name": "computer",
        "type": "computer_20250124",
        "display_width_px": display_width,
        "display_height_px": display_height
    }]
    
    logger.info(f"Running Anthropic Computer Use Agent with model: {model}")
    logger.info(f"Display dimensions: {display_width}x{display_height}")
    
    # Send the message
    try:
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}],
            tools=tools
        )
        
        logger.info("Successfully received response from Anthropic API")
        return {
            "success": True,
            "response": response,
            "content": response.content,
            "model": model
        }
    
    except Exception as e:
        logger.error(f"Error calling Anthropic API: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def main():
    """Main function to parse arguments and run the agent."""
    parser = argparse.ArgumentParser(description='Run Anthropic Computer Use Agent')
    parser.add_argument('--prompt', '-p', type=str, required=True, 
                        help='Prompt to send to the agent')
    parser.add_argument('--system-prompt', '-s', type=str, 
                        help='System prompt to use')
    parser.add_argument('--model', '-m', type=str, default="claude-3-7-sonnet-20250219",
                        help='Anthropic model to use')
    parser.add_argument('--max-tokens', '-t', type=int, default=4096,
                        help='Maximum tokens to generate')
    parser.add_argument('--display-width', '-w', type=int, default=1280,
                        help='Width of the display in pixels')
    parser.add_argument('--display-height', '-dh', type=int, default=800,
                        help='Height of the display in pixels')
    parser.add_argument('--output', '-o', type=str, 
                        help='Output file to save the response to')
    
    args = parser.parse_args()
    
    # Run the agent
    result = run_computer_use_agent(
        prompt=args.prompt,
        system_prompt=args.system_prompt,
        model=args.model,
        max_tokens=args.max_tokens,
        display_width=args.display_width,
        display_height=args.display_height
    )
    
    # Output the result
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"Response saved to {output_path}")
    else:
        if result["success"]:
            print("\nResponse content:")
            
            if hasattr(result["response"], "content"):
                for content_block in result["response"].content:
                    if content_block.type == "text":
                        print(content_block.text)
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
    
    return 0 if result["success"] else 1

if __name__ == "__main__":
    sys.exit(main())
