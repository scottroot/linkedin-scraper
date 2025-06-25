from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import json
import os


def get_driver():
    """Initialize and configure Chrome WebDriver"""
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver


def login(driver):
    """Handle LinkedIn login with cookie management"""
    print("Please log in manually in the browser window.")
    driver.get("https://www.linkedin.com")

    # Load existing cookies if available
    cookies_path = "linkedin_cookies.json"
    if os.path.exists(cookies_path):
        try:
            with open(cookies_path, "r") as f:
                cookies = json.load(f)
                for cookie in cookies:
                    # Remove 'expiry' field if it causes an error
                    cookie.pop("expiry", None)
                    driver.add_cookie(cookie)
        except Exception as e:
            print(f"Error loading cookies: {e}")

    driver.get("https://www.linkedin.com/login")
    input("After logging in and passing any CAPTCHA, press Enter to continue...")

    # Save cookies for future use
    try:
        cookies = driver.get_cookies()
        with open(cookies_path, "w") as f:
            json.dump(cookies, f, indent=2)
    except Exception as e:
        print(f"Error saving cookies: {e}")
