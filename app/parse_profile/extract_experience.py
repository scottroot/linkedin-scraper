# This module takes company names found on LinkedIn and compares them to a target company name
import sys
sys.path.append("/Users/scomax/Documents/Git/linkedin-scraper/")

import os
import time
from typing import Any, Dict, List, Literal
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from app.driver_and_login import get_driver, login, cleanup_driver
from app.parse_profile.wait_for_page_load import wait_for_page_load
from app.logger import get_logger


LINKEDIN_PAGE_LOAD_TIMEOUT = int(os.getenv("LINKEDIN_PAGE_LOAD_TIMEOUT", 15))


def find_experience_section(driver, timeout=10):
    """
    Try multiple strategies to find the experience section.
    Used by get_current_employer()
    """
    logger = get_logger()

    try:
        # Find all sections with class artdeco-card using Selenium
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "li.artdeco-list__item"))
        )
        artdeco_sections = driver.find_elements(By.CSS_SELECTOR, "section.artdeco-card")
        logger.info(f"Found {len(artdeco_sections)} artdeco-card sections")

        # Check each section individually
        for i, section in enumerate(artdeco_sections):
            try:
                # Get the HTML content of this specific section
                section_html = section.get_attribute('outerHTML')
                soup = BeautifulSoup(section_html, 'html.parser')

                exp_div = soup.find("div", id="experience", class_="pv-profile-card__anchor")
                if(exp_div):
                    return [section]

                # # Debug: Log all heading elements in this section
                # all_headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                # logger.info(f"Section {i}: Found {len(all_headings)} heading elements")
                # for j, heading in enumerate(all_headings):
                #     heading_text = heading.get_text().strip()
                #     logger.info(f"  Heading {j}: '{heading_text}' (tag: {heading.name})")

                # Look for h2 elements within this section
                # experience_div = soup.find('div', id='experience')
                # h2_elements = soup.find_all('h2')
                # for h2 in h2_elements:
                #     # Check the h2 text directly (including nested elements)
                #     h2_text = h2.get_text().strip().lower()
                #     logger.info(f"Checking h2 text: '{h2_text}'")
                #     if "experience" in h2_text:
                #         logger.info(f"Found experience section with h2 text: '{h2.get_text().strip()}'")
                #         return [section]  # Return the original Selenium element

            except Exception as e:
                logger.debug(f"Error processing section {i}: {e}")
                continue

        logger.warning("No artdeco-card section found with 'Experience' h2")

    except Exception as e:
        logger.error(f"Error finding artdeco-card sections: {e}")

    # Fallback: try finding by text content in any section
    try:
        logger.debug("Trying to find sections by text content...")
        sections = driver.find_elements(By.TAG_NAME, "section")
        for i, section in enumerate(sections):
            try:
                section_text = section.get_attribute("innerHTML").lower()
                if "experience" in section_text or "work" in section_text or "employment" in section_text:
                    logger.debug("Found experience section by text content")
                    return [section]
            except Exception as e:
                # Handle stale element reference
                logger.debug(f"Stale section element at index {i}, skipping: {e}")
                continue
    except Exception as e:
        logger.error(f"Error searching by text content: {e}")

    # Try alternative selectors for experience sections
    try:
        logger.debug("Trying alternative selectors for experience sections...")
        alternative_selectors = [
            ".pvs-list__item--line-separated",
            ".pvs-entity",
            ".pv-entity__position-group-pager",
            ".pv-profile-section__list-item",
            "[data-section='experience']",
            "[data-test-id='experience-section']"
        ]

        for selector in alternative_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    logger.debug(f"Found {len(elements)} elements with selector: {selector}")
                    return elements
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
                continue
    except Exception as e:
        logger.error(f"Error with alternative selectors: {e}")

    # Last resort: try to find any content that might contain experience info
    try:
        logger.debug("Trying to find any content sections...")
        all_sections = driver.find_elements(By.CSS_SELECTOR, "section, .artdeco-card, .pvs-list")
        if all_sections:
            logger.debug(f"Found {len(all_sections)} potential sections, returning first few")
            return all_sections[:3]  # Return first 3 sections as potential experience sections
    except Exception as e:
        logger.error(f"Error in last resort search: {e}")

    exit("No experience section found for profile...")
    return []


