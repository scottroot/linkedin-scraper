# This module takes company names found on LinkedIn and compares them to a target company name
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
        item_html = item.get_attribute('outerHTML')
        soup = BeautifulSoup(item_html, 'html.parser')

        # Get all text elements once for use throughout the function
        all_text_elements = soup.find_all(text=True)

        # Extract job title - look for bold text that's likely a job title
        title_candidates = []

        # Look for the specific LinkedIn job title structure
        # div with hoverable-link-text t-bold classes containing span with aria-hidden="true"
        title_divs = soup.find_all('div', class_='hoverable-link-text t-bold')
        for div in title_divs:
            # Look for span with aria-hidden="true" within the div
            span = div.find('span', attrs={'aria-hidden': 'true'})
            if span:
                text = span.get_text().strip()
                if text and len(text) > 2:  # Filter out very short text
                    title_candidates.append(text)

        # Fallback: look for elements with t-bold class
        if not title_candidates:
            bold_elements = soup.find_all(class_='t-bold')
            for element in bold_elements:
                text = element.get_text().strip()
                if text and len(text) > 2:  # Filter out very short text
                    title_candidates.append(text)

        # Take the first meaningful title candidate and deduplicate
        if title_candidates:
            # Remove duplicates while preserving order
            seen = set()
            unique_titles = []
            for title in title_candidates:
                if title not in seen:
                    seen.add(title)
                    unique_titles.append(title)

            if unique_titles:
                position_info["job_title"] = unique_titles[0]
                logger.debug(f"Found job title: {unique_titles[0]}")

        # Extract company and employment type
        # First, try to find company name from logo alt text
        logo_img = soup.find('img', attrs={'alt': True})
        if logo_img:
            alt_text = logo_img.get('alt', '').strip()
            if alt_text.endswith(' logo'):
                company_name = alt_text[:-5]  # Remove " logo" from the end
                if company_name:
                    position_info["company"] = company_name
                    logger.debug(f"Found company from logo alt text: {company_name}")

        # If we didn't find company from logo, fall back to text-based extraction
        if not position_info["company"]:
            company_candidates = []

            for text in all_text_elements:
                text_clean = text.strip()
                if text_clean and "·" in text_clean:
                    company_candidates.append(text_clean)

            # Also look for elements with t-14 class (common for company info)
            t14_elements = soup.find_all(class_='t-14')
            for element in t14_elements:
                text = element.get_text().strip()
                if text and len(text) > 2:
                    company_candidates.append(text)

            # Process company candidates
            for candidate in company_candidates:
                if "·" in candidate:
                    parts = candidate.split("·")
                    company_part = parts[0].strip()
                    if company_part and len(company_part) > 1:
                        position_info["company"] = company_part
                        if len(parts) > 1:
                            position_info["employment_type"] = parts[1].strip()
                        break
                elif not position_info["company"] and len(candidate) > 2:
                    # If no bullet separator, use as company if we don't have one yet
                    position_info["company"] = candidate

        # Extract date range and determine if current
        date_candidates = []

        # Look for date-like text patterns in all text elements
        for text in all_text_elements:
            text_clean = text.strip()
            if text_clean and len(text_clean) > 2:
                # Check for date patterns
                text_lower = text_clean.lower()
                if any(word in text_lower for word in ["present", "current", "now", "today", "month", "year", "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]):
                    # Additional validation: check if it looks like a date range
                    if any(char.isdigit() for char in text_clean) or any(word in text_lower for word in ["present", "current", "now", "today"]):
                        date_candidates.append(text_clean)

        # Look for specific date elements with t-14 class (common for dates)
        t14_elements = soup.find_all(class_='t-14')
        for element in t14_elements:
            text = element.get_text().strip()
            if text and len(text) > 2:
                text_lower = text.lower()
                # Check if this looks like a date (contains numbers or date keywords)
                if any(char.isdigit() for char in text) or any(word in text_lower for word in ["present", "current", "now", "today", "month", "year", "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]):
                    # Avoid duplicates
                    if text not in date_candidates:
                        date_candidates.append(text)

        # Look for elements with t-normal class (also common for dates)
        t_normal_elements = soup.find_all(class_='t-normal')
        for element in t_normal_elements:
            text = element.get_text().strip()
            if text and len(text) > 2:
                text_lower = text.lower()
                if any(char.isdigit() for char in text) or any(word in text_lower for word in ["present", "current", "now", "today", "month", "year", "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]):
                    if text not in date_candidates:
                        date_candidates.append(text)

        # Look for elements with t-black--light class (often used for dates)
        t_black_light_elements = soup.find_all(class_='t-black--light')
        for element in t_black_light_elements:
            text = element.get_text().strip()
            if text and len(text) > 2:
                text_lower = text.lower()
                if any(char.isdigit() for char in text) or any(word in text_lower for word in ["present", "current", "now", "today", "month", "year", "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]):
                    if text not in date_candidates:
                        date_candidates.append(text)

        # Process date candidates - prioritize by relevance
        for candidate in date_candidates:
            candidate_lower = candidate.lower()

            # Check if it's a current position indicator
            if any(word in candidate_lower for word in ["present", "current", "now", "today"]):
                position_info["date_range"] = candidate
                position_info["is_current"] = True
                logger.debug(f"Found current position date: {candidate}")
                break
            # Check if it contains date patterns
            elif any(word in candidate_lower for word in ["month", "year", "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]) or any(char.isdigit() for char in candidate):
                # Additional validation: should not be the same as job title
                if candidate != position_info["job_title"]:
                    position_info["date_range"] = candidate
                    logger.debug(f"Found date range: {candidate}")
                    break

        # If we still don't have a date range, try to infer if it's current
        if not position_info["date_range"] and position_info["job_title"]:
            # Check if the item itself suggests it's current
            item_text = soup.get_text().lower()
            if "present" in item_text or "current" in item_text:
                position_info["is_current"] = True
                logger.debug("Inferred current position from item text")

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
        # Navigate to profile
        logger.info(f"Navigating to profile: {profile_url}")
        driver.get(profile_url)

        # Wait for page to load
        if not wait_for_page_load(driver):
            logger.error("Failed to wait for page load")
            return []

        logger.debug("Page loaded successfully, looking for experience section...")

        # Find experience sections
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
                # ".pvs-list__item",
                # ".pv-entity__position-group-pager",
                # ".pv-profile-section__list-item",
                # ".pvs-list__item--line-separated",
                # ".pvs-entity",
                ".artdeco-list__item",
                "li",
                # ".pvs-list__item--with-top-padding"
            ]

            experience_items = []
            for selector in item_selectors:
                try:
                    items = section.find_elements(By.CSS_SELECTOR, selector)
                    if items:
                        experience_items = items
                        logger.info(f"Found {len(items)} experience items with selector: {selector}")
                        break
                except Exception as e:
                    continue

            if not experience_items:
                logger.warning(f"No experience items found in section {section_idx + 1}")
                continue

            # Process each experience item
            for item_idx, item in enumerate(experience_items):
                try:
                    position_info = extract_position_info(item)

                    logger.info(f"Item {item_idx + 1}:")
                    logger.info(f"  Title: {position_info['job_title']}")
                    logger.info(f"  Company: {position_info['company']}")
                    logger.info(f"  Date: {position_info['date_range']}")
                    logger.info(f"  Current: {position_info['is_current']}")

                    # Only add if we found meaningful information and it's current
                    if position_info['is_current'] and (position_info['job_title'] or position_info['company']):
                        current_positions.append(position_info)
                        logger.info(f"  -> Added to current positions")

                except Exception as e:
                    logger.error(f"Error processing item {item_idx + 1}: {e}")
                    continue

        logger.info(f"Total current positions found: {len(current_positions)}")
        return current_positions

    except TimeoutException:
        logger.error("Timeout waiting for page to load")
        return []

    except Exception as e:
        logger.error(f"Error in get_current_employer: {e}")
        return []
