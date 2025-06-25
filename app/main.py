from app.find_urls import get_linkedin_url_candidates
from app.check_company import (
    fuzzy_match_company,
    get_current_employer_with_matching
)


def is_employed_at_company(name, company, threshold=75, max_profiles=3, verbose=False):
    """
    Main function: Check if a person is currently employed at a specific company

    Args:
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
            # Get current positions with company matching
            result = get_current_employer_with_matching(
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


# if __name__ == "__main__":

#     target_company = "GK Software SE"
#     target_name = "Abril M Tenorio"


#     is_employed = is_employed_at_company(target_name, target_company)

#     print(is_employed)