def extract_position_info(item) -> Dict[Literal['job_title', 'company', 'employment_type', 'date_range', 'is_current'], Any]:
    """
    Extract position information from a job item using BeautifulSoup.
    Used by get_current_employer()
    Returns a dictionary with the following keys:
    - job_title (str)
    - company (str)
    - employment_type (str)
    - date_range (str)
    - is_current (bool)

    Position with multiple roles:
    Company = 1st title
    Dates = 1st t-14 t-normal t-black--light

    Position with single role:
    Company = 1st span t-14 t-normal
    Dates = 1st t-14 t-normal t-black--light /// Also span pvs-entity__caption-wrapper
    """
    logger = get_logger()
    position_info = {
        "job_title": "",
        "company": "",
        "employment_type": "",
        "date_range": "",
        "is_current": False
    }

    try:
        # Get the HTML content of the item and parse with BeautifulSoup
        try:
            item_html = item.get_attribute('outerHTML')
        except Exception as e:
            logger.warning(f"Stale element reference when getting HTML: {e}")
            return position_info

        soup = BeautifulSoup(item_html, 'html.parser')

        title_divs = soup.select("div.hoverable-link-text.t-bold")

        # MULTI-ROLE POSITION
        if len(title_divs) > 1:

            print(f"Found multiple ({len(title_divs)}) titles - this is a multi-role position.")
            # FIND COMPANY
            company_span = title_divs[0].find('span', attrs={'aria-hidden': 'true'})
            if company_span:
                company_text = company_span.get_text().strip()
                if company_text and len(company_text) > 2:  # Filter out very short text
                    position_info["company"] = company_text

            title_span = title_divs[1].find('span', attrs={'aria-hidden': 'true'})
            if title_span:
                title_text = title_span.get_text().strip()
                if title_text and len(title_text) > 2:  # Filter out very short text
                    position_info["title"] = title_text

        # SINGLE ROLE POSITION
        elif len(title_divs) == 1:
            print(f"Found single title - this is a single-role position.")
            title_span = title_divs[0].find('span', attrs={'aria-hidden': 'true'})
            if title_span:
                title_text = title_span.get_text().strip()
                if title_text and len(title_text) > 2:  # Filter out very short text
                    position_info["title"] = title_text

            company_spans = soup.select("span.t-14.t-normal")
            company_span = company_spans[0].find('span', attrs={'aria-hidden': 'true'})
            if company_span:
                company_text = company_span.get_text().strip()
                if company_text and len(company_text) > 2:  # Filter out very short text
                    position_info["company"] = company_text

        else:
            print("No title found")

        # FIND DATES
        date_divs = soup.select("span.t-14.t-normal.t-black--light")
        for div in date_divs:
            span = div.find('span', attrs={'aria-hidden': 'true'})
            if span:
                text = span.get_text().strip().lower()
                if text and len(text) > 2:  # Filter out very short text
                    if any(word in text for word in ["present", "current", "now", "today", "month", "year", "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]):
                        # Additional validation: check if it looks like a date range
                        if any(char.isdigit() for char in text) or any(word in text for word in ["present", "current", "now", "today"]):
                            # date_range = text.split("·")[0].strip()
                            position_info["date_range"] = date_range = text.split("·")[0].strip()
                            if any(word in text for word in ["present", "current", "now", "today"]):
                                position_info["is_current"] = True
                            break

    except Exception as e:
        logger.error(f"Error extracting position info: {e}")

    return position_info


def get_current_employer(
    driver,
    profile_url,
    verbose=False
) -> List[Dict[Literal['job_title', 'company', 'employment_type', 'date_range', 'is_current'], Any]]:
    """
    Extract current employer from LinkedIn profile URL using existing driver
    Returns a list of dictionaries with the following keys:
    - job_title
    - company
    - employment_type
    - date_range
    - is_current
    """
    logger = get_logger()
    current_positions = []

    try:
        logger.info(f"Navigating to profile: {profile_url}")
        driver.get(profile_url)

        # Wait for page to load
        # if not wait_for_page_load(driver):
        #     logger.error("Failed to wait for page load")
        #     return []
        try:
            WebDriverWait(driver, LINKEDIN_PAGE_LOAD_TIMEOUT).until(
                EC.presence_of_element_located((By.TAG_NAME, "main"))
            )
        except TimeoutException:
            WebDriverWait(driver, LINKEDIN_PAGE_LOAD_TIMEOUT).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

        WebDriverWait(driver, LINKEDIN_PAGE_LOAD_TIMEOUT * 2).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.artdeco-list__item"))
        )

        logger.debug("Page loaded successfully, looking for experience section...")

        experience_sections = find_experience_section(driver)
        if not experience_sections:
            logger.warning("No experience sections found")
            return []
        logger.debug(f"Found {len(experience_sections)} experience sections")

        # Process each experience section
        for section_idx, section in enumerate(experience_sections):
            logger.debug(f"Processing experience section {section_idx + 1}")

            # Try different selectors for experience items
            item_selectors = [
                "li.artdeco-list__item",
                ".artdeco-list__item",
                "li",
            ]

            # Process items immediately after finding them to avoid stale element issues
            for selector in item_selectors:
                try:
                    items = section.find_elements(By.CSS_SELECTOR, selector)
                    if items:
                        logger.info(f"Found {len(items)} experience items with selector: {selector}")

                        # Process each item immediately to avoid stale element issues
                        for item_idx, item in enumerate(items):
                            try:
                                # Get the HTML content immediately to avoid stale element issues
                                position_info = extract_position_info(item)

                                logger.info(f"Item {item_idx + 1}:")
                                logger.info(f"  Title: {position_info['job_title']}")
                                logger.info(f"  Company: {position_info['company']}")
                                logger.info(f"  Date: {position_info['date_range']}")
                                logger.info(f"  Current: {position_info['is_current']}")

                                # Add positions that are either:
                                # 1. Current positions with dates (is_current = True)
                                # 2. Positions with company info but no dates (for "No dates listed" detection)
                                if (position_info['is_current'] and (position_info['job_title'] or position_info['company'])) or \
                                   (position_info['company'] and not position_info['date_range'] and (position_info['job_title'] or position_info['company'])):
                                    current_positions.append(position_info)
                                    if position_info['is_current']:
                                        logger.info(f"  -> Added to current positions (with dates)")
                                    else:
                                        logger.info(f"  -> Added to current positions (no dates)")

                            except Exception as e:
                                logger.error(f"Error processing item {item_idx + 1}: {e}")
                                continue

                            # Small delay to prevent overwhelming the page
                            time.sleep(0.1)

                        # If we successfully processed items with this selector, break
                        break

                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue

            # If we found and processed items in this section, we can move to the next section
            if current_positions:
                logger.debug(f"Found current positions in section {section_idx + 1}, moving to next section")
                continue

        logger.info(f"Total current positions found: {len(current_positions)}")
        return current_positions

    except TimeoutException:
        logger.error("Timeout waiting for page to load")
        return []

    except Exception as e:
        logger.error(f"Error in get_current_employer: {e}")
        return []


if __name__ == "__main__":
    driver = get_driver(headless=True)
    login(driver)
    profile_url = "https://www.linkedin.com/in/abhi-p-11004211/"
    result = get_current_employer(driver, profile_url)
    print(result)
    cleanup_driver(driver)

