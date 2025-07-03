import re
from rapidfuzz import fuzz
from app.logger import get_logger


def fuzzy_match(name1: str, name2: str, threshold: float) -> bool:
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

    print(f"name1_clean: {name1_clean}")
    print(f"name2_clean: {name2_clean}")

    # Calculate similarity ratio
    similarity = SequenceMatcher(None, name1_clean, name2_clean).ratio()
    similarity = fuzz.token_set_ratio(name1_clean, name2_clean)
    print(similarity)

    return similarity >= threshold


if __name__ == "__main__":
    result = fuzzy_match(
        "J. Fernández",
        "Juan Carlos Fernández Gómez",
        threshold=0.6
    )
    print(result)