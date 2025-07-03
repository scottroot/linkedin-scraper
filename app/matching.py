# import sys
# from pathlib import Path
# sys.path.append(str(Path(__file__).parent.parent))

import json
from typing import Any, Dict, List, Literal
import re
import unidecode
from rapidfuzz import fuzz, process
from app.logger import get_logger

def normalize_person_name(name: str) -> str:
    logger = get_logger()
    if not name:
        if name is None:
            logger.warning("Cannot normalize person name: No name arg provided...")
        else:
            logger.warning(f"Cannot normalize person name: name arg provided is empty: '{name}'")
        return ""
    name = unidecode.unidecode(name.lower())
    name = re.sub(r"[.,\-]", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name

def normalize_company_name(company_name: str) -> str:
    logger = get_logger()
    if not company_name:
        if company_name is None:
            logger.warning("Cannot normalize company name: No company_name arg provided...")
        else:
            logger.warning(f"Cannot normalize company name: company_name arg provided is empty: '{company_name}'")
        return ""
    name = unidecode.unidecode(company_name.lower())
    name = re.sub(r'[.,&()\-]', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()
    suffixes_to_remove = {
        "inc", "incorporated", "corp", "corporation", "ltd", "limited", "llc",
        "co", "company", "gmbh", "ag", "sa", "sab", "de", "cv", "spa", "bv",
        "nv", "ab", "as", "oy", "se", "plc", "pty", "pvt", "private", "public"
    }
    tokens = [t for t in name.split() if t not in suffixes_to_remove]
    return " ".join(tokens)


def initial_matches(tokens1: list[str], tokens2: list[str]) -> bool:
    """
    Allow initials to support a borderline match, but only if:
    - Both names have at least 2 tokens
    - At least 2 meaningful tokens match directly or via single-character initial expansion
    """
    if len(tokens1) < 2 or len(tokens2) < 2:
        return False

    aligned = 0
    for t1, t2 in zip(tokens1, tokens2):
        if t1 == t2:
            aligned += 1
        # Only allow single-character initials to match full names
        elif len(t1) == 1 and len(t2) > 1 and t2.startswith(t1):
            aligned += 1
        elif len(t2) == 1 and len(t1) > 1 and t1.startswith(t2):
            aligned += 1
        # Don't allow multi-character tokens like "JB" to match anything
        else:
            continue
    return aligned >= 2


def fuzzy_match(
    actual_name: str,
    test_name: str,
    type: Literal["company", "person"] | str,
    threshold: float,
    verbose: bool = False
) -> bool:
    logger = get_logger()

    if threshold < 1:
        threshold = threshold * 100

    if type == "company":
        actual_name = normalize_company_name(actual_name)
        test_name = normalize_company_name(test_name)
        score = fuzz.token_set_ratio(actual_name, test_name)
        is_match = score >= threshold
        if verbose:
            return {

            }

    elif type == "person":
        actual_name = normalize_person_name(actual_name)
        test_name = normalize_person_name(test_name)
        tokens1 = actual_name.split()
        tokens2 = test_name.split()
        if len(tokens1) < 2 or len(tokens2) < 2:
            # Only allow match if exact string match after normalization
            return actual_name == test_name
        score = fuzz.token_set_ratio(actual_name, test_name)

        # Allow initials to help only when score is close
        if score >= threshold:
            return True
        # elif threshold - 5 <= score < threshold and initial_matches(tokens1, tokens2):
        #     return True
        else:
            return False
    else:
        raise ValueError(f"Invalid type: {type}")


def score_fuzzy_match(
    actual_name: str,
    test_name: str,
    type: Literal["company", "person"] | str,
    threshold: float
) -> bool:
    logger = get_logger()

    if not actual_name or not test_name:
        print(f"Error in score_fuzzy_match - Empty input: actual_name: {actual_name}, test_name: {test_name}")
        return {
            'is_match': False,
            'score': 0,
            'target_normalized': '',
            'discovered_normalized': '',
            'match_type': 'empty_input'
        }

    if threshold < 1:
        threshold = threshold * 100

    if type == "company":
        actual_name = normalize_company_name(actual_name)
        test_name = normalize_company_name(test_name)
        score = fuzz.token_set_ratio(actual_name, test_name)
        is_match = score >= threshold
        return {
            "score": score,
            "is_match": is_match,
            "actual_normalized": actual_name,
            "test_normalized": test_name,
            "match_type": "rapidfuzz"
        }
    elif type == "person":
        actual_name = normalize_person_name(actual_name)
        test_name = normalize_person_name(test_name)
        tokens1 = actual_name.split()
        tokens2 = test_name.split()
        if len(tokens1) < 2 or len(tokens2) < 2:
            # If one has only a single word, then it must be an exact match...
            is_match = actual_name == test_name
            score = 100.0 if is_match else 0.0
            return {
                "score": score,
                "is_match": is_match,
                "actual_normalized": actual_name,
                "test_normalized": test_name,
                "match_type": "exact_single_word"
            }

        # Calculate basic fuzzy score
        score = fuzz.token_set_ratio(actual_name, test_name)

        # For person names, add stricter validation to prevent false positives
        # like "Sam Brenner" matching "Sam Frenzel"
        if score >= threshold:
            # Additional validation for person names
            is_valid_person_match = _validate_person_name_match(tokens1, tokens2, score, threshold)
            if not is_valid_person_match:
                # Reduce score significantly if validation fails
                score = max(0, score - 30)  # Penalty for failed validation

        is_match = score >= threshold
        return {
            "score": score,
            "is_match": is_match,
            "actual_normalized": actual_name,
            "test_normalized": test_name,
            "match_type": "rapidfuzz_with_person_validation"
        }
    else:
        raise ValueError(f"Invalid type: {type}")


def _validate_person_name_match(tokens1: list, tokens2: list, score: float, threshold: float) -> bool:
    """
    Additional validation for person names to prevent false positives.
    Returns True if the match is valid, False if it should be rejected.
    """
    logger = get_logger()

    # If score is very high (95+), likely a legitimate match
    if score >= 95:
        return True

    # Extract likely first and last names (assuming first token is first name, last token is last name)
    first1, last1 = tokens1[0], tokens1[-1]
    first2, last2 = tokens2[0], tokens2[-1]

    # Check if last names are reasonably similar
    last_name_score = fuzz.ratio(last1, last2)

    # If last names are very different (< 60% similar), be more strict
    if last_name_score < 60:
        logger.debug(f"Last names '{last1}' vs '{last2}' are too different (score: {last_name_score})")

        # Check if first names are exact or very similar
        first_name_score = fuzz.ratio(first1, first2)

        # DISABLE initial matching for now - too many false positives
        # Single-character last names (initials) are almost always false positives
        # when searching for specific people, so we reject them entirely
        if len(last1) == 1 or len(last2) == 1:
            logger.debug(f"Rejecting match due to single-character last name: '{last1}' vs '{last2}' - initials not allowed")
            return False

        # Even if first names match well, reject if last names are completely different
        if last_name_score < 40:  # Very different last names
            logger.debug(f"Rejecting match due to very different last names: '{last1}' vs '{last2}'")
            return False

        # If first names are also not very similar, reject
        if first_name_score < 80:
            logger.debug(f"Rejecting match due to different first names (score: {first_name_score}) and last names (score: {last_name_score})")
            return False

    # Check initials as an additional safeguard
    initials1 = ''.join([token[0] for token in tokens1])
    initials2 = ''.join([token[0] for token in tokens2])

    if initials1 != initials2:
        # Different initials - be more strict
        if score < 85:  # Require higher score when initials don't match
            logger.debug(f"Rejecting match due to different initials: '{initials1}' vs '{initials2}' with score {score}")
            return False

    return True


def analyze_positions_for_company_match(
    target_company,
    all_positions: List[Dict[Literal['company', 'job_title', 'is_current'], Any]],
    threshold=75
) -> Dict[Literal['has_current_match', 'has_any_match', 'any_match'], Any]:
    """
    Simple company matching - check if target company matches any position,
    and if that matching position is current.

    Args:
        target_company (str): Company name to search for
        all_positions (list): List of all position dictionaries (current + historical)
        threshold (int): Minimum similarity score for a match

    Returns:
        dict: Simple match information
            {
                'has_any_match': bool,      # True if target company matches any position
                'has_current_match': bool,  # True if target company matches a current position
                'any_match': dict,          # Best matching position info (keeping name for compatibility)
            }
    """
    if not all_positions:
        return {
            'has_any_match': False,
            'has_current_match': False,
            'any_match': None
        }

    best_match = None
    best_score = 0
    has_current_match = False

    # Check each position for company match
    for position in all_positions:
        if position.get('company'):
            match_result = score_fuzzy_match(
                actual_name=target_company,
                test_name=position['company'],
                type="company",
                threshold=threshold
            )

            if match_result['is_match']:
                # Track the best match
                if match_result['score'] > best_score:
                    best_score = match_result['score']
                    best_match = {
                        'position': position,
                        'match_result': match_result
                    }

                # Check if this matching position is current
                if position.get('is_current', False):
                    has_current_match = True

    return {
        'has_any_match': best_match is not None,
        'has_current_match': has_current_match,
        'any_match': best_match  # Keeping 'any_match' name for compatibility with existing code
    }


if __name__ == "__main__":
    base_name = "Sam Brenner"
    test_names = [
        "Sam Frenzel",
        "Samuel Brenner",
        "Sammy B",
        "Brenner Sam"
    ]
    print(base_name + "\n" + "*" * 80)
    for test_name in test_names:
        result = fuzzy_match(
            base_name,
            test_name,
            "person",
            0.8
        )
        print(f"{result}: {test_name}")

    positions = [
        {
            "title": "Engineering Entry-Level Recruiter",
            "company": "Bloomberg",
            "date": "jun 2024 - present",
            "is_current": True
        },
        {
            "title": "HR Recruiter",
            "company": "Screenvision Media",
            "date": "nov 2019 - jul 2020",
            "is_current": False
        },
        {
            "title": "Technical Sourcer",
            "company": "Modis",
            "date": "oct 2017 - jun 2018",
            "is_current": False
        },
        {
            "title": "Human Resources Intern",
            "company": "Kid Care Concierge",
            "date": "sep 2017 - dec 2017",
            "is_current": False
        },
        {
            "title": "Human Resources Intern",
            "company": "Aflac",
            "date": "jun 2017 - sep 2017",
            "is_current": False
        }
    ]
    result = analyze_positions_for_company_match(
        target_company="Bloomberg",
        all_positions=positions,
        threshold=0.8
    )
    print(json.dumps(result, indent=4))
    # Returns:
    # {
    #     "has_any_match": true,
    #     "has_current_match": true,
    #     "any_match": {
    #         "position": {
    #             "title": "Engineering Entry-Level Recruiter",
    #             "company": "Bloomberg",
    #             "date": "jun 2024 - present",
    #             "is_current": true
    #         },
    #         "match_result": {
    #             "score": 100.0,
    #             "is_match": true,
    #             "actual_normalized": "bloomberg",
    #             "test_normalized": "bloomberg",
    #             "match_type": "rapidfuzz"
    #         }
    #     }
    # }
