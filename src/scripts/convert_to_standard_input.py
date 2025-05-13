import os
import json
import logging
import argparse
import re
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Assuming these utils exist and work
from src.utils.logging_utils import setup_logging 
from src.utils.json_utils import save_json

logger = setup_logging("input_converter", "logs/input_converter", logging.INFO)

def get_default_schema() -> Dict[str, Any]:
    """Returns a dictionary representing the default structure based on test_bug_data.json."""
    return {
        "bug_metadata": {
            "bug_id": "Unknown",
            "bug_title": "Unknown",
            "test_environment_url": "http://localhost:3000",
            "severity": {"level": 0, "description": "Unknown"},
            "status": {"code": "0", "description": "New"},
            "customer": {"name": "N/A", "environment": "Web"},
            "product": {
                "id": "N/A",
                "name": "Unknown",
                "version": {"reported": "Unknown", "component_ver": "", "fixed_ver": ""}
            },
            "component": {"name": "Unknown", "type": "", "subcomponent": ""},
            "dates": {"created": "", "updated": "", "fix_eta": ""},
            "reporter": "N/A",
            "assignee": "N/A"
        },
        "bug_content": {
            "description": "",
            "steps_to_reproduce": "",
            "expected_outcome": "",
            "additional_info": "",
            "reproducible": {"by_customer": True, "by_support": False, "environment": "Web"}
        },
        "attachments": [],
        "comments": [],
        "history": []
    }

def convert_juice_shop_challenge(challenge: Dict[str, Any]) -> Dict[str, Any]:
    """Converts a Juice Shop challenge dict to the standard bug data package schema."""
    standard_data = get_default_schema()
    challenge_id_safe = challenge.get('id', 'unknown').replace(' ', '_').lower()
    now_iso = datetime.now().isoformat()
    challenge_title = challenge.get('title', 'Unknown Juice Shop Challenge')

    # Map metadata
    standard_data["bug_metadata"]["bug_id"] = f"juiceshop_{challenge_id_safe}"
    standard_data["bug_metadata"]["bug_title"] = challenge_title
    standard_data["bug_metadata"]["test_environment_url"] = challenge.get('target_url', 'http://localhost:3000')
    
    try:
        difficulty_str = challenge.get('difficulty', '0')
        level = int(re.search(r'\d+', difficulty_str).group()) if re.search(r'\d+', difficulty_str) else 0
    except:
        level = 0 
    standard_data["bug_metadata"]["severity"] = {
        "level": level,
        "description": challenge.get('difficulty', 'Unknown')
    }
    standard_data["bug_metadata"]["product"]["name"] = "OWASP Juice Shop"
    standard_data["bug_metadata"]["component"]["name"] = challenge.get('category', 'Unknown')
    standard_data["bug_metadata"]["dates"]["created"] = now_iso
    standard_data["bug_metadata"]["dates"]["updated"] = now_iso
    
    # Map content
    standard_data["bug_content"]["description"] = challenge.get('description', '')
    # Use the 'goal' (which should now be more detailed) as the basis for steps to reproduce
    standard_data["bug_content"]["steps_to_reproduce"] = challenge.get('goal', 'No detailed steps provided. Infer from description.') 
    standard_data["bug_content"]["expected_outcome"] = f"Challenge '{challenge_title}' is solved successfully."
    standard_data["bug_content"]["additional_info"] = f"Source: OWASP Juice Shop Challenge - {challenge_title}. Category: {challenge.get('category', 'Unknown')}. Difficulty: {challenge.get('difficulty', 'Unknown')}."

    return standard_data

