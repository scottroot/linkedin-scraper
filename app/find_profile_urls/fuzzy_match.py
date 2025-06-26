import re
from difflib import SequenceMatcher


def fuzzy_match(name1: str, name2: str, threshold: float = 0.6) -> bool:
    """
    Perform fuzzy string matching between two names

    Args:
        name1 (str): First name to compare
        name2 (str): Second name to compare
        threshold (float): Minimum similarity ratio (0.0 to 1.0)

    Returns:
        bool: True if names match above threshold
    """
    # Normalize names for comparison
    name1_clean = re.sub(r'[^\w\s]', '', name1.lower().strip())
    name2_clean = re.sub(r'[^\w\s]', '', name2.lower().strip())

    # Calculate similarity ratio
    similarity = SequenceMatcher(None, name1_clean, name2_clean).ratio()

    return similarity >= threshold
