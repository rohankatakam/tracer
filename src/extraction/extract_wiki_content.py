#!/usr/bin/env python3
"""
Script to extract content from a Wikipedia page and save it to a file.
This is used as part of the task graph execution for CUA tasks.
"""

import os
import sys
import time
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def extract_wiki_content(output_file=None):
    """Extract the first paragraph and Personal Life section from a Wikipedia page.
    
    Args:
        output_file (str, optional): Path to save the output. If None, uses default path.
    
    Returns:
        bool: True if extraction was successful, False otherwise.
    """
    # Use default path if not provided
    if output_file is None:
        output_file = os.path.join('data', 'outputs', 'wiki_content.json')
    try:
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        
        # Start a new browser
        driver = webdriver.Chrome(options=chrome_options)
        
        # Navigate to the page
        print("Opening browser and navigating to Wikipedia page...")
        driver.get("https://en.wikipedia.org/wiki/Larry_Ellison")
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "content"))
        )
        
        # Extract first paragraph
        first_paragraph = driver.find_element(By.CSS_SELECTOR, ".mw-parser-output > p:not(.mw-empty-elt)").text
        print("Extracted first paragraph")
        
        # Find the Personal Life section
        personal_life_section = None
        headings = driver.find_elements(By.CSS_SELECTOR, ".mw-headline")
        personal_life_heading = None
        
        for heading in headings:
            if "Personal life" in heading.text:
                personal_life_heading = heading
                break
        
        if personal_life_heading:
            # Get the section content - all paragraphs until the next heading
            section_id = personal_life_heading.get_attribute("id")
            section_element = personal_life_heading.find_element(By.XPATH, "./ancestor::h2")
            
            # Get all paragraphs after this heading until the next heading
            paragraphs = []
            current = section_element.find_element(By.XPATH, "./following-sibling::p")
            
            while current and current.tag_name == "p":
                paragraphs.append(current.text)
                try:
                    current = current.find_element(By.XPATH, "./following-sibling::*[1]")
                    if current.tag_name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                        break
                except:
                    break
            
            personal_life_section = "\n\n".join(paragraphs)
            print("Extracted Personal Life section")
        else:
            personal_life_section = "Personal Life section not found."
            print("Warning: Personal Life section not found")
        
        # Create output content
        output_content = {
            "extraction_time": datetime.now().isoformat(),
            "url": driver.current_url,
            "title": driver.title,
            "first_paragraph": first_paragraph,
            "personal_life_section": personal_life_section
        }
        
        # Save to file
        with open(output_file, 'w') as f:
            json.dump(output_content, f, indent=2)
        
        print(f"Content successfully saved to {output_file}")
        
        # Close the browser
        driver.quit()
        return True
        
    except Exception as e:
        print(f"Error extracting wiki content: {e}")
        # Make sure browser is closed even if there's an error
        try:
            driver.quit()
        except:
            pass
        return False

if __name__ == "__main__":
    # Default output file
    output_file = "wiki_content.json"
    
    # If output file is specified as argument
    if len(sys.argv) > 1:
        output_file = sys.argv[1]
    
    # Make sure the directory exists
    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
    
    # Extract content
    success = extract_wiki_content(output_file)
    sys.exit(0 if success else 1)
