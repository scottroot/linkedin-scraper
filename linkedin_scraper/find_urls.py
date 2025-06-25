from googlesearch import search
from typing import List

def get_linkedin_url_candidates(name, company, limit=5) -> List[str]:
    """
    Search for LinkedIn profile URLs for a given name and company

    Args:
        name (str): Person's name
        company (str): Company name
        limit (int): Maximum number of results to return

    Returns:
        list: List of LinkedIn profile URLs
    """
    try:
        results = search(
            f'site:linkedin.com/in "{name}" "{company}"',
            num_results=limit
        )
        return list(results)
    except Exception as e:
        print(f"Error searching for LinkedIn URLs: {e}")
        return []
