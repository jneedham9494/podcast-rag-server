"""
Guest name cleaning and normalization utilities.
"""

import re
from typing import Optional


def clean_guest_name(name: str) -> Optional[str]:
    """
    Clean and normalize guest names.

    Removes common prefixes, parenthetical content, trailing patterns,
    and filters out generic terms that aren't actual names.

    Args:
        name: Raw guest name to clean

    Returns:
        Cleaned name or None if invalid
    """
    if not name:
        return None

    # Remove common prefixes
    name = re.sub(
        r'^(?:with\s+|featuring\s+|ft\.?\s+)',
        '',
        name,
        flags=re.IGNORECASE
    )
    name = re.sub(r'\([^)]*\)', '', name)
    name = re.sub(
        r'\s+(?:returns?|part\s+\d+|#\d+)$',
        '',
        name,
        flags=re.IGNORECASE
    )

    # Remove trailing prepositions and common patterns
    name = re.sub(
        r'\s+to\s+(?:discuss|talk|chat|look|preview|review)$',
        '',
        name,
        flags=re.IGNORECASE
    )
    name = re.sub(
        r'\s+of\s+(?:CBS|ESPN|The Athletic|Second Captains)$',
        '',
        name,
        flags=re.IGNORECASE
    )
    name = re.sub(r'\s+from\s+(?:the|The)\s+\w+$', '', name)

    # Remove job titles at the start
    name = re.sub(
        r'^(?:Author|Writer|Journalist|Professor|Director|Comedian|Reporter|Activist)\s+',
        '',
        name
    )

    # Extract person name from "Company CEO Name" patterns
    # "Mercury Group CEO Anton Posner" -> "Anton Posner"
    match = re.match(
        r'^(.+?)\s+(CEO|Founder|President|Director)\s+(.+?)(?:\s+about)?$',
        name
    )
    if match:
        person = match.group(3)
        name = person.strip()

    # Remove Fed position titles (extract person name)
    # "Chicago Fed President Austan Goolsbee" -> "Austan Goolsbee"
    match = re.match(
        r'^(Chicago|Dallas|Richmond|San Francisco|New York)\s+Fed\s+President\s+(.+)$',
        name
    )
    if match:
        name = match.group(2).strip()

    # Clean "about her/his/their work" patterns
    name = re.sub(
        r'\s+about\s+(?:her|his|their)\s+work$',
        '',
        name,
        flags=re.IGNORECASE
    )

    name = ' '.join(name.split())

    if len(name) < 3:
        return None

    name_lower = name.lower()

    # Skip generic terms
    skip_terms = [
        'podcast', 'show', 'episode', 'special', 'bonus', 'trailer', 'live',
        'coming soon', 'listen now', 'doctors', 'diaries', 'journey', 'corp',
        'world', 'society', 'institute', 'foundation', 'models', 'research',
        'economics and', 'about her', 'about his'
    ]

    if any(term in name_lower for term in skip_terms):
        return None

    # Skip if starts with question words/articles
    if any(name_lower.startswith(q) for q in [
        'how ', 'why ', 'what ', 'the ', 'a ', 'an ', 'of '
    ]):
        return None

    if ' vs ' in name_lower or name[0].isdigit():
        return None

    return name
