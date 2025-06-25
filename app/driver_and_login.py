from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
import json
import os
import gc


def get_driver(headless=False):
    """Initialize and configure Chrome WebDriver with better error handling"""
    try:
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless=new")
        else:
            chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # Add memory management options
        chrome_options.add_argument("--memory-pressure-off")

        # Add options to prevent crashes
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")

        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        # Set page load timeout
        driver.set_page_load_timeout(30)
        driver.implicitly_wait(10)
        print("Setting -> page load timeout = 30 seconds; implicit wait for element = 10 seconds")

        return driver

    except WebDriverException as e:
        print(f"WebDriver initialization error: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error initializing WebDriver: {e}")
        raise


def login(driver):
    """Handle LinkedIn login with cookie management and better error handling"""
    try:
        print("Please log in manually in the browser window.")
        driver.get("https://www.linkedin.com")

        # Load existing cookies if available
        cookies_path = "linkedin_cookies.json"
        cookies_exist = os.path.exists(cookies_path)
        if cookies_exist:
            try:
                with open(cookies_path, "r") as f:
                    cookies = json.load(f)
                    for cookie in cookies:
                        # Remove 'expiry' field if it causes an error
                        cookie.pop("expiry", None)
                        try:
                            driver.add_cookie(cookie)
                        except Exception as cookie_error:
                            print(f"Error adding cookie: {cookie_error}")
                            continue
            except Exception as e:
                print(f"Error loading cookies: {e}")

        driver.get("https://www.linkedin.com/login")
        if not cookies_exist:
            print("Press Enter to continue after logging in...")
            input("After logging in and passing any CAPTCHA, press Enter to continue...")
        else:
            print("Cookies loaded. If you need to log in manually, please do so now.")

        # Save cookies for future use
        try:
            cookies = driver.get_cookies()
            with open(cookies_path, "w") as f:
                json.dump(cookies, f, indent=2)
        except Exception as e:
            print(f"Error saving cookies: {e}")

    except Exception as e:
        print(f"Error during login process: {e}")
        raise


def cleanup_driver(driver):
    """Safely cleanup WebDriver resources"""
    try:
        if driver:
            # Close all windows
            driver.close()
            driver.quit()
    except Exception as e:
        print(f"Error closing driver: {e}")
    finally:
        # Force garbage collection
        gc.collect()
