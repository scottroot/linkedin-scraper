# This module takes company names found on LinkedIn and compares them to a target company name
import re
import time
import gc
from fuzzywuzzy import fuzz
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from app.driver_and_login import get_driver, login, cleanup_driver
from app.find_urls import get_linkedin_url_candidates
import pandas as pd


def process_contacts_batch(contacts_df, batch_size=5, delay_between_batches=30, log_callback=None, save_callback=None, stop_flag=None):
    """
    Process contacts in batches, checking employment status and updating the CSV

    Args:
        contacts_df: DataFrame with contact information
        batch_size: Number of contacts to process before saving
        delay_between_batches: Seconds to wait between batches to avoid rate limiting
        log_callback: Optional callback function for logging messages
        save_callback: Optional callback function for saving progress
        stop_flag: Optional threading.Event or similar to check for stop signal
    """

    def log(message):
        if log_callback:
            log_callback(message)
        else:
            print(message)

    total_rows = len(contacts_df)
    log(f"Processing {total_rows} contacts in batches of {batch_size}")

    # Initialize a single browser session for all processing
    log("Initializing browser session...")
    driver = None

    try:
        driver = get_driver(headless=True)

        # Login once at the beginning
        log("Logging into LinkedIn...")
        log("NOTE: A browser window will open. Please log in manually if needed.")
        log("The GUI will remain responsive during this process.")
        login(driver)
        log("Login successful!")

        for i in range(0, total_rows, batch_size):
            # Check stop flag before processing each batch
            if stop_flag and stop_flag.is_set():
                log("Stop signal received. Stopping processing.")
                return contacts_df

            batch_end = min(i + batch_size, total_rows)
            batch = contacts_df.iloc[i:batch_end]

            log(f"\n--- Processing batch {i//batch_size + 1} (rows {i+1}-{batch_end}) ---")

            for idx, row in batch.iterrows():
                # Check stop flag before processing each contact
                if stop_flag and stop_flag.is_set():
                    log("Stop signal received. Stopping processing.")
                    return contacts_df

                # Skip if already processed (Valid column has a boolean value)
                if pd.notna(row['Valid']) and isinstance(row['Valid'], bool):
                    log(f"Skipping {row['First Name']} {row['Last Name']} - already processed")
                    continue

                # Join first and last name
                full_name = f"{row['First Name']} {row['Last Name']}"
                company_name = row['Account Name']

                log(f"Checking: {full_name} at {company_name}")

                try:
                    # Check employment status using the shared driver
                    is_employed = check_employment_with_driver(driver, full_name, company_name)

                    # Update the Valid column
                    contacts_df.at[idx, 'Valid'] = is_employed

                    log(f"Result: {is_employed}")

                    # Small delay between individual checks
                    log("Waiting 2 seconds between individual contact checks to avoid rate limiting...")
                    time.sleep(2)

                except Exception as e:
                    log(f"Error processing {full_name}: {e}")
                    # Mark as False if there's an error
                    contacts_df.at[idx, 'Valid'] = False
                    # Force garbage collection after error
                    gc.collect()

            # Save progress after each batch
            if save_callback:
                save_callback(contacts_df)
            else:
                # Default behavior: save to contacts.csv
                contacts_df.to_csv('contacts.csv', index=False)

            log(f"Batch {i//batch_size + 1} completed and saved")

            # Force garbage collection after each batch
            gc.collect()

            # Delay between batches (except for the last batch)
            if batch_end < total_rows:
                log(f"Waiting {delay_between_batches} seconds before next batch...")
                time.sleep(delay_between_batches)

            # Check stop flag
            if stop_flag and stop_flag.is_set():
                log("Stop signal received. Stopping processing.")
                break

        log(f"\nAll {total_rows} contacts processed successfully!")
        return contacts_df

    except Exception as e:
        log(f"Error during processing: {e}")
        raise

    finally:
        # Always close the browser when done
        if driver:
            log("Closing browser...")
            cleanup_driver(driver)
            # Force garbage collection after cleanup
            gc.collect()


