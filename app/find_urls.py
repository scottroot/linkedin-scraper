from googlesearch import search
from typing import List, Tuple
from app.driver_and_login import get_driver, cleanup_driver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from app.logger import get_logger
import re
import base64
import time
from urllib.parse import urlparse, parse_qs, unquote
from difflib import SequenceMatcher


def fuzzy_match(name1: str, name2: str, threshold: float = 0.6) -> bool:
    """
    Perform fuzzy string matching between two names

    Args:
        name1 (str): First name to compare
        name2 (str): Second name to compare
        threshold (float): Minimum similarity ratio (0.0 to 1.0)

    Returns:
        bool: True if names match above threshold
    """
    # Normalize names for comparison
    name1_clean = re.sub(r'[^\w\s]', '', name1.lower().strip())
    name2_clean = re.sub(r'[^\w\s]', '', name2.lower().strip())

    # Calculate similarity ratio
    similarity = SequenceMatcher(None, name1_clean, name2_clean).ratio()

    return similarity >= threshold


class GoogleSearch:
    def __init__(self):
        self.logger = get_logger()

    def run_google_search(self, name: str, company: str, limit: int = 5, threshold: float = 0.6) -> List[Tuple[str, str, float]]:
        """
        Search Google for LinkedIn profiles with fuzzy validation

        Args:
            name (str): Person's name
            company (str): Company name
            limit (int): Maximum number of results to return
            threshold (float): Minimum fuzzy match threshold

        Returns:
            List[Tuple[str, str, float]]: List of (url, title, similarity_score) tuples
        """
        try:
            self.logger.info(f"Starting Google search for '{name}' at '{company}'")

            # Perform Google search
            search_query = f'site:linkedin.com/in "{name}" "{company}"'
            results = search(search_query, num_results=limit)

            validated_results = []
            for url in results:
                if "linkedin.com/in/" in url:
                    # Extract name from LinkedIn URL for validation
                    url_parts = url.split('/')
                    if len(url_parts) >= 5:
                        profile_name = url_parts[4].replace('-', ' ').replace('_', ' ')

                        # Perform fuzzy matching
                        similarity = SequenceMatcher(None, name.lower(), profile_name.lower()).ratio()

                        if similarity >= threshold:
                            validated_results.append((url, profile_name, similarity))
                            self.logger.info(f"Google: Valid match found - {profile_name} (similarity: {similarity:.2f})")
                        else:
                            self.logger.info(f"Google: Skipping low similarity match - {profile_name} (similarity: {similarity:.2f})")
                    else:
                        # If we can't extract name from URL, still include it but with lower confidence
                        validated_results.append((url, "Unknown", 0.5))
                        self.logger.info(f"Google: Including URL with unknown name: {url}")

            self.logger.info(f"Google search completed. Found {len(validated_results)} validated results")
            return validated_results

        except Exception as e:
            self.logger.error(f"Error in Google search: {e}")
            return []


