from linkedin_scraper.driver_and_login import get_driver, login
from linkedin_scraper.find_urls import get_linkedin_url_candidates
from linkedin_scraper.check_company import check_company_match, fuzzy_match_company
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd
import time
import re

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
                return elements
        except Exception as e:
            continue

    # If no specific selectors work, try finding by text content
    try:
        sections = driver.find_elements(By.TAG_NAME, "section")
        for section in sections:
            if "experience" in section.get_attribute("innerHTML").lower():
                return [section]
    except Exception as e:
        pass

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
        pass

    return position_info

def get_current_employer_with_driver(driver, profile_url, verbose=False):
    """
    Extract current employer from LinkedIn profile URL using existing driver
    """
    current_positions = []

    try:
        # Navigate to profile
        driver.get(profile_url)

        # Wait for page to load
        if not wait_for_page_load(driver):
            return []

        # Find experience sections
        experience_sections = find_experience_section(driver)

        if not experience_sections:
            return []

        # Process each experience section
        for section_idx, section in enumerate(experience_sections):
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
                        break
                except Exception as e:
                    continue

            if not experience_items:
                continue

            # Process each experience item
            for item_idx, item in enumerate(experience_items):
                try:
                    position_info = extract_position_info(item)

                    # Only add if we found meaningful information and it's current
                    if position_info['is_current'] and (position_info['job_title'] or position_info['company']):
                        current_positions.append(position_info)

                except Exception as e:
                    continue

        return current_positions

    except TimeoutException:
        return []

    except Exception as e:
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

def process_contacts_batch(contacts_df, batch_size=5, delay_between_batches=30):
    """
    Process contacts in batches, checking employment status and updating the CSV

    Args:
        contacts_df: DataFrame with contact information
        batch_size: Number of contacts to process before saving
        delay_between_batches: Seconds to wait between batches to avoid rate limiting
    """

    total_rows = len(contacts_df)
    print(f"Processing {total_rows} contacts in batches of {batch_size}")

    # Initialize a single browser session for all processing
    print("Initializing browser session...")
    driver = get_driver()

    try:
        # Login once at the beginning
        print("Logging into LinkedIn...")
        login(driver)
        print("Login successful!")

        for i in range(0, total_rows, batch_size):
            batch_end = min(i + batch_size, total_rows)
            batch = contacts_df.iloc[i:batch_end]

            print(f"\n--- Processing batch {i//batch_size + 1} (rows {i+1}-{batch_end}) ---")

            for idx, row in batch.iterrows():
                # Skip if already processed (Valid column has a boolean value)
                if pd.notna(row['Valid']) and isinstance(row['Valid'], bool):
                    print(f"Skipping {row['First Name']} {row['Last Name']} - already processed")
                    continue

                # Join first and last name
                full_name = f"{row['First Name']} {row['Last Name']}"
                company_name = row['Account Name']

                print(f"Checking: {full_name} at {company_name}")

                try:
                    # Check employment status using the shared driver
                    is_employed = check_employment_with_driver(driver, full_name, company_name)

                    # Update the Valid column
                    contacts_df.at[idx, 'Valid'] = is_employed

                    print(f"Result: {is_employed}")

                    # Small delay between individual checks
                    time.sleep(2)

                except Exception as e:
                    print(f"Error processing {full_name}: {e}")
                    # Mark as False if there's an error
                    contacts_df.at[idx, 'Valid'] = False

            # Save the CSV after each batch
            contacts_df.to_csv('contacts.csv', index=False)
            print(f"Batch {i//batch_size + 1} completed and saved")

            # Delay between batches (except for the last batch)
            if batch_end < total_rows:
                print(f"Waiting {delay_between_batches} seconds before next batch...")
                time.sleep(delay_between_batches)

        print(f"\nAll {total_rows} contacts processed successfully!")

    finally:
        # Always close the browser when done
        print("Closing browser...")
        driver.quit()

def check_employment_with_driver(driver, name, company, threshold=75, max_profiles=3, verbose=False):
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
            # Get current positions with company matching using existing driver
            result = get_current_employer_with_matching_and_driver(
                driver,
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

def main():
    # Read the CSV file
    print("Reading contacts.csv...")
    contacts_df = pd.read_csv('contacts.csv')

    # Display initial data
    print(f"Found {len(contacts_df)} contacts")
    print("\nFirst few rows:")
    print(contacts_df.head())

    # Check if Valid column exists, if not create it with proper dtype
    if 'Valid' not in contacts_df.columns:
        contacts_df['Valid'] = None
        print("\nCreated 'Valid' column")
    else:
        # Convert existing Valid column to object dtype to handle both bool and NaN
        contacts_df['Valid'] = contacts_df['Valid'].astype('object')
        print("\nConverted 'Valid' column to object dtype")

    # Process contacts in batches
    process_contacts_batch(contacts_df, batch_size=5, delay_between_batches=30)

    # Display final results
    print("\nFinal results:")
    print(contacts_df[['First Name', 'Last Name', 'Account Name', 'Valid']].head(10))

if __name__ == "__main__":
    main()