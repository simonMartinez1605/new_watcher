from fuzzywuzzy import fuzz

def find_similar_key(current_key, pending_merges, threshold=85):
    """
    Find a similar key in the pending merges list based on a similarity threshold.

    Args:
        current_key (str): The current key to compare against.
        pending_merges (list): A list of keys to check for similarity.
        threshold (int): The similarity threshold (0-100).

    Returns:
        str: The most similar key found, or None if no similar key is found.
    """
    for existing_key in pending_merges:
        similarity = fuzz.ratio(current_key, existing_key)
        if similarity >= threshold:
            return existing_key
    return None