from googlesearch import search
from typing import List, Tuple
from app.logger import get_logger
import time
import random
from difflib import SequenceMatcher


class GoogleSearch:
    def __init__(self):
        self.logger = get_logger()
        self.last_request_time = 0
        self.min_delay_between_requests = 3  # Minimum 3 seconds between requests

    def run_google_search(self, name: str, company: str, limit: int = 5, threshold: float = 0.6, max_retries: int = 3) -> List[Tuple[str, str, float]]:
        """
        Search Google for LinkedIn profiles with fuzzy validation

        Args:
            name (str): Person's name
            company (str): Company name
            limit (int): Maximum number of results to return
            threshold (float): Minimum fuzzy match threshold
            max_retries (int): Maximum number of retries for rate limit errors

        Returns:
            List[Tuple[str, str, float]]: List of (url, title, similarity_score) tuples
        """
        for attempt in range(max_retries):
            try:
                # Rate limiting - ensure minimum delay between requests
                current_time = time.time()
                time_since_last_request = current_time - self.last_request_time
                if time_since_last_request < self.min_delay_between_requests:
                    sleep_time = self.min_delay_between_requests - time_since_last_request
                    self.logger.info(f"Rate limiting: waiting {sleep_time:.1f} seconds before Google search")
                    time.sleep(sleep_time)

                self.logger.info(f"Starting Google search for '{name}' at '{company}' (attempt {attempt + 1}/{max_retries})")

                # Perform Google search
                search_query = f'site:linkedin.com/in "{name}" "{company}"'
                results = search(search_query, num_results=limit)

                # Update last request time
                self.last_request_time = time.time()

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
                error_msg = str(e)
                self.logger.error(f"Error in Google search (attempt {attempt + 1}/{max_retries}): {e}")

                # Check if it's a rate limit error
                if "429" in error_msg or "Too Many Requests" in error_msg:
                    if attempt < max_retries - 1:
                        # Exponential backoff: wait longer for each retry
                        wait_time = (2 ** attempt) + random.uniform(2, 5)
                        self.logger.info(f"Rate limit detected. Waiting {wait_time:.1f} seconds before retry...")
                        time.sleep(wait_time)
                        continue
                    else:
                        self.logger.warning("Max retries reached for Google search due to rate limiting")
                        return []
                else:
                    # For non-rate-limit errors, don't retry
                    self.logger.error(f"Non-retryable error in Google search: {e}")
                    return []

        return []
