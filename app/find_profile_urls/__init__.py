from dotenv import load_dotenv
load_dotenv()

from app.parse_profile.get_positions_and_company_match import scrape_positions_and_match_company
from app.matching import normalize_company_name
from .brave_search import BraveSearch
from .bing_search import BingSearch


def validate_search_results(
    url_candidates,
    full_name,
    company_name,
    linkedin_driver,
    search_count,
    idx,
    log,
    linkedin_threshold,
    linkedin_timeout,
    early_exit_threshold,
    search_source="Unknown"
):
    """
    Validate a list of profile candidates and return the best match and profile URL.
    """
    best_match = None
    best_score = 0
    best_profile_url = None
    found_good_match = False

    for i, profile_url in enumerate(url_candidates):
        try:
            log(f"Search #{search_count} (Row {idx+1}): Checking {search_source} candidate {i+1}/{len(url_candidates)}: {profile_url}")

            # Check employment status using the shared driver
            positions_and_company_match = scrape_positions_and_match_company(
                driver=linkedin_driver,
                profile_url=profile_url,
                target_company=company_name,
                threshold=linkedin_threshold,
                verbose=False,
                timeout=linkedin_timeout
            )

            # Check if this profile has a company match (current or historical)
            company_match = positions_and_company_match['company_match']

            if company_match['has_any_match']:
                # Get the best match score from this profile
                best_match_info = company_match['any_match']
                current_best_score = best_match_info['match_result']['score']

                # Log the type of match found
                match_type = "current position" if company_match['has_current_match'] else "historical position"
                log(f"Search #{search_count} (Row {idx+1}): {search_source} candidate {i+1} has company match in {match_type} with score {current_best_score}")

                # Update best match if this score is higher
                if current_best_score > best_score:
                    best_score = current_best_score
                    best_match = positions_and_company_match
                    best_profile_url = profile_url
                    log(f"Search #{search_count} (Row {idx+1}): New best match found! Score: {best_score}")

                # If we have a very good match (high confidence), stop checking other candidates
                if current_best_score >= early_exit_threshold:
                    log(f"Search #{search_count} (Row {idx+1}): Found excellent match with score {current_best_score} - stopping search")
                    found_good_match = True
                    break
            else:
                log(f"Search #{search_count} (Row {idx+1}): {search_source} candidate {i+1} has no company match in any position")

        except Exception as e:
            log(f"Search #{search_count} (Row {idx+1}): Error checking {search_source} candidate {i+1}: {e}")
            continue

    # Log if we checked all candidates
    if not found_good_match and len(url_candidates) > 1:
        log(f"Search #{search_count} (Row {idx+1}): Checked all {len(url_candidates)} {search_source} candidates")

    # Return both the best match and the profile URL
    return best_match, best_profile_url


