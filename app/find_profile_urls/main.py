from app.find_profile_urls.google_search import GoogleSearch
from app.find_profile_urls.bing_search import BingSearch
from app.find_profile_urls.brave_search import BraveSearch
from app.logger import get_logger
from typing import List

from app.parse_profile.evaluate_company_match import normalize_company_name


def get_linkedin_url_candidates(name, company, driver=None, limit=5, threshold=0.6, bing_timeout=20) -> List[str]:
    """
    Search for LinkedIn profile URLs using Bing search only.
    This function is designed to work with the new fallback logic in main.py
    where Brave search is handled separately if Bing returns no valid matches.

    Args:
        name (str): Person's name
        company (str): Company name
        driver: Selenium driver (required for Bing search)
        limit (int): Maximum number of results to return
        threshold (float): Minimum fuzzy match threshold (0.0 to 1.0)
        bing_timeout (int): Timeout for Bing search operations

    Returns:
        list: List of LinkedIn profile URLs
    """
    logger = get_logger()
    try:
        logger.info(f"Starting Bing search for LinkedIn URLs for '{name}' at '{company}' with threshold {threshold}")

        clean_company = normalize_company_name(company)
        bing_search = BingSearch(driver, timeout=bing_timeout)
        links = bing_search.run_bing_search(name, clean_company, limit=limit, threshold=threshold)

        logger.info(f"Bing search completed. Found {len(links)} URLs")
        return links

    except Exception as e:
        logger.error(f"Error in Bing search for LinkedIn URLs: {e}")
        return []
