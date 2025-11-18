"""
Guest extraction from episode titles.

Contains podcast-specific patterns for extracting guest names from titles.
"""

import re
from typing import Optional


def extract_guest_from_title(title: str, podcast_name: str) -> Optional[str]:
    """
    Extract guest name from episode title.

    Uses podcast-specific patterns to identify guest names in titles.

    Args:
        title: Episode title
        podcast_name: Name of the podcast

    Returns:
        Extracted guest name or None if not found
    """
    title_clean = title.strip()
    podcast_lower = podcast_name.lower()

    # Try podcast-specific extractors first
    if 'friedland' in podcast_lower:
        result = _extract_adam_friedland(title_clean)
        if result:
            return result

    if 'odd lots' in podcast_lower:
        result = _extract_odd_lots(title_clean)
        if result:
            return result

    if 'adam buxton' in podcast_lower:
        result = _extract_adam_buxton(title_clean)
        if result:
            return result

    if 'louis theroux' in podcast_lower:
        result = _extract_louis_theroux(title_clean)
        if result:
            return result

    if 'grounded' in podcast_lower:
        result = _extract_grounded(title_clean)
        if result:
            return result

    if 'i like films' in podcast_lower or 'jonathan ross' in podcast_lower:
        result = _extract_i_like_films(title_clean)
        if result:
            return result

    if 'rhlstp' in podcast_lower or 'richard herring' in podcast_lower:
        result = _extract_rhlstp(title_clean)
        if result:
            return result

    if 'chapo' in podcast_lower:
        result = _extract_chapo(title_clean)
        if result:
            return result

    if 'joshua citarella' in podcast_lower or 'citarella' in podcast_lower:
        result = _extract_citarella(title_clean)
        if result:
            return result

    # Generic patterns
    return _extract_generic(title_clean)


def _extract_adam_friedland(title: str) -> Optional[str]:
    """Extract guest from Adam Friedland Show titles."""
    # Format 1: "GUEST NAME Talks/talks Topic"
    match = re.match(r'^([A-Z][A-Z\s\'-]+)\s+[Tt]alks\s+', title)
    if match:
        return match.group(1).strip().title()

    # Format 2: "GUEST NAME | Topic"
    match = re.match(r'^([A-Z][A-Z\s\'-]+)\s*\|\s*', title)
    if match:
        return match.group(1).strip().title()

    # Format 3: "The Adam Friedland Show Podcast - Guest Name - Episode ##"
    match = re.match(
        r'The Adam Friedland Show(?:\s+Podcast)?\s+-\s+(.+?)\s+-\s+'
        r'(?:Episode|The Lost Episodes)',
        title,
        re.IGNORECASE
    )
    if match:
        guest = match.group(1).strip()
        if len(guest.split()) >= 2 or len(guest) > 5:
            return guest

    # Format 4: "Episode ## Featuring Guest Name"
    match = re.search(
        r'Episode \d+\s+(?:Featuring|featuring|Ft\.|ft\.)\s+(.+?)$',
        title
    )
    if match:
        return match.group(1).strip()

    return None


def _extract_odd_lots(title: str) -> Optional[str]:
    """Extract guest from Odd Lots titles."""
    # Pattern 1: "Lots More With GUEST on/about..."
    # Use non-greedy +? to stop before "on/about"
    match = re.match(
        r'^Lots More [Ww]ith\s+([A-Z][a-zA-Z\'\-\.]+(?:\s+(?:van|de|von|di|da|del)?'
        r'[A-Z]?[a-zA-Z\'\-\.]+)+?)(?:\s+on|\s+about|\s*$)',
        title,
        re.IGNORECASE
    )
    if match:
        return match.group(1).strip()

    # Pattern 2: "GUEST on Topic"
    match = re.match(
        r'^([A-Z][a-zA-Z\'\-\.]+(?:\s+(?:van|de|von|di|da|del)?[A-Z]?'
        r'[a-zA-Z\'\-\.]+)+)\s+on\s+',
        title,
        re.IGNORECASE
    )
    if match:
        guest = match.group(1).strip()
        if not any(x in guest for x in [
            'Big Take', 'Everybody', 'Why ', 'How ', 'Inside ', 'What ', 'Lots More'
        ]):
            return guest

    # Pattern 3: "Topic With GUEST Name"
    match = re.search(
        r'\s+[Ww]ith\s+([A-Z][a-zA-Z\'\-\.]+(?:\s+(?:van|de|von)?[A-Z]?'
        r'[a-zA-Z\'\-\.]+)+)(?:\s+on|\s*$)',
        title
    )
    if match:
        guest = match.group(1).strip()
        if not any(x in guest for x in [
            'The ', 'A Trip', 'President', 'Fed ', 'CEO'
        ]):
            return guest

    # Pattern 4: "GUEST Is/Was/Wants..."
    match = re.match(
        r'^([A-Z][a-zA-Z\'\-\.]+(?:\s+(?:van|de|von)?[A-Z]?[a-zA-Z\'\-\.]+)+)'
        r'\s+(?:Is|Was|Wants|Thinks|Says|Explains)\s+',
        title
    )
    if match:
        guest = match.group(1).strip()
        if not any(x in guest for x in [
            'The ', 'Why ', 'What ', 'How ', 'This ', 'These '
        ]):
            return guest

    # Pattern 5: "GUEST: Topic"
    match = re.match(
        r'^([A-Z][a-zA-Z\'\-\.]+(?:\s+(?:van|de|von)?[A-Z]?[a-zA-Z\'\-\.]+)):\s+',
        title
    )
    if match:
        guest = match.group(1).strip()
        if not any(x in guest for x in [
            'Lots More', 'Big Take', 'The ', 'Why ', 'What '
        ]):
            return guest

    return None


