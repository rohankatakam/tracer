#!/usr/bin/env python3

import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Create output directory
output_dir = Path("debug_output")
output_dir.mkdir(parents=True, exist_ok=True)

def save_element_info(driver, element, name):
    """Save information about an element for debugging"""
    with open(output_dir / f"{name}_info.txt", "w") as f:
        f.write(f"Element: {name}\n")
        f.write(f"Tag: {element.tag_name}\n")
        f.write(f"Attributes: {element.get_attribute('outerHTML')}\n")
        f.write(f"Is displayed: {element.is_displayed()}\n")
        f.write(f"Is enabled: {element.is_enabled()}\n")

def main():
    print("Starting debug session for Computer Use Demo interface")
    
    # Set up Chrome options
    options = Options()
    # Uncomment this for headless mode if needed
    # options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    # Initialize the browser
    print("Initializing browser...")
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(60)
    
    try:
        # Navigate to the Computer Use Demo
        print("Navigating to Computer Use Demo...")
        driver.get("http://localhost:8080")
        
        # Save screenshot before any interactions
        driver.save_screenshot(str(output_dir / "initial_load.png"))
        
        # Save page source for HTML inspection
        with open(output_dir / "page_source.html", "w") as f:
            f.write(driver.page_source)
            
        print("Saved initial screenshot and HTML source")
        
        # Wait for main interface to load
        print("Waiting for interface to load...")
        time.sleep(5)  # Give it some time to initialize
        
        # Take another screenshot after waiting
        driver.save_screenshot(str(output_dir / "after_wait.png"))
        
        # Try to find input field using various strategies
        print("Attempting to find input field...")
        
        # List all input elements
        print("Finding all input elements")
        inputs = driver.find_elements(By.TAG_NAME, "input")
        textareas = driver.find_elements(By.TAG_NAME, "textarea")
        
        print(f"Found {len(inputs)} input elements and {len(textareas)} textarea elements")
        
        # Save information about each input and textarea
        for i, input_elem in enumerate(inputs):
            save_element_info(driver, input_elem, f"input_{i}")
            
        for i, textarea in enumerate(textareas):
            save_element_info(driver, textarea, f"textarea_{i}")
        
        # Try to find the chat container
        print("Finding chat container")
        try:
            chat_tab = driver.find_element(By.XPATH, "//div[contains(text(), 'Chat')]")
            save_element_info(driver, chat_tab, "chat_tab")
            # Click the chat tab to ensure it's active
            chat_tab.click()
            print("Successfully clicked chat tab")
            driver.save_screenshot(str(output_dir / "after_chat_tab_click.png"))
        except Exception as e:
            print(f"Error finding chat tab: {e}")
        
        # Try to find the message input using various selectors
        selectors = [
            "//input[contains(@placeholder, 'message')]",
            "//textarea[contains(@placeholder, 'message')]",
            "//div[contains(@class, 'chat')]//input",
            "//div[contains(@class, 'chat')]//textarea",
            "//input[contains(@class, 'chat')]",
            "//textarea[contains(@class, 'chat')]",
        ]
        
        chat_input = None
        for selector in selectors:
            try:
                print(f"Trying selector: {selector}")
                chat_input = driver.find_element(By.XPATH, selector)
                save_element_info(driver, chat_input, f"chat_input_{selector.replace('/', '_')}")
                print(f"Found input with selector: {selector}")
                break
            except Exception as e:
                print(f"Selector {selector} failed: {e}")
        
        # If we found the input, try to interact with it
        if chat_input:
            try:
                chat_input.click()
                chat_input.send_keys("Hello from debug script")
                print("Successfully entered text in input field")
                driver.save_screenshot(str(output_dir / "after_input.png"))
                
                # Try to find and click send button
                send_buttons = driver.find_elements(By.XPATH, "//button[contains(@class, 'send') or contains(text(), 'Send')]")
                if send_buttons:
                    send_buttons[0].click()
                    print("Clicked send button")
                    driver.save_screenshot(str(output_dir / "after_send.png"))
                    # Wait to see if response appears
                    time.sleep(5)
                    driver.save_screenshot(str(output_dir / "after_response_wait.png"))
            except Exception as e:
                print(f"Error interacting with input: {e}")
        
        print("Debug information saved to debug_output directory")
        
    except Exception as e:
        print(f"Error during debug session: {e}")
    finally:
        # Save final screenshot
        driver.save_screenshot(str(output_dir / "final_state.png"))
        
        # Wait for user confirmation before closing
        input("Press Enter to close the browser and end the debug session...")
        
        # Close the browser
        driver.quit()

if __name__ == "__main__":
    main()