class BingSearch:
    def __init__(self, driver=None, timeout=10):
        self.logger = get_logger()
        self.timeout = timeout
        if driver is None:
            self.bing_driver = get_driver(headless=True)
        else:
            self.bing_driver = driver

    def extract_real_url_from_bing_redirect(self, bing_url):
        """
        Extract the real URL from a Bing redirect URL
        """
        try:
            # self.logger.info(f"Processing Bing redirect URL: {bing_url}")

            # Parse the Bing URL to extract the real URL
            parsed = urlparse(bing_url)
            # self.logger.info(f"Parsed URL - netloc: {parsed.netloc}, path: {parsed.path}")

            if 'bing.com' in parsed.netloc and '/ck/' in parsed.path:
                # This is a Bing redirect URL, extract the real URL
                query_params = parse_qs(parsed.query)

                # Try different parameter names that might contain the real URL
                for param_name in ['u', 'url', 'r', 'redirect']:
                    if param_name in query_params:
                        encoded_url = query_params[param_name][0]
                        # self.logger.info(f"Found encoded URL in parameter '{param_name}': {encoded_url}")

                        # Try to decode it - it might be URL-encoded or base64
                        try:
                            # First try URL decoding
                            decoded_url = unquote(encoded_url).lstrip('a').lstrip('1') + "=="
                            # self.logger.info(f"URL decoded: {decoded_url}")

                            # If it still looks encoded, try base64
                            if decoded_url.startswith('aHR0c') or len(decoded_url) > 50:
                                try:
                                    base64_decoded = base64.b64decode(decoded_url).decode('utf-8')
                                    self.logger.info(f"Base64 decoded: {base64_decoded}")
                                    if 'linkedin.com' in base64_decoded:
                                        return base64_decoded
                                except Exception as e:
                                    self.logger.warning(f"Base64 decode failed: {e}")

                            # Check if the URL decoded version is valid
                            if 'linkedin.com' in decoded_url:
                                return decoded_url

                        except Exception as e:
                            self.logger.warning(f"Error decoding URL from parameter '{param_name}': {e}")

                # If we can't extract it from parameters, try to follow the redirect
                self.logger.info("Attempting to follow redirect...")
                try:
                    # Get the current page URL before following redirect
                    current_url = self.bing_driver.current_url
                    self.logger.info(f"Current URL before redirect: {current_url}")

                    # Navigate to the Bing redirect URL
                    self.bing_driver.get(bing_url)

                    # Wait a moment for redirect
                    time.sleep(2)

                    # Get the final URL after redirect
                    final_url = self.bing_driver.current_url
                    self.logger.info(f"Final URL after redirect: {final_url}")

                    if 'linkedin.com' in final_url:
                        return final_url
                    else:
                        self.logger.warning(f"Redirect did not lead to LinkedIn URL: {final_url}")

                except Exception as e:
                    self.logger.warning(f"Error following redirect: {e}")

            return bing_url
        except Exception as e:
            self.logger.warning(f"Error extracting real URL from Bing redirect: {e}")
            return bing_url

    def run_bing_search(self, name, company, limit=5, threshold=0.6):
        try:
            # Store original name for comparison
            original_name = name

            site = "site%3Alinkedin.com%2Fin%20"
            name = '"' + name.replace(" ", "%20") + '"'
            company = company.replace(" ", "%20")# + '"'
            params = "&".join([
                "qs=n",  # Query suggestion behavior. n means no suggestions.
                "form=QBRE",  # Form type. QBRE means it was entered directly into the Bing search bar.
                "sp=-1",  # Controls spelling corrections. -1 means Bing should decide automatically.
                "ghc=1",  # Enables grouping of related results (grouped hit count).
                "lq=0",  # Local query flag; 0 usually means no local context used.
                "sk=",  # Search keywords. Empty here, possibly reserved.
                "ajf=100"  # Possibly related to autocomplete or justification features.
            ])
            url = "https://www.bing.com/search?" + params + "&q=" + site + "%20" + name + "%20" + company
            self.logger.info(f"Searching Bing for: {name} at {company}")
            self.bing_driver.get(url)

            WebDriverWait(self.bing_driver, self.timeout).until(
                EC.presence_of_element_located((By.ID, "b_results"))
            )

            result_container = self.bing_driver.find_element(By.ID, "b_results")
            result_items = result_container.find_elements(By.CSS_SELECTOR, "li.b_algo")[:limit]

            self.logger.debug(f"Found {len(result_items)} search results")

            validated_results = []
            for item in result_items:
                if len(validated_results) >= limit:
                    break
                try:
                    link = item.find_element(By.CSS_SELECTOR, "h2 a")
                    href = link.get_attribute("href")

                    # Try multiple ways to get the title
                    title = ""
                    try:
                        # First try the link text (this should be the most reliable)
                        title = link.text.strip()

                        if not title:
                            # Try finding the title in the h2 element
                            h2_element = item.find_element(By.CSS_SELECTOR, "h2")
                            title = h2_element.text.strip()

                        if not title:
                            # Try finding the title in the h2 anchor specifically
                            h2_anchor = item.find_element(By.CSS_SELECTOR, "h2 a")
                            title = h2_anchor.text.strip()

                        if not title:
                            # Try finding any text in the result item
                            title = item.text.strip()

                        # Clean up the title - remove common LinkedIn suffixes
                        if title:
                            # Remove common LinkedIn profile suffixes
                            suffixes_to_remove = [
                                " | Professional Profile",
                                " | LinkedIn",
                                " - Professional Profile",
                                " - LinkedIn",
                                " | Business Profile",
                                " - Business Profile"
                            ]
                            for suffix in suffixes_to_remove:
                                if title.endswith(suffix):
                                    title = title[:-len(suffix)].strip()
                                    break

                    except Exception as e:
                        self.logger.debug(f"Error extracting title: {e}")

                    self.logger.debug(f"Raw URL: {href}")
                    self.logger.debug(f"Title: '{title}'")

                    if href:
                        # Handle Bing redirect URLs
                        if "bing.com" in href and ("/ck/" in href or "u=" in href):
                            # This is a Bing redirect, extract the real URL
                            real_url = self.extract_real_url_from_bing_redirect(href)
                            self.logger.debug(f"Extracted real URL from Bing redirect: {real_url}")
                            if real_url and "linkedin.com/in/" in real_url:
                                # Validate the title against the name
                                if title and title.strip():
                                    # Clean title for comparison - remove location info
                                    clean_title = title
                                    # Remove location patterns like " - City, State, Country"
                                    if " - " in clean_title:
                                        clean_title = clean_title.split(" - ")[0].strip()

                                    similarity = SequenceMatcher(None, original_name.lower(), clean_title.lower()).ratio()
                                    self.logger.info(f"Comparing '{original_name}' with '{clean_title}' (similarity: {similarity:.2f})")

                                    if similarity >= threshold:
                                        validated_results.append((real_url, title, similarity))
                                        self.logger.debug(f"Bing: Valid match found - {title} (similarity: {similarity:.2f})")
                                    else:
                                        self.logger.debug(f"Bing: Skipping low similarity match - {title} (similarity: {similarity:.2f})")
                                else:
                                    # Title is empty, extract name from LinkedIn URL for validation
                                    url_parts = real_url.split('/')
                                    if len(url_parts) >= 5:
                                        profile_name = url_parts[4].replace('-', ' ').replace('_', ' ')
                                        similarity = SequenceMatcher(None, original_name.lower(), profile_name.lower()).ratio()
                                        self.logger.debug(f"Comparing '{original_name}' with '{profile_name}' from URL (similarity: {similarity:.2f})")

                                        if similarity >= threshold:
                                            validated_results.append((real_url, profile_name, similarity))
                                            self.logger.debug(f"Bing: Valid match found (from URL) - {profile_name} (similarity: {similarity:.2f})")
                                        else:
                                            self.logger.debug(f"Bing: Skipping low similarity match (from URL) - {profile_name} (similarity: {similarity:.2f})")
                                    else:
                                        # If we can't extract name from URL, include with lower confidence
                                        validated_results.append((real_url, "Unknown", 0.5))
                                        self.logger.debug(f"Bing: Including URL with unknown name: {real_url}")
                        elif "linkedin.com/in/" in href:
                            # Direct LinkedIn URL
                            # Validate the title against the name
                            if title and title.strip():
                                # Clean title for comparison - remove location info
                                clean_title = title
                                # Remove location patterns like " - City, State, Country"
                                if " - " in clean_title:
                                    clean_title = clean_title.split(" - ")[0].strip()

                                similarity = SequenceMatcher(None, original_name.lower(), clean_title.lower()).ratio()
                                self.logger.debug(f"Comparing '{original_name}' with '{clean_title}' (similarity: {similarity:.2f})")

                                if similarity >= threshold:
                                    validated_results.append((href, title, similarity))
                                    self.logger.debug(f"Bing: Valid match found - {title} (similarity: {similarity:.2f})")
                                else:
                                    self.logger.debug(f"Bing: Skipping low similarity match - {title} (similarity: {similarity:.2f})")
                            else:
                                # Title is empty, extract name from LinkedIn URL for validation
                                url_parts = href.split('/')
                                if len(url_parts) >= 5:
                                    profile_name = url_parts[4].replace('-', ' ').replace('_', ' ')
                                    similarity = SequenceMatcher(None, original_name.lower(), profile_name.lower()).ratio()
                                    self.logger.debug(f"Comparing '{original_name}' with '{profile_name}' from URL (similarity: {similarity:.2f})")

                                    if similarity >= threshold:
                                        validated_results.append((href, profile_name, similarity))
                                        self.logger.debug(f"Bing: Valid match found (from URL) - {profile_name} (similarity: {similarity:.2f})")
                                    else:
                                        self.logger.debug(f"Bing: Skipping low similarity match (from URL) - {profile_name} (similarity: {similarity:.2f})")
                                else:
                                    # If we can't extract name from URL, include with lower confidence
                                    validated_results.append((href, "Unknown", 0.5))
                                    self.logger.debug(f"Bing: Including URL with unknown name: {href}")
                        else:
                            self.logger.debug(f"Skipping non-LinkedIn URL: {href}")
                except Exception as e:
                    self.logger.warning(f"Error processing search result item: {e}")
                    continue  # skip malformed items

            # Sort by similarity score (highest first)
            validated_results.sort(key=lambda x: x[2], reverse=True)

            # Extract just the URLs for backward compatibility
            links = [result[0] for result in validated_results]

            for l in links:
                self.logger.debug(f"\t- {l}")
            return links
        except Exception as e:
            self.logger.error(f"Error running Bing search: {e}")
            cleanup_driver(self.bing_driver)
            raise e

    def cleanup(self):
        cleanup_driver(self.bing_driver)


