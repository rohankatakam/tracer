#!/usr/bin/env python3
"""
Bug Reproduction Graph Generator using Gemini API.
This module generates structured bug reproduction graphs from GitHub issues.
"""

import json
import os
import sys
import re
import traceback
from pathlib import Path
from dotenv import load_dotenv

# Import from our new structure
from .schema_converter import convert_to_gemini_schema

def generate_bug_reproduction_graph(bug_data_text: str, schema_file: str, system_instruction_file: str, 
                                   prompt_template_file: str, output_file=None, model_name="models/gemini-2.5-pro-preview-05-06"):
    """
    Generate a bug reproduction graph using the Gemini API with a structured output schema.
    
    Args:
        bug_data_text: A formatted string containing key details about the bug.
        output_file: Optional path to save the result
        model_name: Gemini model to use (default: models/gemini-1.5-flash)
    
    Returns:
        The generated bug reproduction graph as a dictionary
    """
    # Load environment variables from .env file
    env_path = Path(os.path.dirname(os.path.abspath(__file__))) / '../../../.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    
    try:
        import google.generativeai as genai
    except ImportError:
        print("Error: Google Generative AI SDK not found.")
        print("Install it with: pip install google-generativeai")
        sys.exit(1)
    
    # bug_data_text is already the formatted string. No JSON loading needed for it here.
    
    with open(system_instruction_file, 'r') as f:
        system_instruction = f.read()
    
    with open(prompt_template_file, 'r') as f:
        prompt_template = f.read()
    
    with open(schema_file, 'r') as f:
        schema = json.load(f)
    
    # Convert schema to Gemini format
    gemini_schema = convert_to_gemini_schema(schema)
    
    # Add schema guidance to system instruction
    schema_guidance = "\n\nYour response MUST follow this exact JSON schema structure:\n"
    schema_guidance += json.dumps(gemini_schema, indent=2)
    schema_guidance += "\n\nYour response should be VALID JSON that conforms to this schema, with no additional text before or after the JSON."
    
    enhanced_system_instruction = system_instruction + schema_guidance
    
    # Format the prompt with the bug details string
    formatted_prompt = prompt_template.replace('{{BUG_DETAILS_TEXT}}', bug_data_text)
    
    # Configure the Gemini API
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable is not set")
        print("Make sure it is defined in your .env file or set it using: export GEMINI_API_KEY='your-api-key'")
        sys.exit(1)
    
    genai.configure(api_key=api_key)
    
    # Initialize the model
    model = genai.GenerativeModel(model_name)
    
    # Set up generation config
    generation_config = {
        "temperature": 0.2,
        "max_output_tokens": 8192,
        "top_p": 0.95
    }
    
    # Since Gemini API currently doesn't support system role, combine both as user content
    combined_prompt = f"{enhanced_system_instruction}\n\n---\n\nGITHUB ISSUE DATA:\n{formatted_prompt}"
    
    # Create content with only user role
    content = [{"text": combined_prompt}]
    
    # Generate content
    print(f"Sending request to Gemini API using model: {model_name}...")
    
    try:
        response = model.generate_content(
            contents=content,
            generation_config=generation_config
        )
        
        print("Received response from Gemini API")
        
        # Process the response
        if hasattr(response, 'text'):
            result_text = response.text
            print(f"Response size: {len(result_text)} characters")
            
            # Extract JSON from the response
            try:
                # Try to find JSON in the response
                json_match = re.search(r'(\{.*\}|\[.*\])', result_text, re.DOTALL)
                if json_match:
                    json_text = json_match.group(0)
                    result = json.loads(json_text)
                else:
                    # Try direct parsing if no clear JSON pattern found
                    result = json.loads(result_text)
                
                # Save the result if an output file is specified
                if output_file:
                    with open(output_file, 'w') as f:
                        json.dump(result, f, indent=2)
                    print(f"Result saved to {output_file}")
                
                # Print result summary
                if 'bug_reproduction_graph' in result and 'reproduction_summary' in result:
                    nodes = result['bug_reproduction_graph'].get('nodes', [])
                    edges = result['bug_reproduction_graph'].get('edges', [])
                    print(f"Generated bug reproduction graph with {len(nodes)} nodes and {len(edges)} edges")
                    
                    takeaway = result['reproduction_summary'].get('developer_takeaway', '')
                    if takeaway:
                        print(f"Developer takeaway: {takeaway[:100]}...") # Added ellipsis for clarity
                else:
                    print("No detailed result summary found in parsed JSON.")
                
                return json.dumps(result, indent=2) # SUCCESS: Return JSON string
            except json.JSONDecodeError as e:
                print(f"Error: Failed to parse response as JSON: {e}")
                print(f"Raw response: {result_text[:500]}...")
                return json.dumps({"error": "Failed to parse JSON response from LLM", "raw_snippet": result_text[:500]+"..."}, indent=2)
        else:
            print("Error: No text attribute in Gemini response object or response.text is empty.")
            return json.dumps({"error": "No text in Gemini response or response.text is empty"}, indent=2)
    except Exception as e:
        print(f"Error calling Gemini API: {e}\n{traceback.format_exc()}")
        return json.dumps({"error": f"Error calling Gemini API: {str(e)}"}, indent=2)

def main():
    if len(sys.argv) < 5:
        print("Usage: python generator.py <github_issue_file> <schema_file> <system_instruction_file> <prompt_template_file> [output_file] [model_name]")
        sys.exit(1)
    
    github_issue_file = sys.argv[1]
    schema_file = sys.argv[2]
    system_instruction_file = sys.argv[3]
    prompt_template_file = sys.argv[4]
    output_file = sys.argv[5] if len(sys.argv) > 5 else None
    model_name = sys.argv[6] if len(sys.argv) > 6 else "models/gemini-1.5-flash"
    
    result = generate_bug_reproduction_graph(
        github_issue_file,
        schema_file,
        system_instruction_file,
        prompt_template_file,
        output_file,
        model_name
    )
    
    if "error" in result:
        print(f"Error: {result['error']}")
        sys.exit(1)
    
    print("Bug reproduction graph generated successfully!")

if __name__ == "__main__":
    main()
