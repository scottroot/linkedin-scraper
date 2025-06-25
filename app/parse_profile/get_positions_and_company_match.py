from typing import Any, Dict, Literal
from app.parse_profile.evaluate_company_match import check_company_match
from app.parse_profile.extract_experience import get_current_employer


def get_positions_and_company_match(
    driver,
    profile_url,
    target_company,
    threshold=75,
    verbose=False
) -> Dict[Literal['current_positions', 'company_match'], Any]:
    """
    Extract current employer from LinkedIn profile URL and check for company match using existing driver.
    Returns a dictionary with the following keys:
        {
            'current_positions': list[dict],
            'company_match': {
                'has_match': bool,
                'best_match': dict,
                'all_matches': list
            }
        }
    """
    current_positions = get_current_employer(driver, profile_url, verbose=verbose)

    if not current_positions:
        return {
            'current_positions': [],
            'company_match': {
                'has_match': False,
                'best_match': None,
                'all_matches': []
            }
        }

    # Check for company matches
    match_result = check_company_match(target_company, current_positions, threshold)

    return {
        'current_positions': current_positions,
        'company_match': match_result
    }
