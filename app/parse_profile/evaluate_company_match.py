import re
from fuzzywuzzy import fuzz


def normalize_company_name(company_name):
    """
    Normalize company name for better matching
    """
    if not company_name:
        return ""

    # Convert to lowercase
    normalized = company_name.lower()

    # Remove common suffixes and prefixes
    suffixes_to_remove = [
        'inc', 'inc.', 'incorporated', 'corp', 'corp.', 'corporation',
        'ltd', 'ltd.', 'limited', 'llc', 'l.l.c.', 'co', 'co.', 'company',
        'gmbh', 'ag', 'sa', 'spa', 'bv', 'nv', 'ab', 'as', 'oy', 'se',
        'plc', 'p.l.c.', 'pty', 'pvt', 'private', 'public'
    ]

    # Remove suffixes
    words = normalized.split()
    filtered_words = []
    for word in words:
        # Remove punctuation from word
        clean_word = re.sub(r'[^\w\s]', '', word)
        if clean_word not in suffixes_to_remove:
            filtered_words.append(clean_word)

    # Join words back
    normalized = ' '.join(filtered_words)

    # Remove extra whitespace and special characters
    normalized = re.sub(r'[^\w\s]', ' ', normalized)
    normalized = re.sub(r'\s+', ' ', normalized).strip()

    return normalized


def fuzzy_match_company(target_company, discovered_company, threshold=75):
    """
    Compare two company names using fuzzy matching

    Args:
        target_company (str): The company name we're looking for
        discovered_company (str): The company name found on LinkedIn
        threshold (int): Minimum similarity score (0-100) to consider a match

    Returns:
        dict: Match result with score and normalized names
    """
    if not target_company or not discovered_company:
        return {
            'is_match': False,
            'score': 0,
            'target_normalized': '',
            'discovered_normalized': '',
            'match_type': 'empty_input'
        }

    # Normalize both company names
    target_norm = normalize_company_name(target_company)
    discovered_norm = normalize_company_name(discovered_company)

    # Calculate different types of similarity scores
    ratio_score = fuzz.ratio(target_norm, discovered_norm)
    partial_ratio_score = fuzz.partial_ratio(target_norm, discovered_norm)
    token_sort_score = fuzz.token_sort_ratio(target_norm, discovered_norm)
    token_set_score = fuzz.token_set_ratio(target_norm, discovered_norm)

    # Use the highest score
    max_score = max(ratio_score, partial_ratio_score, token_sort_score, token_set_score)

    # Determine match type
    match_type = 'no_match'
    if max_score >= threshold:
        if ratio_score == max_score:
            match_type = 'exact_fuzzy'
        elif partial_ratio_score == max_score:
            match_type = 'partial_match'
        elif token_sort_score == max_score:
            match_type = 'token_sort_match'
        elif token_set_score == max_score:
            match_type = 'token_set_match'

    return {
        'is_match': max_score >= threshold,
        'score': max_score,
        'target_normalized': target_norm,
        'discovered_normalized': discovered_norm,
        'match_type': match_type,
        'scores': {
            'ratio': ratio_score,
            'partial_ratio': partial_ratio_score,
            'token_sort': token_sort_score,
            'token_set': token_set_score
        }
    }


def check_company_match(target_company, current_positions, threshold=75):
    """
    Check if any of the current positions match the target company

    Args:
        target_company (str): Company name to search for
        current_positions (list): List of current position dictionaries
        threshold (int): Minimum similarity score for a match

    Returns:
        dict: Best match information
    """
    if not current_positions:
        return {
            'has_match': False,
            'best_match': None,
            'all_matches': []
        }

    all_matches = []
    best_match = None
    best_score = 0

    for position in current_positions:
        if position.get('company'):
            match_result = fuzzy_match_company(
                target_company,
                position['company'],
                threshold
            )

            if match_result['is_match']:
                match_info = {
                    'position': position,
                    'match_result': match_result
                }
                all_matches.append(match_info)

                if match_result['score'] > best_score:
                    best_score = match_result['score']
                    best_match = match_info

    return {
        'has_match': len(all_matches) > 0,
        'best_match': best_match,
        'all_matches': all_matches
    }

