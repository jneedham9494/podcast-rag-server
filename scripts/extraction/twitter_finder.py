"""
Twitter handle extraction utilities.
"""

import re
from typing import List


# Handles to filter out (common false positives)
HANDLE_BLACKLIST = [
    'googlemail', 'gmail', 'email', 'twitter',
    'instagram', 'facebook'
]


def extract_twitter_handles(text: str) -> List[str]:
    """
    Extract Twitter handles from text (@username format).

    Args:
        text: Text to search for Twitter handles

    Returns:
        List of Twitter handles (without @ prefix)
    """
    # Find @username patterns (1-15 characters, alphanumeric + underscore)
    handles = re.findall(r'@([A-Za-z0-9_]{1,15})\b', text)

    # Filter out common false positives
    filtered = []

    for handle in handles:
        if handle.lower() not in HANDLE_BLACKLIST and not handle.isdigit():
            filtered.append(handle)

    return filtered
