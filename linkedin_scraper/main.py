from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import re
import json
import os
from fuzzywuzzy import fuzz
from linkedin_scraper.find_urls import get_linkedin_url_candidates
from linkedin_scraper.driver_and_login import get_driver, login
from linkedin_scraper.check_company import check_company_match, fuzzy_match_company


def wait_for_page_load(driver, timeout=20):
    """Wait for the page to be fully loaded using multiple strategies"""
    try:
        # Wait for basic page structure
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.TAG_NAME, "main"))
        )

        # Wait for profile-specific elements (try multiple selectors)
        profile_selectors = [
            ".pv-text-details__left-panel",
            ".ph5.pb5",
            ".pv-profile-section",
            "[data-view-name='profile-card']",
            ".artdeco-card"
        ]

        for selector in profile_selectors:
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                # print(f"Found element with selector: {selector}")
                return True
            except TimeoutException:
                continue

        # If none of the specific selectors work, just wait a bit more
        time.sleep(5)
        return True

    except TimeoutException:
        print("Page failed to load within timeout period")
        return False


def find_experience_section(driver):
    """Try multiple strategies to find the experience section"""

    # Common selectors for experience sections
    experience_selectors = [
        "section[data-view-name='profile-card']",
        "section[id*='experience']",
        "section[aria-labelledby*='experience']",
        ".pv-profile-section.experience-section",
        ".pvs-list",
        ".artdeco-card.pv-profile-section"
    ]

    for selector in experience_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                # print(f"Found experience section with selector: {selector}")
                return elements
        except Exception as e:
            print(f"Error with selector {selector}: {e}")
            continue

    # If no specific selectors work, try finding by text content
    try:
        sections = driver.find_elements(By.TAG_NAME, "section")
        for section in sections:
            if "experience" in section.get_attribute("innerHTML").lower():
                print("Found experience section by text content")
                return [section]
    except Exception as e:
        print(f"Error searching by text content: {e}")

    return []