def get_linkedin_url_candidates(name, company, driver, limit=5, threshold=0.6) -> List[str]:
    """
    Search for LinkedIn profile URLs for a given name and company
    First tries Google search, then falls back to Bing search if needed

    Args:
        name (str): Person's name
        company (str): Company name
        driver: Selenium driver (for Bing fallback)
        limit (int): Maximum number of results to return
        threshold (float): Minimum fuzzy match threshold (0.0 to 1.0)

    Returns:
        list: List of LinkedIn profile URLs
    """
    logger = get_logger()
    try:
        logger.info(f"Starting LinkedIn URL search for '{name}' at '{company}' with threshold {threshold}")

        # First, try Google search
        google_search = GoogleSearch()
        google_results = google_search.run_google_search(name, company, limit=limit, threshold=threshold)

        if google_results:
            # Extract URLs from Google results
            urls = [result[0] for result in google_results]
            logger.info(f"Google search successful. Found {len(urls)} validated URLs")
            return urls

        # If Google search fails or returns no results, fall back to Bing
        logger.debug("Google search failed or returned no results. Falling back to Bing search...")
        bing_search = BingSearch(driver)
        links = bing_search.run_bing_search(name, company, limit=limit, threshold=threshold)
        # bing_search.cleanup()
        logger.info(f"Bing search completed. Found {len(links)} URLs")
        return links

    except Exception as e:
        logger.error(f"Error searching for LinkedIn URLs: {e}")
        return []


if __name__ == "__main__":
    name = "Scott Hendrix"
    company = "LCN Services LLC"
    limit = 10

    # Create a driver for testing
    driver = get_driver(headless=True)

    try:
        results = get_linkedin_url_candidates(name, company, driver, limit, threshold=0.6)

        for r in results:
            logger = get_logger()
            logger.info(r)
    finally:
        cleanup_driver(driver)