def _extract_adam_buxton(title: str) -> Optional[str]:
    """Extract guest from Adam Buxton titles."""
    # "EP.198 - GUEST NAME"
    match = re.match(
        r'EP\.\d+\s*-\s*(.+?)(?:\s*@|\s*\d{4}|$)',
        title,
        re.IGNORECASE
    )
    if match:
        return match.group(1).strip().title()
    return None


def _extract_louis_theroux(title: str) -> Optional[str]:
    """Extract guest from Louis Theroux titles."""
    # "S1 EP1: Guest Name on/discusses..."
    match = re.match(
        r'S\d+\s+EP\d+:\s+([^,]+?)\s+(?:on|discusses|talks)',
        title,
        re.IGNORECASE
    )
    if match:
        return match.group(1).strip()
    return None


def _extract_grounded(title: str) -> Optional[str]:
    """Extract guest from Grounded titles."""
    # "18. Guest Name"
    match = re.match(r'^\d+\.\s+(.+?)$', title)
    if match:
        return match.group(1).strip()
    return None


def _extract_i_like_films(title: str) -> Optional[str]:
    """Extract guest from I Like Films titles."""
    # "1 Guest Name"
    match = re.match(r'^\d+\s+(.+?)$', title)
    if match:
        guest = match.group(1).strip()
        if len(guest.split()) >= 2:
            return guest
    return None


def _extract_rhlstp(title: str) -> Optional[str]:
    """Extract guest from RHLSTP titles."""
    # "RHLSTP 587 - Guest Name"
    match = re.match(
        r'RHLSTP\s+(?:Book Club\s+)?\d+\s+-\s+(.+?)(?:\s*\(Part\s+\d+\))?$',
        title,
        re.IGNORECASE
    )
    if match:
        guest = match.group(1).strip()
        if not any(x in guest.lower() for x in [
            'best of', 'emergency', 'live from'
        ]):
            return guest

    # "Retro RHLSTP ## - Guest Name"
    match = re.match(
        r'Retro\s+RHLSTP\s+\d+\s+-\s+(.+?)$',
        title,
        re.IGNORECASE
    )
    if match:
        return match.group(1).strip()

    return None


def _extract_chapo(title: str) -> Optional[str]:
    """Extract guest from Chapo Trap House titles."""
    # "feat. Guest Name" or "feat. Guest Name (date)"
    match = re.search(
        r'feat\.\s+(.+?)(?:\s*\([\d/]+\))?$',
        title,
        re.IGNORECASE
    )
    if match:
        guest = match.group(1).strip()
        # Skip host names
        if guest.lower() in ['felix', 'will', 'matt', 'chris', 'amber']:
            return None
        # Skip film/show titles
        if any(x in guest for x in [' to ', ' a ', ' the ', ' Up A ', ' of the ']):
            return None
        return guest

    return None


def _extract_citarella(title: str) -> Optional[str]:
    """Extract guest from Joshua Citarella titles."""
    # Pattern 1: "Doomscroll 31.5: Guest Name"
    match = re.match(
        r'Doomscroll\s+[\d\.]+:\s+(.+?)$',
        title,
        re.IGNORECASE
    )
    if match:
        return match.group(1).strip()

    # Pattern 2: "Topic w/ Guest Name"
    match = re.search(
        r'\s+w/\s+([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+)+)',
        title
    )
    if match:
        guest = match.group(1).strip()
        guest = re.sub(r':\s+Live.*$', '', guest, flags=re.IGNORECASE)
        if len(guest.split()) >= 2:
            return guest

    # Pattern 3: "GUEST on Topic"
    match = re.match(
        r'^([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+)+)\s+on\s+',
        title
    )
    if match:
        guest = match.group(1).strip()
        if not any(x in guest for x in ['Deep Research', 'My Political']):
            return guest

    return None


def _extract_generic(title: str) -> Optional[str]:
    """Extract guest using generic patterns."""
    # "(w/ Guest Name)" or "w/o Guest Name"
    match = re.search(
        r'\(w(?:ith)?\/?\s+([^\)]+)\)',
        title,
        re.IGNORECASE
    )
    if match:
        guest = match.group(1).strip()
        guest = re.sub(r'\s*\(\d+\)$', '', guest)
        if len(guest.split()) >= 2 or (len(guest) > 3 and len(guest.split()) == 1):
            return guest

    # "ft. Guest Name"
    match = re.search(r'\s+[Ff]t\.?\s+(.+?)(?:\s*\||$)', title)
    if match:
        guest = match.group(1).strip()
        guest = re.sub(r'\s*[-:].*$', '', guest)
        if len(guest) > 3:
            return guest

    return None
