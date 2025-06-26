import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


def wait_for_page_load(driver, timeout=10, selectors=[".artdeco-card"]):
    """
    Wait for the page to be fully loaded using multiple strategies
    """
    try:
        print(f"Waiting up to {timeout} seconds for page to load...")

        # Wait for basic page structure - try multiple approaches
        try:
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "main"))
            )
        except TimeoutException:
            # Fallback: wait for body or any content
            try:
                WebDriverWait(driver, timeout).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except TimeoutException:
                print("Page failed to load basic structure")
                return False


        element_found = False
        for selector in selectors:
            try:
                print(f"Waiting up to 5 seconds for profile element: {selector}")
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                print(f"Found element with selector: {selector}")
                element_found = True
                break
            except TimeoutException:
                continue

        # If no specific selectors work, check if page has loaded any content
        if not element_found:
            print("No specific profile elements found, checking for any content...")
            try:
                # Wait for any content to be present
                WebDriverWait(driver, 10).until(
                    lambda d: len(d.find_elements(By.TAG_NAME, "div")) > 10
                )
                print("Page has loaded with content, proceeding...")
                element_found = True
            except TimeoutException:
                print("Page appears to be empty or not loading properly")
                return False

        # Additional wait for Experience section to load
        print("Waiting for Experience section to load...")
        try:
            # Wait for experience-related elements to appear
            WebDriverWait(driver, 10).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, "li.artdeco-list__item")) > 0
            )
            print("Experience section elements found")
        except TimeoutException:
            print("Warning: Experience section elements not found within timeout")
            # Don't fail here, just log the warning

        # Additional wait for dynamic content to fully load
        print("Waiting 2 seconds for dynamic content to fully load...")
        time.sleep(2)

        return element_found

    except TimeoutException:
        print("Page failed to load within timeout period")
        return False
    except Exception as e:
        print(f"Unexpected error during page load wait: {e}")
        return False