def find_profile_urls_and_validate(
    full_name: str,
    company_name: str,
    linkedin_driver,
    bing_driver,
    search_count: int,
    idx: int,
    log,
    max_candidates: int = 3,
    search_threshold: float = 0.6,
    linkedin_threshold: int = 75,
    linkedin_timeout: int = 15,
    bing_timeout: int = 20,
    early_exit_threshold: int = 85
) -> tuple[dict | None, str | None]:
    """
    Search for LinkedIn profiles using Bing first, then Brave if no valid matches found.

    This function performs a two-stage search process:
    1. First attempts to find profiles using Bing search
    2. If Bing fails or returns no valid matches, falls back to Brave search
    3. Validates all candidates against LinkedIn to ensure accuracy

    Args:
        full_name (str): The full name of the person to search for
        company_name (str): The company name to search within
        linkedin_driver: Selenium WebDriver instance for LinkedIn
        bing_driver: Selenium WebDriver instance for Bing
        search_count (int): Current search iteration number for logging
        idx (int): Row index in the source data for logging
        log: Logging function to use for output
        max_candidates (int, optional): Maximum number of search candidates to return. Defaults to 3.
        search_threshold (float, optional): Minimum similarity threshold for search results. Defaults to 0.6.
        linkedin_threshold (int, optional): Minimum LinkedIn validation score. Defaults to 75.
        linkedin_timeout (int, optional): Timeout in seconds for LinkedIn page loads. Defaults to 15.
        bing_timeout (int, optional): Timeout in seconds for Bing searches. Defaults to 20.
        early_exit_threshold (int, optional): Score threshold for early exit on validation. Defaults to 85.

    Returns:
        tuple[dict | None, str | None]: A tuple containing:
            - dict | None: Best matching profile data if found, None otherwise. The dict contains:
                - 'all_positions' (list[dict]): List of all job positions (current + historical)
                - 'company_match' (dict): Company matching results containing:
                    - 'has_current_match' (bool): True if target company matches a current position
                    - 'has_any_match' (bool): True if target company matches any position (current or historical)
                    - 'any_match' (dict): Best match from any position with highest fuzzy score. Contains:
                        - 'position' (dict): Job position data (title, company, dates, etc.)
                        - 'match_result' (dict): Fuzzy matching details (score, match type, normalized names)
            - str | None: LinkedIn profile URL if found, None otherwise
    """
    # Step 1: Try Bing search first
    log(f"Search #{search_count} (Row {idx+1}): Starting Bing search for {full_name} at {company_name}")
    clean_company = normalize_company_name(company_name)
    log(f"Using 'cleaned' company of of: {clean_company}")

    bing_search = BingSearch(bing_driver, timeout=bing_timeout)
    url_candidates = bing_search.run_bing_search(
        name=full_name,
        company=clean_company,
        limit=max_candidates,
        threshold=search_threshold
    )

    if url_candidates:
        log(f"Search #{search_count} (Row {idx+1}): Bing found {len(url_candidates)} results")

        # Validate Bing candidates
        best_match, best_profile_url = validate_search_results(
            url_candidates,
            full_name,
            company_name,
            linkedin_driver,
            search_count,
            idx,
            log,
            linkedin_threshold,
            linkedin_timeout,
            early_exit_threshold,
            search_source="Bing"
        )

        if best_match:
            log(f"Search #{search_count} (Row {idx+1}): Valid match found from Bing search")
            return best_match, best_profile_url
        else:
            log(f"Search #{search_count} (Row {idx+1}): No valid matches from Bing candidates, trying Brave search")
    else:
        log(f"Search #{search_count} (Row {idx+1}): Bing search returned no candidates, trying Brave search")

    # Step 2: Try Brave search if Bing failed or returned no valid matches
    log(f"Search #{search_count} (Row {idx+1}): Starting Brave search for {full_name} at {company_name}")

    clean_company = normalize_company_name(company_name)
    brave_search_instance = BraveSearch()
    brave_results = brave_search_instance.run_brave_search(
        full_name,
        clean_company,
        limit=max_candidates,
        threshold=search_threshold
    )

    if brave_results:
        # Extract URLs from Brave results
        brave_urls = [result[0] for result in brave_results]
        log(f"Search #{search_count} (Row {idx+1}): Brave found {len(brave_urls)} candidates")

        # Validate Brave candidates
        best_match, best_profile_url = validate_search_results(
            brave_urls,
            full_name,
            company_name,
            linkedin_driver,
            search_count,
            idx,
            log,
            linkedin_threshold,
            linkedin_timeout,
            early_exit_threshold,
            search_source="Brave"
        )

        if best_match:
            log(f"Search #{search_count} (Row {idx+1}): Valid match found from Brave search")
            return best_match, best_profile_url
        else:
            log(f"Search #{search_count} (Row {idx+1}): No valid matches from Brave candidates either")
    else:
        log(f"Search #{search_count} (Row {idx+1}): Brave search returned no candidates")

    # No valid matches found from either search
    log(f"Search #{search_count} (Row {idx+1}): No valid matches found from either Bing or Brave search")
    return None, None
