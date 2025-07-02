import sys
sys.path.append("/Users/scomax/Documents/Git/linkedin-scraper/")

from app.driver_and_login import get_driver, cleanup_driver
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from app.logger import get_logger
import base64
import time
from urllib.parse import urlparse, parse_qs, unquote
from difflib import SequenceMatcher


class BingSearch:
    def __init__(self, driver=None, timeout=20):
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
            # Parse the Bing URL to extract the real URL
            parsed = urlparse(bing_url)

            if 'bing.com' in parsed.netloc and ('/ck/' in parsed.path or 'u=' in parsed.query):
                query_params = parse_qs(parsed.query)

                for param_name in ['u', 'url', 'r', 'redirect']:
                    if param_name in query_params:
                        encoded_url = query_params[param_name][0]
                        try:
                            decoded_url = unquote(encoded_url)
                            if decoded_url.startswith("a1"):
                                decoded_url = decoded_url[2:] + "=="
                            if decoded_url.startswith('aHR0c') or len(decoded_url) > 50:
                                return base64.b64decode(decoded_url).decode('utf-8')

                            # Check if the URL decoded version is valid
                            # if 'linkedin.com/in/' in decoded_url:
                            return decoded_url
                            # else:
                            #     self.logger.debug(f"Skipping non-LinkedIn URL from URL decode: {decoded_url}")

                        except Exception as e:
                            self.logger.warning(f"Error decoding URL from parameter '{param_name}': {e}")
                            return ""

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

                    if 'linkedin.com/in/' in final_url:
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
            # Ensure name and company are strings
            if not isinstance(name, str):
                name = str(name) if name is not None else ""
            if not company or not isinstance(company, str):
                self.logger.warning(f"Missing company for {name}")
                return []

            # Store original name for comparison
            original_name = name

            site = "site%3Alinkedin.com%2Fin"
            # name = '"' + name.replace(" ", "%20") + '"'
            name = f'"{name.replace(" ", "%20")}"'
            company = f'"{company.replace(" ", "%20")}"'
            params = "&".join([
                "qs=n",  # Query suggestion behavior. n means no suggestions.
                "form=QBRE",  # Form type. QBRE means it was entered directly into the Bing search bar.
                "sp=-1",  # Controls spelling corrections. -1 means Bing should decide automatically.
                "ghc=1",  # Enables grouping of related results (grouped hit count).
                "lq=0",  # Local query flag; 0 usually means no local context used.
                "sk=",  # Search keywords. Empty here, possibly reserved.
                "ajf=100"  # Possibly related to autocomplete or justification features.
            ])
            query = f"{site}%20{name}%20{company}"

            url = "https://www.bing.com/search?" + params + "&q=" + query + "&pq=" + query.lower()

            self.logger.info(f"Searching Bing for: {name} at {company}")
            self.logger.info(f"Search URL: {url}")
            self.bing_driver.get(url)

            WebDriverWait(self.bing_driver, self.timeout).until(
                EC.presence_of_element_located((By.ID, "b_results"))
            )

            result_container = self.bing_driver.find_element(By.ID, "b_results")
            self.logger.info("Search results container found")

            self.logger.info("Waiting for individual result items to load...")
            WebDriverWait(self.bing_driver, self.timeout * 2).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.b_algo"))
            )

            result_items = result_container.find_elements(By.CSS_SELECTOR, "li.b_algo")
            self.logger.info(f"Found {len(result_items)} result items with CSS selector 'li.b_algo'")

            WebDriverWait(self.bing_driver, self.timeout).until(
                EC.presence_of_all_elements_located((By.TAG_NAME, "h2"))
            )

            self.logger.info(f"Found {len(result_items)} search results")

            validated_results = []
            for i, item in enumerate(result_items):
                if len(validated_results) >= limit:
                    break
                try:
                    self.logger.info(f"Processing result item {i+1}/{len(result_items)}")

                    html = item.get_attribute("outerHTML")
                    soup = BeautifulSoup(html, 'html.parser')
                    h2 = soup.find("h2")

                    title = ""
                    if h2 and h2.text.strip():
                        title = h2.text.strip()
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
                    self.logger.info(f"Item {i+1} - Title: '{title}'")

                    link = ""
                    a = h2.find("a")
                    if a and a.has_attr("href"):
                        link = a["href"]
                        self.logger.info(f"Item {i+1} - Raw URL: {link}")
                    else:
                        self.logger.warning(f"Item {i+1} - No href attribute found in anchor tag")
                        if a:
                            self.logger.debug(f"Item {i+1} - Anchor tag attributes: {a.attrs}")

                    if link:
                        self.logger.info(f"Item {i+1} - Processing link: {link}")

                        # Handle Bing redirect URLs
                        if "bing.com" in link and ("/ck/" in link or "u=" in link):
                            # This is a Bing redirect, extract the real URL
                            real_url = self.extract_real_url_from_bing_redirect(link)
                            self.logger.debug(f"Found URL: {real_url}")
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
                            else:
                                self.logger.debug(f"Bing: Skipping non-LinkedIn redirect result: {real_url}")
                        elif "linkedin.com/in/" in link:
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
                                    validated_results.append((link, title, similarity))
                                    self.logger.debug(f"Bing: Valid match found - {title} (similarity: {similarity:.2f})")
                                else:
                                    self.logger.debug(f"Bing: Skipping low similarity match - {title} (similarity: {similarity:.2f})")
                            else:
                                # Title is empty, extract name from LinkedIn URL for validation
                                url_parts = link.split('/')
                                if len(url_parts) >= 5:
                                    profile_name = url_parts[4].replace('-', ' ').replace('_', ' ')
                                    similarity = SequenceMatcher(None, original_name.lower(), profile_name.lower()).ratio()
                                    self.logger.debug(f"Comparing '{original_name}' with '{profile_name}' from URL (similarity: {similarity:.2f})")

                                    if similarity >= threshold:
                                        validated_results.append((link, profile_name, similarity))
                                        self.logger.debug(f"Bing: Valid match found (from URL) - {profile_name} (similarity: {similarity:.2f})")
                                    else:
                                        self.logger.debug(f"Bing: Skipping low similarity match (from URL) - {profile_name} (similarity: {similarity:.2f})")
                                else:
                                    # If we can't extract name from URL, include with lower confidence
                                    validated_results.append((link, "Unknown", 0.5))
                                    self.logger.debug(f"Bing: Including URL with unknown name: {link}")
                        else:
                            self.logger.debug(f"Bing: Skipping non-LinkedIn URL: {link}")
                    else:
                        self.logger.debug("Bing: Skipping result with no link")
                except Exception as e:
                    self.logger.warning(f"Error processing search result item: {e}")
                    continue  # skip malformed items

            self.logger.info(f"Bing search processed {len(result_items)} results, found {len(validated_results)} valid LinkedIn URLs")

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


if __name__ == "__main__":
    bing_search = BingSearch()

    results = bing_search.run_bing_search("Steve Polenske", "Smart and Final Stores")
    print(results)