def extract_position_info(item):
    """Extract position information from a job item"""
    position_info = {
        "job_title": "",
        "company": "",
        "employment_type": "",
        "date_range": "",
        "is_current": False
    }

    try:
        # Try multiple selectors for job title
        title_selectors = [
            ".t-bold span[aria-hidden='true']",
            "h3 span[aria-hidden='true']",
            ".pvs-entity__path-node span[aria-hidden='true']",
            ".t-16.t-black.t-bold"
        ]

        for selector in title_selectors:
            try:
                title_element = item.find_element(By.CSS_SELECTOR, selector)
                position_info["job_title"] = title_element.text.strip()
                break
            except NoSuchElementException:
                continue

        # Try multiple selectors for company info
        company_selectors = [
            ".t-14.t-normal span[aria-hidden='true']",
            ".t-14.t-black--light span[aria-hidden='true']",
            ".pvs-entity__caption-wrapper"
        ]

        for selector in company_selectors:
            try:
                company_elements = item.find_elements(By.CSS_SELECTOR, selector)
                for company_element in company_elements:
                    company_text = company_element.text.strip()
                    if company_text and "·" in company_text:
                        company_parts = company_text.split("·")
                        position_info["company"] = company_parts[0].strip()
                        if len(company_parts) > 1:
                            position_info["employment_type"] = company_parts[1].strip()
                        break
                if position_info["company"]:
                    break
            except NoSuchElementException:
                continue

        # Try to find date range
        date_selectors = [
            ".pvs-entity__caption-wrapper",
            ".t-14.t-black--light.t-normal",
            ".pv-entity__bullet-item-v2"
        ]

        for selector in date_selectors:
            try:
                date_elements = item.find_elements(By.CSS_SELECTOR, selector)
                for date_element in date_elements:
                    date_text = date_element.text.strip().lower()
                    if any(word in date_text for word in ["present", "current", "now"]):
                        position_info["date_range"] = date_element.text.strip()
                        position_info["is_current"] = True
                        break
                    elif any(word in date_text for word in ["month", "year", "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]):
                        position_info["date_range"] = date_element.text.strip()
                        break
                if position_info["date_range"]:
                    break
            except NoSuchElementException:
                continue

    except Exception as e:
        print(f"Error extracting position info: {e}")

    return position_info


def get_current_employer(profile_url, verbose=False):
    """
    Extract current employer from LinkedIn profile URL

    Args:
        profile_url (str): LinkedIn profile URL
        verbose (bool): If True, show detailed output. If False, suppress output

    Returns:
        list: List of current positions or empty list if not found
    """

    driver = get_driver()

    try:
        login(driver)

        # Navigate to profile
        if verbose:
            print(f"Navigating to profile: {profile_url}")
        driver.get(profile_url)

        # Wait for page to load with improved strategy
        if not wait_for_page_load(driver):
            if verbose:
                print("Failed to load profile page")
            return []

        if verbose:
            print("Page loaded successfully, looking for experience section...")

        # Additional wait for dynamic content
        time.sleep(3)

        current_positions = []

        # Find experience section with multiple strategies
        experience_sections = find_experience_section(driver)

        if not experience_sections:
            if verbose:
                print("No experience section found")
                # Debug: Save page source for inspection
                with open("debug_page_source.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                print("Page source saved to debug_page_source.html for inspection")
            return []

        if verbose:
            print(f"Found {len(experience_sections)} potential experience sections")

        # Process each experience section
        for section_idx, section in enumerate(experience_sections):
            if verbose:
                print(f"Processing section {section_idx + 1}")

            # Try different selectors for experience items
            item_selectors = [
                "li.artdeco-list__item",
                ".pvs-list__item",
                ".pv-entity__position-group-pager",
                ".pv-profile-section__list-item"
            ]

            experience_items = []
            for selector in item_selectors:
                try:
                    items = section.find_elements(By.CSS_SELECTOR, selector)
                    if items:
                        experience_items = items
                        if verbose:
                            print(f"Found {len(items)} experience items with selector: {selector}")
                        break
                except Exception as e:
                    continue

            if not experience_items:
                if verbose:
                    print(f"No experience items found in section {section_idx + 1}")
                continue

            # Process each experience item
            for item_idx, item in enumerate(experience_items):
                try:
                    position_info = extract_position_info(item)

                    if verbose:
                        print(f"Item {item_idx + 1}:")
                        print(f"  Title: {position_info['job_title']}")
                        print(f"  Company: {position_info['company']}")
                        print(f"  Date: {position_info['date_range']}")
                        print(f"  Current: {position_info['is_current']}")

                    # Only add if we found meaningful information and it's current
                    if position_info['is_current'] and (position_info['job_title'] or position_info['company']):
                        current_positions.append(position_info)

                except Exception as e:
                    if verbose:
                        print(f"Error processing item {item_idx + 1}: {e}")
                    continue

        return current_positions

    except TimeoutException:
        if verbose:
            print("Timeout waiting for page to load")
        return []

    except Exception as e:
        if verbose:
            print(f"Error occurred: {str(e)}")
        return []

    finally:
        driver.quit()


def get_current_employer_with_matching(profile_url, target_company, threshold=75, verbose=False):
    """
    Extract current employer from LinkedIn profile URL and check for company match

    Args:
        profile_url (str): LinkedIn profile URL
        target_company (str): Company name to match against
        email (str, optional): LinkedIn login email
        password (str, optional): LinkedIn login password
        threshold (int): Minimum similarity score for fuzzy matching
        verbose (bool): If True, show detailed output. If False, suppress output

    Returns:
        dict: Results including positions and match information
    """

    current_positions = get_current_employer(profile_url, verbose=verbose)

    if not current_positions:
        return {
            'current_positions': [],
            'company_match': {
                'has_match': False,
                'best_match': None,
                'all_matches': []
            }
        }

    # Check for company matches
    match_result = check_company_match(target_company, current_positions, threshold)

    return {
        'current_positions': current_positions,
        'company_match': match_result
    }


def is_employed_at_company(name, company, threshold=75, max_profiles=3, verbose=False):
    """
    Main function: Check if a person is currently employed at a specific company

    Args:
        name (str): Person's full name
        company (str): Company name to check
        threshold (int): Minimum similarity score for company name matching (0-100)
        max_profiles (int): Maximum number of LinkedIn profiles to check
        verbose (bool): If True, show detailed output. If False, only show final result

    Returns:
        bool: True if person is employed at the company, False otherwise
    """
    if verbose:
        print(f"Checking if {name} is employed at {company}")
        print("=" * 60)

    # Get LinkedIn profile candidates
    profile_urls = get_linkedin_url_candidates(name, company, limit=max_profiles)

    if not profile_urls:
        if verbose:
            print("No LinkedIn profiles found")
        return False

    if verbose:
        print(f"Found {len(profile_urls)} LinkedIn profile(s)")

    # Check each profile until we find a match
    for i, profile_url in enumerate(profile_urls):
        if verbose:
            print(f"\nChecking profile {i+1}/{len(profile_urls)}: {profile_url}")
            print("-" * 50)

        try:
            # Get current positions with company matching
            result = get_current_employer_with_matching(
                profile_url,
                company,
                threshold=threshold,
                verbose=verbose
            )

            current_positions = result['current_positions']
            company_match = result['company_match']

            if company_match['has_match']:
                if verbose:
                    best_match = company_match['best_match']
                    match_result = best_match['match_result']
                    position = best_match['position']

                    print(f"✅ MATCH FOUND!")
                    print(f"Position: {position['job_title']}")
                    print(f"Company: {position['company']}")
                    print(f"Match Score: {match_result['score']}/100")
                    print(f"Match Type: {match_result['match_type']}")

                return True
            else:
                if verbose:
                    print("❌ No company match found in this profile")

                    if current_positions:
                        print("Current positions found:")
                        for pos in current_positions:
                            if pos.get('company'):
                                match_result = fuzzy_match_company(company, pos['company'])
                                print(f"  - {pos['job_title']} at {pos['company']} (Score: {match_result['score']})")

        except Exception as e:
            if verbose:
                print(f"Error processing profile {i+1}: {e}")
            continue

    if verbose:
        print(f"\n❌ No employment match found for {name} at {company}")
    return False


if __name__ == "__main__":

    target_company = "GK Software SE"
    target_name = "Abril M Tenorio"


    is_employed = is_employed_at_company(target_name, target_company)

    print(is_employed)