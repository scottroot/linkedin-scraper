# import sys
# from pathlib import Path
# sys.path.append(str(Path(__file__).parent.parent.parent))

from app.driver_and_login import get_driver, cleanup_driver
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from app.logger import get_logger
from app.matching import score_fuzzy_match
import base64
import time
from urllib.parse import urlparse, parse_qs, unquote


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

                            # Ensure proper base64 padding
                            if decoded_url.startswith('aHR0c') or len(decoded_url) > 50:
                                # Add padding if needed
                                padding_needed = len(decoded_url) % 4
                                if padding_needed:
                                    decoded_url += '=' * (4 - padding_needed)
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

    def run_bing_search(self, name, company, limit=5, threshold=0.6, quoted_query=True):
        try:
            # Ensure name and company are strings
            if not isinstance(name, str):
                name = str(name) if name is not None else ""
            if not company or not isinstance(company, str):
                self.logger.warning(f"Missing company for {name}")
                return []

            # Store original name and company for comparison and potential retry
            original_name = name
            original_company = company

            site = "site%3Alinkedin.com%2Fin"
            # name = '"' + name.replace(" ", "%20") + '"'
            quoted_name = f'"{name.replace(" ", "%20")}"'
            quoted_company = f'"{company.replace(" ", "%20")}"'

            if quoted_query:
                name = quoted_name
                company = quoted_company
                self.logger.info(f"""Searching Bing for contact with quotes around name and company: "{original_name}" "{original_company}" """)
                pq = ""
            else:
                name = name.replace(" ", "%20")
                company = company.replace(" ", "%20")
                self.logger.info(f"""Searching Bing for contact with no quotes - site:linkedin.com/in {original_name} {original_company}""")
                pq = f"{site}%20{quoted_name}%20{quoted_company}".lower()

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

            url = "https://www.bing.com/search?" + params + "&q=" + query + "&pq=" + pq

            self.logger.info(f"Raw Bing Search URL: {url}")
            self.bing_driver.get(url)

            WebDriverWait(self.bing_driver, self.timeout).until(
                EC.presence_of_element_located((By.ID, "b_results"))
            )

            result_container = self.bing_driver.find_element(By.ID, "b_results")
            self.logger.debug("Search results container found")

            self.logger.debug("Waiting for individual result items to load...")
            WebDriverWait(self.bing_driver, self.timeout * 2).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.b_algo"))
            )

            result_items = result_container.find_elements(By.CSS_SELECTOR, "li.b_algo")
            self.logger.debug(f"Found {len(result_items)} result items with CSS selector 'li.b_algo'")

            WebDriverWait(self.bing_driver, self.timeout).until(
                EC.presence_of_all_elements_located((By.TAG_NAME, "h2"))
            )

            self.logger.info(f"Found {len(result_items)} search results")

            validated_results = []
            for i, item in enumerate(result_items):
                if len(validated_results) >= limit:
                    break
                try:
                    self.logger.debug(f"Processing result item {i+1}/{len(result_items)}")

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
                    else:
                        self.logger.debug(f"Bing: Item {i+1} - No h2 tag or empty title found")
                        # Log the HTML structure to understand what we're dealing with
                        self.logger.debug(f"Bing: Item {i+1} - HTML structure: {html[:200]}...")
                        continue
                    self.logger.info(f"Bing: Item {i+1} - Title: '{title}'")

                    link = ""
                    a = h2.find("a")
                    if a and a.has_attr("href"):
                        link = a["href"]
                        self.logger.debug(f"Bing: Item {i+1} - Raw URL: {link}")
                    else:
                        self.logger.warning(f"Bing: Item {i+1} - No href attribute found in anchor tag")
                        if a:
                            self.logger.debug(f"Bing: Item {i+1} - Anchor tag attributes: {a.attrs}")

                    if link:
                        self.logger.debug(f"Bing: Item {i+1} - Processing link: {link}")

                        # Handle Bing redirect URLs
                        if "bing.com" in link and ("/ck/" in link or "u=" in link):
                            real_url = self.extract_real_url_from_bing_redirect(link)
                            self.logger.info(f"Bing: Item {i+1} - URL: {real_url}")
                            if real_url and "linkedin.com/in/" in real_url:
                                if title and title.strip():
                                    # Clean title for comparison - remove location info
                                    clean_title = title
                                    # Remove location patterns like " - City, State, Country"
                                    if " - " in clean_title:
                                        clean_title = clean_title.split(" - ")[0].strip()

                                    # Use your custom fuzzy matching function
                                    match_result = score_fuzzy_match(original_name, clean_title, "person", threshold * 100)
                                    similarity = match_result['score'] / 100  # Convert to 0-1 scale for consistency
                                    self.logger.info(f"Bing: Item {i+1} - Comparing '{original_name}' with '{clean_title}' (similarity: {similarity:.2f})")

                                    if match_result['is_match']:
                                        validated_results.append((real_url, title, similarity))
                                        self.logger.info(f"Bing: Item {i+1} - Valid LinkedIn match found - {title} (similarity: {similarity:.2f})")
                                    else:
                                        self.logger.debug(f"Bing: Item {i+1} - Skipping low similarity match - {title} (similarity: {similarity:.2f})")
                                        self.logger.debug(f"Bing: Item {i+1} - URL was: {real_url}")
                                else:
                                    # Title is empty, extract name from LinkedIn URL for validation
                                    url_parts = real_url.split('/')
                                    if len(url_parts) >= 5:
                                        profile_name = url_parts[4].replace('-', ' ').replace('_', ' ')
                                        # Use your custom fuzzy matching function
                                        match_result = score_fuzzy_match(original_name, profile_name, "person", threshold * 100)
                                        similarity = match_result['score'] / 100  # Convert to 0-1 scale for consistency
                                        self.logger.debug(f"Bing: Item {i+1} - Comparing '{original_name}' with '{profile_name}' from URL (similarity: {similarity:.2f})")

                                        if match_result['is_match']:
                                            validated_results.append((real_url, profile_name, similarity))
                                            self.logger.info(f"Bing: Item {i+1} - Valid LinkedIn match found (from URL) - {profile_name} (similarity: {similarity:.2f})")
                                        else:
                                            self.logger.debug(f"Bing: Item {i+1} - Skipping low similarity match (from URL) - {profile_name} (similarity: {similarity:.2f})")
                                    else:
                                        # If we can't extract name from URL, include with lower confidence
                                        validated_results.append((real_url, "Unknown", 0.5))
                                        self.logger.info(f"Bing: Item {i+1} - Including LinkedIn URL with unknown name: {real_url}")
                            else:
                                self.logger.debug(f"Bing: Item {i+1} - Skipping non-LinkedIn redirect result: {real_url}")
                                self.logger.debug(f"Bing: Item {i+1} - Title was: '{title}'")
                        elif "linkedin.com/in/" in link:
                            # Direct LinkedIn URL
                            self.logger.info(f"Bing: Item {i+1} - URL: {link}")
                            # Validate the title against the name
                            if title and title.strip():
                                # Clean title for comparison - remove location info
                                clean_title = title
                                # Remove location patterns like " - City, State, Country"
                                if " - " in clean_title:
                                    clean_title = clean_title.split(" - ")[0].strip()

                                # Use your custom fuzzy matching function
                                match_result = score_fuzzy_match(original_name, clean_title, "person", threshold * 100)
                                similarity = match_result['score'] / 100  # Convert to 0-1 scale for consistency
                                self.logger.debug(f"Bing: Item {i+1} - Comparing '{original_name}' with '{clean_title}' (similarity: {similarity:.2f})")

                                if match_result['is_match']:
                                    validated_results.append((link, title, similarity))
                                    self.logger.info(f"Bing: Item {i+1} - Valid LinkedIn match found - {title} (similarity: {similarity:.2f})")
                                else:
                                    self.logger.debug(f"Bing: Item {i+1} - Skipping low similarity match - {title} (similarity: {similarity:.2f})")
                                    self.logger.debug(f"Bing: Item {i+1} - URL was: {link}")
                            else:
                                # Title is empty, extract name from LinkedIn URL for validation
                                url_parts = link.split('/')
                                if len(url_parts) >= 5:
                                    profile_name = url_parts[4].replace('-', ' ').replace('_', ' ')
                                    # Use your custom fuzzy matching function
                                    match_result = score_fuzzy_match(original_name, profile_name, "person", threshold * 100)
                                    similarity = match_result['score'] / 100  # Convert to 0-1 scale for consistency
                                    self.logger.debug(f"Bing: Item {i+1} - Comparing '{original_name}' with '{profile_name}' from URL (similarity: {similarity:.2f})")

                                    if match_result['is_match']:
                                        validated_results.append((link, profile_name, similarity))
                                        self.logger.info(f"Bing: Item {i+1} - Valid LinkedIn match found (from URL) - {profile_name} (similarity: {similarity:.2f})")
                                    else:
                                        self.logger.debug(f"Bing: Item {i+1} - Skipping low similarity match (from URL) - {profile_name} (similarity: {similarity:.2f})")
                                else:
                                    # If we can't extract name from URL, include with lower confidence
                                    validated_results.append((link, "Unknown", 0.5))
                                    self.logger.info(f"Bing: Item {i+1} - Including LinkedIn URL with unknown name: {link}")
                        else:
                            self.logger.debug(f"Bing: Item {i+1} - Skipping non-LinkedIn URL: {link}")
                            self.logger.debug(f"Bing: Item {i+1} - Title was: '{title}'")
                    else:
                        self.logger.debug(f"Bing: Item {i+1} - Skipping result with no link")
                except Exception as e:
                    self.logger.warning(f"Bing: Item {i+1} - Error processing search result item: {e}")
                    continue  # skip malformed items

            self.logger.info(f"Bing search processed {len(result_items)} results, found {len(validated_results)} valid LinkedIn URLs")

            # Sort by similarity score (highest first)
            # validated_results.sort(key=lambda x: x[2], reverse=True)

            # Extract just the URLs for backward compatibility
            links = [result[0] for result in validated_results]

            for l in links:
                self.logger.debug(f"\t- {l}")

            # If no results found and this was a quoted query, retry without quotes
            if not links and quoted_query:
                self.logger.info("No results found with quoted query, retrying without quotes...")
                return self.run_bing_search(original_name, original_company, limit, threshold, quoted_query=False)

            return links
        except Exception as e:
            self.logger.error(f"Error running Bing search: {e}")
            cleanup_driver(self.bing_driver)
            raise e

    def cleanup(self):
        cleanup_driver(self.bing_driver)


if __name__ == "__main__":
    bing_search = BingSearch()

    results = bing_search.run_bing_search("Magaly Romero", "Smart and Final Stores")
    print(results)
