import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from typing import Any, Dict, Literal
from app.matching import analyze_positions_for_company_match
from app.parse_profile.scrape_experience import get_all_positions


def scrape_positions_and_match_company(
    driver,
    profile_url,
    target_company,
    threshold=75,
    verbose=False,
    timeout=15
) -> Dict[Literal['all_positions', 'company_match'], Any]:
    """
    Extract current and all positions from LinkedIn profile URL and check for comprehensive company match.
    Returns a dictionary with the following keys:
        {
            'all_positions': list[dict],
            'company_match':
                'has_current_match': bool,
                'has_any_match': bool,
                'any_match': dict,  # Best matching position info (keeping name for compatibility)
            }
        }
    """
    # Get both current and all positions in a single pass
    all_positions = get_all_positions(driver, profile_url, verbose=verbose, timeout=timeout)

    # if not current_positions and not all_positions:
    if not all_positions or len(all_positions) == 0 or not all_positions[0].get("company"):
        print(f"get_positions_and_company_match: No positions found for {profile_url}")
        return {
            'all_positions': [],
            'company_match': {
                'has_current_match': False,
                'has_any_match': False,
                'any_match': None
            }
        }

    # Check for comprehensive company matches
    match_result = analyze_positions_for_company_match(
        target_company,
        all_positions,
        threshold
    )

    return {
        'all_positions': all_positions,
        'company_match': match_result
    }
