from app.find_profile_urls.google_search import GoogleSearch
from app.find_profile_urls.bing_search import BingSearch
from app.find_profile_urls.brave_search import BraveSearch
from app.logger import get_logger
from typing import List

from app.parse_profile.evaluate_company_match import normalize_company_name


def get_linkedin_url_candidates(name, company, driver=None, limit=5, threshold=0.6) -> List[str]:
    """
    Search for LinkedIn profile URLs for a given name and company
    First tries Google search, then falls back to Bing search if needed

    Args:
        name (str): Person's name
        company (str): Company name
        driver: (optional) Selenium driver (for Bing fallback)
        limit (int): Maximum number of results to return
        threshold (float): Minimum fuzzy match threshold (0.0 to 1.0)

    Returns:
        list: List of LinkedIn profile URLs
    """
    logger = get_logger()
    try:
        # logger.info(f"Starting LinkedIn URL search for '{name}' at '{company}' with threshold {threshold}")

        # # First, try Google search
        # google_search = GoogleSearch()
        # google_results = google_search.run_google_search(name, company, limit=limit, threshold=threshold)

        # if google_results:
        #     # Extract URLs from Google results
        #     urls = [result[0] for result in google_results]
        #     logger.info(f"Google search successful. Found {len(urls)} validated URLs")
        #     return urls

        # # If Google search fails or returns no results, fall back to Bing
        # logger.debug("Google search failed or returned no results. Falling back to Bing search...")

        clean_company = normalize_company_name(company)
        bing_search = BingSearch(driver)
        links = bing_search.run_bing_search(name, clean_company, limit=limit, threshold=threshold)
        # bing_search.cleanup()
        logger.info(f"Bing search completed. Found {len(links)} URLs")

        if links:
            return links

        # If both Google and Bing fail, try Brave search
        logger.info("Both Google and Bing searches failed. Trying Brave search...")
        brave_search_instance = BraveSearch()
        brave_results = brave_search_instance.run_brave_search(name, clean_company, limit=limit, threshold=threshold)

        if brave_results:
            # Extract URLs from Brave results
            urls = [result[0] for result in brave_results]
            logger.info(f"Brave search successful. Found {len(urls)} validated URLs")
            return urls

        logger.warning(f"No LinkedIn URLs found for '{name}' at '{company}'")
        return []

    except Exception as e:
        logger.error(f"Error searching for LinkedIn URLs: {e}")
        return []
