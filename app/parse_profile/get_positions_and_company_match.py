from typing import Any, Dict, Literal
from app.parse_profile.evaluate_company_match import check_company_match, check_company_match_comprehensive
from app.parse_profile.extract_experience import get_current_employer, get_positions_comprehensive


def get_positions_and_company_match(
    driver,
    profile_url,
    target_company,
    threshold=75,
    verbose=False,
    timeout=15
) -> Dict[Literal['current_positions', 'all_positions', 'company_match'], Any]:
    """
    Extract current and all positions from LinkedIn profile URL and check for comprehensive company match.
    Returns a dictionary with the following keys:
        {
            'current_positions': list[dict],
            'all_positions': list[dict],
            'company_match': {
                'has_current_match': bool,
                'has_any_match': bool,
                'current_match': dict,
                'any_match': dict,
                'all_matches': list
            }
        }
    """
    # Get both current and all positions in a single pass
    positions_data = get_positions_comprehensive(driver, profile_url, verbose=verbose, timeout=timeout)

    current_positions = positions_data['current_positions']
    all_positions = positions_data['all_positions']

    if not current_positions and not all_positions:
        return {
            'current_positions': [],
            'all_positions': [],
            'company_match': {
                'has_current_match': False,
                'has_any_match': False,
                'current_match': None,
                'any_match': None,
                'all_matches': []
            }
        }

    # Check for comprehensive company matches
    match_result = check_company_match_comprehensive(
        target_company,
        current_positions,
        all_positions,
        threshold
    )

    return {
        'current_positions': current_positions,
        'all_positions': all_positions,
        'company_match': match_result
    }