def check_employment_with_driver(driver, name, company, threshold=75, max_profiles=2, verbose=False):
    """
    Check if a person is currently employed at a specific company using an existing driver

    Args:
        driver: Existing WebDriver instance
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
    print(f"Searching for LinkedIn profiles for {name} at {company}...")
    profile_urls = get_linkedin_url_candidates(name, company, limit=max_profiles)

    if not profile_urls:
        print("No LinkedIn profiles found")
        return False

    print(f"Found {len(profile_urls)} LinkedIn profile candidates")

    # Check each profile
    for i, profile_url in enumerate(profile_urls):
        print(f"Checking profile {i+1}/{len(profile_urls)}: {profile_url}")

        try:
            # Get current employer information
            result = get_current_employer_with_matching_and_driver(driver, profile_url, company, threshold, verbose=verbose)

            if result['company_match']['has_match']:
                print(f"Found employment match: {result['company_match']['best_match']}")
                return True
            else:
                print("No employment match found for this profile")

        except Exception as e:
            print(f"Error checking profile {i+1}: {e}")
            continue

    print("No employment match found across all profiles")
    return False


def find_experience_section(driver):
    """Try multiple strategies to find the experience section"""
    # Common selectors for experience sections
    # TODO: verify i can just use artdeco-card...
    experience_selectors = [
        # Primary selectors for experience sections
        # "section[data-view-name='profile-card']",
        # "section[id*='experience']",
        # "section[aria-labelledby*='experience']",
        # ".pv-profile-section.experience-section",
        # ".pvs-list",
        # ".artdeco-card.pv-profile-section",
        # # New LinkedIn selectors
        # "[data-section='experience']",
        # ".pvs-profile-content section",
        # ".scaffold-finite-scroll section",
        # # Generic section selectors
        # "section",
        ".artdeco-card"
    ]

    for selector in experience_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                print(f"Found experience section with selector: {selector}")
                return elements
        except Exception as e:
            print(f"Error with selector {selector}: {e}")
            continue

    # If no specific selectors work, try finding by text content
    try:
        print("Trying to find sections by text content...")
        sections = driver.find_elements(By.TAG_NAME, "section")
        for section in sections:
            try:
                section_text = section.get_attribute("innerHTML").lower()
                if "experience" in section_text or "work" in section_text or "employment" in section_text:
                    print("Found experience section by text content")
                    return [section]
            except Exception as e:
                continue
    except Exception as e:
        print(f"Error searching by text content: {e}")

    # Last resort: try to find any content that might contain experience info
    try:
        print("Trying to find any content sections...")
        all_sections = driver.find_elements(By.CSS_SELECTOR, "section, .artdeco-card, .pvs-list")
        if all_sections:
            print(f"Found {len(all_sections)} potential sections, returning first few")
            return all_sections[:3]  # Return first 3 sections as potential experience sections
    except Exception as e:
        print(f"Error in last resort search: {e}")

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
            ".t-16.t-black.t-bold",
            ".pvs-entity__path-node",
            ".t-bold",
            "h3",
            ".pvs-list__item--line-separated .t-bold",
            ".pvs-entity__path-node .t-bold"
        ]

        for selector in title_selectors:
            try:
                title_element = item.find_element(By.CSS_SELECTOR, selector)
                title_text = title_element.text.strip()
                if title_text:
                    position_info["job_title"] = title_text
                    break
            except NoSuchElementException:
                continue

        # Try multiple selectors for company info
        company_selectors = [
            ".t-14.t-normal span[aria-hidden='true']",
            ".t-14.t-black--light span[aria-hidden='true']",
            ".pvs-entity__caption-wrapper",
            ".t-14.t-normal",
            ".t-14.t-black--light",
            ".pvs-entity__caption-wrapper span",
            ".pvs-list__item--line-separated .t-14"
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
                    elif company_text and not position_info["company"]:
                        # If no bullet separator, just use the text as company
                        position_info["company"] = company_text
                if position_info["company"]:
                    break
            except NoSuchElementException:
                continue

        # Try to find date range
        date_selectors = [
            ".pvs-entity__caption-wrapper",
            ".t-14.t-black--light.t-normal",
            ".pv-entity__bullet-item-v2",
            ".t-14.t-black--light",
            ".pvs-entity__caption-wrapper span",
            ".pvs-list__item--line-separated .t-14"
        ]

        for selector in date_selectors:
            try:
                date_elements = item.find_elements(By.CSS_SELECTOR, selector)
                for date_element in date_elements:
                    date_text = date_element.text.strip().lower()
                    if any(word in date_text for word in ["present", "current", "now", "today"]):
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

        # If we still don't have a date range, try to infer if it's current
        if not position_info["date_range"] and position_info["job_title"]:
            # Check if the item itself suggests it's current (e.g., no end date visible)
            item_text = item.text.lower()
            if "present" in item_text or "current" in item_text:
                position_info["is_current"] = True

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
        print("Waiting 3 seconds for dynamic content to fully load...")
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
                ".pv-profile-section__list-item",
                ".pvs-list__item--line-separated",
                ".pvs-entity",
                ".artdeco-list__item",
                "li",
                ".pvs-list__item--with-top-padding"
            ]

            experience_items = []
            for selector in item_selectors:
                try:
                    items = section.find_elements(By.CSS_SELECTOR, selector)
                    if items:
                        experience_items = items
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
        cleanup_driver(driver)


def get_current_employer_with_driver(driver, profile_url, verbose=False):
    """
    Extract current employer from LinkedIn profile URL using existing driver
    """
    current_positions = []

    try:
        # Navigate to profile
        print(f"Navigating to profile: {profile_url}")
        driver.get(profile_url)

        # Wait for page to load
        if not wait_for_page_load(driver):
            print("Failed to wait for page load")
            return []

        print("Page loaded successfully, looking for experience section...")

        # Find experience sections
        experience_sections = find_experience_section(driver)

        if not experience_sections:
            print("No experience sections found")
            return []

        print(f"Found {len(experience_sections)} experience sections")

        # Process each experience section
        for section_idx, section in enumerate(experience_sections):
            print(f"Processing experience section {section_idx + 1}")

            # Try different selectors for experience items
            item_selectors = [
                "li.artdeco-list__item",
                ".pvs-list__item",
                ".pv-entity__position-group-pager",
                ".pv-profile-section__list-item",
                ".pvs-list__item--line-separated",
                ".pvs-entity",
                ".artdeco-list__item",
                "li",
                ".pvs-list__item--with-top-padding"
            ]

            experience_items = []
            for selector in item_selectors:
                try:
                    items = section.find_elements(By.CSS_SELECTOR, selector)
                    if items:
                        experience_items = items
                        print(f"Found {len(items)} experience items with selector: {selector}")
                        break
                except Exception as e:
                    continue

            if not experience_items:
                print(f"No experience items found in section {section_idx + 1}")
                continue

            # Process each experience item
            for item_idx, item in enumerate(experience_items):
                try:
                    position_info = extract_position_info(item)

                    print(f"Item {item_idx + 1}:")
                    print(f"  Title: {position_info['job_title']}")
                    print(f"  Company: {position_info['company']}")
                    print(f"  Date: {position_info['date_range']}")
                    print(f"  Current: {position_info['is_current']}")

                    # Only add if we found meaningful information and it's current
                    if position_info['is_current'] and (position_info['job_title'] or position_info['company']):
                        current_positions.append(position_info)
                        print(f"  -> Added to current positions")

                except Exception as e:
                    print(f"Error processing item {item_idx + 1}: {e}")
                    continue

        print(f"Total current positions found: {len(current_positions)}")
        return current_positions

    except TimeoutException:
        print("Timeout waiting for page to load")
        return []

    except Exception as e:
        print(f"Error in get_current_employer_with_driver: {e}")
        return []

def get_current_employer_with_matching_and_driver(driver, profile_url, target_company, threshold=75, verbose=False):
    """
    Extract current employer from LinkedIn profile URL and check for company match using existing driver
    """
    current_positions = get_current_employer_with_driver(driver, profile_url, verbose=verbose)

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


def get_current_employer_with_matching(profile_url, target_company, threshold=75, verbose=False):
    """
    Extract current employer from LinkedIn profile URL and check for company match

    Args:
        profile_url (str): LinkedIn profile URL
        target_company (str): Company name to match against
        threshold (int): Minimum similarity score for fuzzy matching
        verbose (bool): If True, show detailed output. If False, suppress output

    Returns:
        dict: Results including positions and match information
    """

    # Create a new driver for this function (for backward compatibility)
    # Note: This function should ideally be called with an existing driver
    # using get_current_employer_with_matching_and_driver instead
    driver = get_driver()

    try:
        login(driver)
        current_positions = get_current_employer_with_driver(driver, profile_url, verbose=verbose)
    finally:
        cleanup_driver(driver)

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