def convert_generic_test_case(test_case: Dict[str, Any]) -> Dict[str, Any]:
    """Converts a generic test case dict to the standard bug data package schema."""
    standard_data = get_default_schema()
    case_id_safe = test_case.get('id', 'unknown_case').replace(' ', '_').lower()
    now_iso = datetime.now().isoformat()
    case_title = test_case.get('title', 'Unknown Test Case')

    standard_data["bug_metadata"]["bug_id"] = case_id_safe
    standard_data["bug_metadata"]["bug_title"] = case_title
    standard_data["bug_metadata"]["test_environment_url"] = test_case.get('target_url', 'Not specified')
    standard_data["bug_metadata"]["severity"] = {"level": test_case.get('severity_level', 0), "description": test_case.get('severity_desc', "Test Case")}
    standard_data["bug_metadata"]["product"]["name"] = test_case.get('application_name', 'Unknown Application')
    standard_data["bug_metadata"]["component"]["name"] = test_case.get('feature_tested', case_title)
    standard_data["bug_metadata"]["dates"]["created"] = now_iso
    standard_data["bug_metadata"]["dates"]["updated"] = now_iso
    standard_data["bug_metadata"]["reporter"] = test_case.get('reporter', "Test Case Definition")
    
    standard_data["bug_content"]["description"] = test_case.get('description', '')
    steps_list = test_case.get('detailed_steps', [])
    standard_data["bug_content"]["steps_to_reproduce"] = "\n".join(steps_list) if steps_list else 'No steps provided.'
    # For a bug, expected_outcome is the non-buggy state. For a test case verifying a bug, it's the buggy state.
    standard_data["bug_content"]["expected_outcome"] = test_case.get('expected_bug_behavior', f"Bug '{case_title}' is observed as described.") 
    standard_data["bug_content"]["additional_info"] = f"Source: {test_case.get('application_name', 'Test Case')} - {case_title}. Original Description: {test_case.get('source_bug_description', '')}"
    standard_data["bug_content"]["reproducible"]["environment"] = "Web (Automated Test)"

    return standard_data

def main():
    parser = argparse.ArgumentParser(description="Convert various bug formats to a standard input JSON format.")
    parser.add_argument("--source_file", type=str, required=True, 
                        help="Path to the source JSON file (e.g., juice_shop_challenges.json, academybugs_test_cases.json).")
    parser.add_argument("--source_format", type=str, required=True, choices=['juice_shop', 'academybugs'],
                        help="The format of the source file.")
    parser.add_argument("--output_dir", type=str, default="data/standardized_inputs",
                        help="Directory to save the converted standardized JSON files.")
    args = parser.parse_args()

    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Load source data
    try:
        with open(args.source_file, 'r') as f:
            source_data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load or parse source file {args.source_file}: {e}")
        return

    # Process based on format
    if args.source_format == 'juice_shop':
        if not isinstance(source_data, list):
            logger.error("Juice Shop source file must contain a JSON list.")
            return
        
        logger.info(f"Converting {len(source_data)} Juice Shop challenges...")
        for challenge in source_data:
            if not isinstance(challenge, dict) or not challenge.get('id'):
                logger.warning(f"Skipping invalid challenge data: {challenge}")
                continue
            
            try:
                converted_data = convert_juice_shop_challenge(challenge)
                output_filename = output_path / f"juiceshop_{challenge.get('id', 'unknown').replace(' ', '_').lower()}_standard.json"
                save_json(converted_data, str(output_filename), pretty=True)
                logger.info(f"Saved standardized input to: {output_filename}")
            except Exception as e:
                 logger.error(f"Failed to convert challenge {challenge.get('id', 'unknown')}: {e}")
    elif args.source_format == 'academybugs':
        if not isinstance(source_data, list):
            logger.error("AcademyBugs source file must contain a JSON list.")
            return
        logger.info(f"Converting {len(source_data)} AcademyBugs test cases...")
        for item in source_data:
            if not isinstance(item, dict) or not item.get('id'):
                logger.warning(f"Skipping invalid AcademyBugs data: {item}")
                continue
            try:
                converted_data = convert_generic_test_case(item)
                output_filename = output_path / f"{item.get('id', 'unknown_case').replace(' ', '_').lower()}_standard.json"
                save_json(converted_data, str(output_filename), pretty=True)
                logger.info(f"Saved standardized input to: {output_filename}")
            except Exception as e:
                 logger.error(f"Failed to convert AcademyBugs case {item.get('id', 'unknown')}: {e}")
    else:
        logger.error(f"Unsupported source format: {args.source_format}")

if __name__ == "__main__":
    main() 