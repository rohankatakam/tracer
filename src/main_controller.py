"""
Minimal Anthropic Computer Use API Demo

This script demonstrates a basic usage of the Anthropic API to execute
a single hardcoded CUA tool call to navigate to a URL like example.com.
"""

import os
import anthropic
from dotenv import load_dotenv

def main():
    """Main function that demonstrates a simple Anthropic API call with tools."""
    print("Initializing Anthropic API demo...")
    
    # Load API key from environment variables
    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        raise ValueError(
            "Anthropic API key not found. Please set the ANTHROPIC_API_KEY environment variable "
            "in a .env file or in your system environment."
        )
    
    # Create the Anthropic client
    client = anthropic.Anthropic(api_key=api_key)
    
    # Target URL
    target_url = "https://example.com"
    
    try:
        # Make a simple API call with the bash tool enabled
        print(f"\nAsking Claude to open a web browser and navigate to {target_url}...")
        
        response = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=2048,
            tools=[{
                "type": "bash_20250124",
                "name": "bash"
            }],
            messages=[{
                "role": "user",
                "content": f"What bash command would I use to open {target_url} in a web browser on macOS?"
            }],
            thinking={"type": "enabled", "budget_tokens": 1024}
        )
        
        # Process and display the response
        print("\nResponse from Claude:")
        print(f"Stop reason: {response.stop_reason}")
        
        # Print each content block
        for i, content in enumerate(response.content):
            print(f"\nContent {i+1} ({content.type}):")
            
            if content.type == "text":
                print(content.text)
            elif content.type == "tool_use":
                print(f"Tool: {content.name}")
                print(f"Input: {content.input}")
                
                # In a real implementation, you would execute the bash command here
                # and then return the result to Claude for further processing
                if content.name == "bash":
                    command = content.input.get("command", "")
                    print(f"\nCommand that would be executed: {command}")
                    print("\nIn a full implementation, this command would be executed to open the browser.")
            
        print("\nDemo completed successfully!")
        
    except Exception as e:
        print(f"Error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
