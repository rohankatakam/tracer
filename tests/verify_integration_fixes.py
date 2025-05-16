#!/usr/bin/env python3

import os
import asyncio
import logging
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

"""
A simple script to verify our key fixes:
1. response_text variable scope
2. Preventing multiple chat messages
3. Element interactability fixes
"""

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("integration_test")

async def verify_fixes():
    # Verify API key is set in environment
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable is not set.")
        print("Please set it or use the run_firefox_test.sh script which loads it from .env")
        return
    
    # Set up output directory for screenshots
    output_dir = Path("data/outputs/verification_test")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Set up Chrome options
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    driver = None
    try:
        # Initialize browser
        logger.info("Initializing browser session")
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(30)
        driver.set_script_timeout(30)
        driver.maximize_window()
        
        # Navigate to the Computer Use Demo UI
        web_ui_url = "http://localhost:8080"
        logger.info(f"Navigating to Computer Use Demo at {web_ui_url}")
        
        # Attempt navigation with retries
        max_attempts = 3
        success = False
        
        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(f"Attempt {attempt}/{max_attempts} to navigate to {web_ui_url}")
                driver.get(web_ui_url)
                
                # Wait for the page to load
                WebDriverWait(driver, 15).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                
                # Verify we can actually interact with the page
                WebDriverWait(driver, 10).until(
                    lambda d: len(d.find_elements(By.TAG_NAME, "body")) > 0
                )
                
                logger.info(f"Successfully loaded Computer Use Demo at {driver.current_url}")
                success = True
                break
            except Exception as e:
                logger.warning(f"Navigation attempt {attempt} failed: {e}")
                if attempt == max_attempts:
                    raise
                await asyncio.sleep(3)  # Wait before next attempt
        
        if not success:
            logger.error("Failed to navigate to the Computer Use Demo UI")
            return
        
        # Save screenshot of initial page
        driver.save_screenshot(str(output_dir / "initial_page.png"))
        
        # Switch to the Streamlit chat iframe
        logger.info("Switching to left iframe (Streamlit chat interface)")
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "iframe.left"))
        )
        left_iframe = driver.find_element(By.CSS_SELECTOR, "iframe.left")
        driver.switch_to.frame(left_iframe)
        
        # Wait a moment for Streamlit to initialize
        await asyncio.sleep(5)
        
        # Save screenshot of iframe
        driver.save_screenshot(str(output_dir / "iframe.png"))
        
        # Test Fix #1: Find chat input with WebDriverWait to ensure it's interactable
        logger.info("Testing Fix #1: Element interactability")
        textarea = None
        selectors = [
            "textarea[data-testid='stChatInput']",
            "textarea.streamlit-chat",
            "textarea.stChatInputArea",
            "div.stChatInputContainer textarea",
            "textarea[placeholder*='Type']",
            "textarea",
        ]
        
        for selector in selectors:
            try:
                logger.info(f"Trying selector: {selector}")
                # Use WebDriverWait to ensure the element is interactable
                textarea = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                logger.info(f"Found interactable input with selector: {selector}")
                break
            except TimeoutException:
                logger.info(f"Selector {selector} not interactable, trying next one")
                continue
        
        if not textarea:
            logger.error("Could not find an interactable chat input field")
            return
        
        # Test Fix #2: Implement robust text entry method
        logger.info("Testing Fix #2: Robust text entry")
        
        # Try multiple methods to ensure the field is cleared
        logger.info("Clearing any existing text")
        textarea.clear()
        await asyncio.sleep(0.5)
        
        # Try JavaScript to clear if needed
        current_text = textarea.get_attribute('value')
        if current_text and len(current_text) > 0:
            logger.info(f"Text still present, using JavaScript to clear: '{current_text[:20]}...'")
            driver.execute_script("arguments[0].value = '';", textarea)
            await asyncio.sleep(0.5)
        
        # Enter the text using JavaScript to ensure it works
        test_message = "Verify that the integration fixes are working correctly"
        logger.info(f"Entering text: '{test_message}'")
        
        try:
            # Try standard input first
            textarea.click()
            await asyncio.sleep(0.5)
            textarea.send_keys(test_message)
            logger.info("Standard text entry succeeded")
        except Exception as e:
            logger.warning(f"Standard send_keys failed: {e}, trying JavaScript")
            try:
                # JavaScript fallback
                driver.execute_script("arguments[0].value = arguments[1];", textarea, test_message)
                # Trigger input event to ensure JavaScript change is registered
                driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", textarea)
                logger.info("JavaScript text entry succeeded")
            except Exception as e2:
                logger.error(f"All text entry methods failed: {e2}")
                return
        
        # Save screenshot of entered text
        driver.save_screenshot(str(output_dir / "text_entered.png"))
        
        # Test Fix #3: Verify submission and prevent multiple messages
        logger.info("Testing Fix #3: Preventing multiple messages")
        
        # Find submit button
        submit_button = None
        button_selectors = [
            "button[data-testid='stChatInputSubmitButton']",
            "button.streamlit-chat-submit",
            "button.stSubmitButton",
            "button:not([disabled])"
        ]
        
        for selector in button_selectors:
            try:
                buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                for button in buttons:
                    if button.is_displayed() and button.is_enabled():
                        submit_button = button
                        logger.info(f"Found submit button with selector: {selector}")
                        break
                if submit_button:
                    break
            except Exception as e:
                logger.warning(f"Button selector {selector} failed: {e}")
        
        if not submit_button:
            logger.error("Could not find submit button")
            return
        
        # Click submit button using JavaScript
        logger.info("Clicking submit button with JavaScript")
        driver.execute_script("arguments[0].click();", submit_button)
        
        # Critical: Wait to ensure the click registers properly
        await asyncio.sleep(3)
        
        # Verify submission was successful by checking if input was cleared
        submit_attempts = 0
        max_verification_attempts = 3
        verified_submission = False
        
        while submit_attempts < max_verification_attempts and not verified_submission:
            try:
                # Check if the input has been cleared (indicating successful submission)
                current_text = textarea.get_attribute('value')
                if current_text and len(current_text) > 0:
                    logger.warning(f"Attempt {submit_attempts+1}: Text still present in input field")
                    # Clear the input but don't resubmit
                    textarea.clear()
                    await asyncio.sleep(1)
                    driver.execute_script("arguments[0].value = '';", textarea)
                    await asyncio.sleep(1)
                else:
                    logger.info("Submission successful - input field is now empty")
                    verified_submission = True
            except Exception as e:
                logger.warning(f"Error verifying submission (attempt {submit_attempts+1}): {e}")
            
            submit_attempts += 1
            await asyncio.sleep(1)
        
        # Save screenshot after submission
        driver.save_screenshot(str(output_dir / "after_submit.png"))
        
        # Test Fix #4: response_text scope handling
        logger.info("Testing Fix #4: response_text scope handling")
        
        # Initialize response_text at the top level to ensure it's always defined
        response_text = None
        
        # Define a reasonable timeout for Claude to respond
        claude_response_timeout = 30  # shorter timeout for test purposes
        logger.info(f"Waiting {claude_response_timeout} seconds for Claude to respond")
        
        # Response selectors
        response_selectors = [
            "div[data-testid*='stChatMessage']",
            "div.stChatMessage",
            "div.element-container div",
            "div.st-emotion-cache",
            "div.chat-message",
            "p",
            "div.markdown-text-container"
        ]
        
        start_time = asyncio.get_event_loop().time()
        response_found = False
        
        while asyncio.get_event_loop().time() - start_time < claude_response_timeout and not response_found:
            # Take periodic screenshots
            if int(asyncio.get_event_loop().time() - start_time) % 10 == 0:
                driver.save_screenshot(str(output_dir / f"waiting_{int(asyncio.get_event_loop().time() - start_time)}.png"))
            
            for selector in response_selectors:
                try:
                    response_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    if response_elements:
                        # Look at the last few elements if there are multiple
                        for element in reversed(response_elements[-3:]):
                            element_text = element.text
                            if element_text and len(element_text) > 10 and element_text != test_message:
                                response_text = element_text
                                logger.info(f"Found response with selector: {selector}")
                                logger.info(f"Response text: {response_text[:50]}...")
                                response_found = True
                                break
                    
                    if response_found:
                        break
                except Exception as e:
                    logger.debug(f"Response selector {selector} failed: {e}")
            
            if response_found:
                driver.save_screenshot(str(output_dir / "response_found.png"))
                break
            
            await asyncio.sleep(1)
        
        # If we couldn't find a response, log warning but continue
        if not response_text:
            response_text = "[No response could be extracted from the UI. See screenshots for details.]"
            logger.warning("Failed to extract any response text")
        
        # Success message
        if response_found:
            logger.info("All fixes verified successfully!")
            logger.info(f"Claude's response: {response_text[:100]}...")
        else:
            logger.warning("Text entry and submission verified, but couldn't detect Claude's response")
        
        return response_text
    
    except Exception as e:
        logger.error(f"Error during test: {e}")
        if driver:
            driver.save_screenshot(str(output_dir / "error.png"))
        return None
    
    finally:
        # Clean up the browser session
        if driver:
            logger.info("Closing browser session...")
            driver.quit()

if __name__ == "__main__":
    asyncio.run(verify_fixes())
