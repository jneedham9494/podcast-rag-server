"""
Guest extraction from episode descriptions.

Contains podcast-specific and universal patterns for extracting
guest names from episode descriptions.
"""

import re
from typing import Optional, List


def extract_guest_from_description(
    description: str,
    podcast_name: str
) -> Optional[str]:
    """
    Extract guest name from episode description.

    Args:
        description: Episode description
        podcast_name: Name of the podcast

    Returns:
        Extracted guest name or None if not found
    """
    if not description:
        return None

    # Remove HTML tags and special unicode
    desc_clean = re.sub(r'<[^>]+>', '', description)
    desc_clean = re.sub(r'[\u200b-\u200f\u202a-\u202e]', '', desc_clean)

    podcast_lower = podcast_name.lower()

    # Try podcast-specific extractors
    if 'adam buxton' in podcast_lower:
        result = _extract_adam_buxton(desc_clean)
        if result:
            return result

    if 'joshua citarella' in podcast_lower or 'citarella' in podcast_lower:
        result = _extract_citarella(desc_clean)
        if result:
            return result

    if 'louis theroux' in podcast_lower or 'theroux' in podcast_lower or 'grounded' in podcast_lower:
        result = _extract_theroux_grounded(desc_clean)
        if result:
            return result

    if 'rhlstp' in podcast_lower or 'richard herring' in podcast_lower:
        result = _extract_rhlstp(desc_clean)
        if result:
            return result

    if 'odd lots' in podcast_lower:
        result = _extract_odd_lots(desc_clean)
        if result:
            return result

    if 'chapo' in podcast_lower:
        result = _extract_chapo(desc_clean)
        if result:
            return result

    if 'true anon' in podcast_lower or 'trueanon' in podcast_lower:
        result = _extract_trueanon(desc_clean)
        if result:
            return result

    # Universal fallback patterns
    return _extract_universal(desc_clean)


def _extract_name_from_descriptor(text: str) -> Optional[str]:
    """
    Extract just the name part from text with descriptors.

    Filters out common descriptor words like 'British', 'comedian', etc.
    """
    words = text.split()
    name_words = []
    skip_words = {
        'british', 'american', 'english', 'canadian', 'australian',
        'and', 'the', 'dr', 'comedian', 'writer', 'actor', 'humorist',
        'composer', 'radiohead', 'man'
    }

    for word in reversed(words):
        word_clean = word.strip()
        if not word_clean:
            continue
        if word_clean[0].isupper() and word_clean.lower() not in skip_words:
            name_words.insert(0, word_clean)
        elif word_clean.lower() in ['van', 'de', 'von']:
            name_words.insert(0, word_clean)
        else:
            break

    return ' '.join(name_words) if name_words else text


def _extract_adam_buxton(desc: str) -> Optional[str]:
    """Extract guest from Adam Buxton descriptions."""
    # Pattern 1a: "old friend/Dr GUEST"
    match = re.search(
        r'Adam talks with\s+(?:old friend|Dr\.?)\s+'
        r'([A-Z][a-zA-Z\'\-]+(?:\s+(?:van|de|von)?\s*[A-Z][a-zA-Z\'\-]+)+?)'
        r'(?:\s+about|\s+in front|\s+at|\s*,|\s*\()',
        desc
    )
    if not match:
        # Pattern 1b: Generic descriptor + guest
        match = re.search(
            r'Adam talks with\s+(?:[a-zA-Z\s,\(\)]+?)?'
            r'([A-Z][a-zA-Z\'\-]+(?:\s+(?:van|de|von)?\s*[A-Z][a-zA-Z\'\-]+)+?)'
            r'(?:\s+about|\s+in front|\s+live|\s*,|\s*\(|Recorded|Thanks|\.|\s+and\s+)',
            desc
        )
    if match:
        guest_clean = _extract_name_from_descriptor(match.group(1).strip())
        if len(guest_clean) > 3:
            return guest_clean

    # Pattern 2: "Adam rambles with..."
    match = re.search(
        r'Adam rambles with\s+.+?'
        r'([A-Z][a-zA-Z\'\-]+(?:\s+[A-Z][a-zA-Z\'\-]+)+?)'
        r'(?:\s+about|\s*\(|Recorded|\.)',
        desc
    )
    if match:
        guest_clean = _extract_name_from_descriptor(match.group(1).strip())
        if len(guest_clean) > 3:
            return guest_clean

    # Pattern 3: "Adam enjoys a conversation with..."
    match = re.search(
        r'Adam enjoys a (?:rambly )?conversation with\s+.+?'
        r'([A-Z][a-zA-Z\'\-]+(?:\s+[A-Z][a-zA-Z\'\-]+)+?)'
        r'(?:\s+in front|\s+about|\s*\(|\.)',
        desc
    )
    if match:
        guest_clean = _extract_name_from_descriptor(match.group(1).strip())
        if len(guest_clean) > 3:
            return guest_clean

    # Pattern 4: "Adam enjoys a short ramble with..."
    match = re.search(
        r'Adam enjoys a short ramble with\s+.+?'
        r'([A-Z][a-zA-Z\'\-]+(?:\s+[A-Z][a-zA-Z\'\-]+)+?)'
        r'(?:Recorded|\.)',
        desc
    )
    if match:
        guest_clean = _extract_name_from_descriptor(match.group(1).strip())
        if len(guest_clean) > 3:
            return guest_clean

    # Pattern 5: "Adam's talk with..."
    match = re.search(
        r"Adam's talk with\s+.+?"
        r'([A-Z][a-zA-Z\'\-]+(?:\s+[A-Z][a-zA-Z\'\-]+)+?)'
        r'(?:\s*,|\.|$)',
        desc
    )
    if match:
        guest_clean = _extract_name_from_descriptor(match.group(1).strip())
        if len(guest_clean) > 3:
            return guest_clean

    # Pattern 6: "Adam and Joe" co-host episodes
    if 'Adam and Joe' in desc:
        return "Joe Cornish"

    return None


def _extract_citarella(desc: str) -> Optional[str]:
    """Extract guest from Joshua Citarella descriptions."""
    match = re.search(
        r'My guest is\s+([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,4}),',
        desc
    )
    if match:
        return match.group(1).strip()
    return None


def _extract_theroux_grounded(desc: str) -> Optional[str]:
    """Extract guest from Louis Theroux/Grounded descriptions."""
    # Pattern 1: "Louis sits down with..."
    match = re.search(
        r'Louis sits down with\s+(?:[a-zA-Z\s,\(\)-]+?)?'
        r'([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,4}),',
        desc
    )
    if match:
        guest_clean = _extract_name_from_descriptor(match.group(1).strip())
        if len(guest_clean) > 3:
            return guest_clean

    # Pattern 2: "Louis speaks with/to..."
    match = re.search(
        r'Louis speaks (?:with|to)\s+'
        r'([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,4})(?:,|\.)',
        desc
    )
    if match:
        return match.group(1).strip()

    # Pattern 3: "Louis is joined by..."
    match = re.search(
        r'Louis is joined (?:in the studio )?by\s+(?:[a-zA-Z\s,\(\)-]+?)?'
        r'([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,4})(?:,|\.)',
        desc
    )
    if match:
        guest_clean = _extract_name_from_descriptor(match.group(1).strip())
        if len(guest_clean) > 3:
            return guest_clean

    # Pattern 4: "GUEST talks to Louis"
    match = re.search(
        r'([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,4})\s+talks to Louis',
        desc
    )
    if match:
        return match.group(1).strip()

    return None


def _extract_rhlstp(desc: str) -> Optional[str]:
    """Extract guest from RHLSTP descriptions."""
    # Pattern 1: "Richard talks to..."
    match = re.search(
        r'Richard talks to\s+(?:[a-zA-Z\s,\(\)-]+?)?'
        r'([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,4})\s+about',
        desc
    )
    if match:
        guest = match.group(1).strip()
        words = guest.split()
        name_words = []
        for word in reversed(words):
            if word and word[0].isupper() and word.lower() not in ['book', 'club']:
                name_words.insert(0, word)
            else:
                break
        guest_clean = ' '.join(name_words) if name_words else guest
        if len(guest_clean) > 3:
            return guest_clean

    # Pattern 2: "His guest is..."
    match = re.search(
        r'His guest is\s+(?:[a-zA-Z\s,\(\)-]+?)?'
        r'([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,4})\.',
        desc
    )
    if match:
        guest = match.group(1).strip()
        words = guest.split()
        name_words = []
        for word in reversed(words):
            if word and word[0].isupper() and word.lower() not in ['his', 'guest']:
                name_words.insert(0, word)
            else:
                break
        guest_clean = ' '.join(name_words) if name_words else guest
        if len(guest_clean) > 3:
            return guest_clean

    # Pattern 3: Generic interview patterns
    match = re.search(
        r'(?:talks to|chats with|interviews)\s+'
        r'([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,4})',
        desc
    )
    if match:
        return match.group(1).strip()

    return None


def _extract_odd_lots(desc: str) -> Optional[str]:
    """Extract guest from Odd Lots descriptions."""
    # Pattern 1: "we speak with GUEST, a..."
    match = re.search(
        r'we speak with\s+([A-Z][a-zA-Z\'\-\.]+(?:\s+(?:van|de|von|di|da|del)?\s*'
        r'[A-Z][a-zA-Z\'\-\.]+)+),\s+(?:a|an|the|who)',
        desc
    )
    if match:
        return match.group(1).strip()

    # Pattern 2: "Tracy and Joe speak with..."
    match = re.search(
        r'(?:Tracy and Joe speak with|speak with|talk to|talk with)\s+'
        r'([A-Z][a-zA-Z\'\-\.]+(?:\s+(?:van|de|von|di|da|del)?[A-Z]?'
        r'[a-zA-Z\'\-\.]+){1,4})',
        desc
    )
    if match:
        return match.group(1).strip()

    # Pattern 3: Fed President titles
    match = re.search(
        r'(?:Federal Reserve Bank|Fed|Federal Reserve|San Francisco Fed|'
        r'Chicago Fed|Richmond Fed|New York Fed)\s+President\s+'
        r'([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,3})',
        desc
    )
    if match:
        return match.group(1).strip()

    # Pattern 4: "In this episode...speak with..."
    match = re.search(
        r'In this episode[^\.]+(?:speak with|talk to|talk with)\s+'
        r'([A-Z][a-zA-Z\'\-\.]+(?:\s+(?:van|de|von|di|da|del)?[A-Z]?'
        r'[a-zA-Z\'\-\.]+){1,4})',
        desc
    )
    if match:
        return match.group(1).strip()

    # Pattern 5: "According to GUEST,..."
    match = re.search(
        r'^According to\s+([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,3}),',
        desc
    )
    if match:
        return match.group(1).strip()

    # Pattern 6: "GUEST is the/a [profession]"
    match = re.search(
        r'^([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,3})\s+is\s+(?:the|a)\s+',
        desc
    )
    if match:
        guest = match.group(1).strip()
        if not any(x in guest for x in ['The ', 'This ', 'These ', 'That ']):
            return guest

    # Pattern 7: "GUEST has built/is/was..."
    match = re.search(
        r'^([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,3})\s+(?:has|is|was)\s+',
        desc
    )
    if match:
        guest = match.group(1).strip()
        if not any(x in guest for x in [
            'Some ', 'The ', 'This ', 'That ', 'Many ', 'Few '
        ]):
            return guest

    # Pattern 8: "GUEST of [company]"
    match = re.search(
        r'\s+([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,3})\s+of\s+'
        r'[A-Z][a-zA-Z\s]+(?:,|\.|\s+)',
        desc
    )
    if match:
        guest = match.group(1).strip()
        if len(guest.split()) >= 2 and not any(
            x in guest for x in ['CEO', 'President', 'director']
        ):
            return guest

    return None


def _extract_chapo(desc: str) -> Optional[str]:
    """Extract guest from Chapo Trap House descriptions."""
    # Pattern 1: "We're joined by..."
    match = re.search(
        r"We're joined by\s+(?:[\w\s,\(\)-]+?)?([A-Z][\w\'\-\.]+(?:\s+[A-Z]?[\w\'\-\.]+){1,4})",
        desc,
        re.UNICODE
    )
    if match:
        guest = match.group(1).strip()
        guest = re.sub(r'\s+(?:for|to|from)$', '', guest)
        if len(guest.split()) >= 2:
            return guest

    # Pattern 2: "GUEST is back with"
    match = re.search(
        r'^([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,4})\s+is back with',
        desc
    )
    if match:
        return match.group(1).strip()

    # Pattern 3: "Will welcomes...to the show"
    match = re.search(
        r'Will welcomes\s+(?:[a-zA-Z\s,\(\)-]+?)?'
        r'([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,4})\s+to the show',
        desc
    )
    if match:
        guest = match.group(1).strip()
        if len(guest.split()) >= 2:
            return guest

    # Pattern 4: "[profession] GUEST joins us"
    match = re.search(
        r'(?:Author|Writer|Journalist|Sports journalist|Professor|Organizer|Comedian)\s+'
        r'([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,4})\s+joins us',
        desc
    )
    if match:
        return match.group(1).strip()

    # Pattern 5: "GUEST returns to the show"
    match = re.search(
        r'^([A-Z][\w\'\-\.]+(?:\s+[A-Z]?[\w\'\-\.]+){1,4})\s+returns to the show',
        desc,
        re.UNICODE
    )
    if match:
        return match.group(1).strip()

    # Pattern 6: "[profession] GUEST returns to the show"
    match = re.search(
        r'(?:Author|Writer|Journalist|Professor|Comedian|Tech reporter)\s+'
        r'([A-Z][\w\'\-\.]+(?:\s+[A-Z]?[\w\'\-\.]+){1,4})\s+returns to the show',
        desc,
        re.UNICODE
    )
    if match:
        return match.group(1).strip()

    # Pattern 7: "[profession] GUEST stops by the pod"
    match = re.search(
        r'(?:Comedian|Author|Writer|Journalist)\s+'
        r'([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,4})\s+stops by the pod',
        desc
    )
    if match:
        return match.group(1).strip()

    # Pattern 8: "GUEST joins us to discuss"
    match = re.search(
        r'^([A-Z][\w\'\-\.]+(?:\s+[A-Z]?[\w\'\-\.]+){1,4})(?:\s+\([^)]+\))?\s+joins us to discuss',
        desc,
        re.UNICODE
    )
    if match:
        return match.group(1).strip()

    # Pattern 9: "GUEST joins us this week"
    match = re.search(
        r'^([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,4})\s+joins us this week',
        desc
    )
    if match:
        return match.group(1).strip()

    # Pattern 10: "GUEST joins us"
    match = re.search(
        r'^([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,4})\s+joins us',
        desc
    )
    if match:
        return match.group(1).strip()

    # Pattern 11: "GUEST joins" (at start)
    if desc:
        match = re.search(
            r'^([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,4})\s+joins',
            desc
        )
        if match:
            return match.group(1).strip()

    return None


def _extract_trueanon(desc: str) -> Optional[str]:
    """Extract guest from TRUE ANON descriptions."""
    # Pattern 1: "We're joined by..."
    match = re.search(
        r"We're joined(?:\s+again)?\s+by\s+(?:[a-zA-Z\s,\(\)-]+?)?"
        r"([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,4})",
        desc
    )
    if match:
        guest = match.group(1).strip()
        guest = re.sub(r'\s+(?:to|from|of|about)$', '', guest)
        if len(guest.split()) >= 2:
            return guest

    # Pattern 2: "We talk to..."
    match = re.search(
        r'We talk to\s+(?:[a-zA-Z\s,\(\)-]+?)?'
        r'([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,4})',
        desc
    )
    if match:
        guest = match.group(1).strip()
        guest = re.sub(r'\s+(?:about|to|from)$', '', guest)
        if len(guest.split()) >= 2:
            return guest

    # Pattern 3: "We bring back...to talk"
    match = re.search(
        r'We bring back\s+(?:the\s+)?(?:[a-zA-Z\s,\(\)-]+?)'
        r'([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,4}),?\s+to talk',
        desc
    )
    if match:
        guest = match.group(1).strip()
        if len(guest.split()) >= 2:
            return guest

    # Pattern 4: "An interview with GUEST:"
    match = re.search(
        r'An interview with\s+'
        r'([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,4}):',
        desc
    )
    if match:
        return match.group(1).strip()

    # Pattern 5: "We welcome back..."
    match = re.search(
        r'We welcome back\s+(?:[a-zA-Z\s,\(\)-]+?)?'
        r'([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,4})',
        desc
    )
    if match:
        guest = match.group(1).strip()
        if len(guest.split()) >= 2:
            return guest

    # Pattern 6: "with GUEST, the subject"
    match = re.search(
        r'with\s+([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,4}),\s+the\s+subject',
        desc
    )
    if match:
        return match.group(1).strip()

    # Pattern 6b: "with GUEST to talk"
    match = re.search(
        r'with\s+([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,4})\s+to talk',
        desc
    )
    if match:
        return match.group(1).strip()

    # Pattern 7: "[profession] GUEST joins us"
    match = re.search(
        r'(?:Author|Writer|Journalist|Reporter|Correspondent|Activist|Professor)\s+'
        r'([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,4})\s+joins us',
        desc
    )
    if match:
        return match.group(1).strip()

    # Pattern 8: "GUEST joins us to talk"
    match = re.search(
        r'^([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,4})\s+joins us to talk',
        desc
    )
    if match:
        return match.group(1).strip()

    # Pattern 9: "GUEST joins us"
    match = re.search(
        r'^([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,4})\s+joins us',
        desc
    )
    if match:
        return match.group(1).strip()

    # Pattern 10: "GUEST is back"
    match = re.search(
        r'^([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,4})\s+is back',
        desc
    )
    if match:
        return match.group(1).strip()

    # Pattern 11: "GUEST & Topic"
    match = re.search(
        r'^([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,3})\s+&\s+',
        desc
    )
    if match:
        return match.group(1).strip()

    return None


def _extract_universal(desc: str) -> Optional[str]:
    """Extract guest using universal fallback patterns."""
    patterns = [
        # Original patterns
        r'(?:guest|Guest):\s+([A-Z][\w\'\-\.]+(?:\s+[A-Z]?[\w\'\-\.]+){1,3})',
        r'(?:talks with|speaks with|joined by|interview with|conversation with)\s+'
        r'([A-Z][\w\'\-\.]+(?:\s+[A-Z]?[\w\'\-\.]+){1,3})',
        r'^([A-Z][\w\'\-\.]+(?:\s+[A-Z]?[\w\'\-\.]+){1,3})\s+'
        r'(?:joins|discusses|talks about)',

        # Proven patterns from Chapo/TRUE ANON
        r"(?:We're|we're)\s+joined\s+(?:again\s+)?by\s+(?:[\w\s,\(\)-]+?)?"
        r'([A-Z][\w\'\-\.]+(?:\s+[A-Z]?[\w\'\-\.]+){1,4})',
        r'(?:We|we)\s+talk\s+to\s+(?:[\w\s,\(\)-]+?)?'
        r'([A-Z][\w\'\-\.]+(?:\s+[A-Z]?[\w\'\-\.]+){1,4})',
        r'with\s+([A-Z][\w\'\-\.]+(?:\s+[A-Z]?[\w\'\-\.]+){1,4})\s+(?:to\s+talk|about)',
        r'(?:An|an)\s+interview\s+with\s+'
        r'([A-Z][\w\'\-\.]+(?:\s+[A-Z]?[\w\'\-\.]+){1,4})',
        r'(?:We|we)\s+(?:welcome|bring\s+back)\s+(?:[\w\s,\(\)-]+?)?'
        r'([A-Z][\w\'\-\.]+(?:\s+[A-Z]?[\w\'\-\.]+){1,4})',
        r'(?:host|Host)\s+(?:talks|chats|speaks)\s+with\s+(?:[\w\s,\(\)-]+?)?'
        r'([A-Z][\w\'\-\.]+(?:\s+[A-Z]?[\w\'\-\.]+){1,4})',
        r'This\s+(?:week|episode):\s+'
        r'([A-Z][\w\'\-\.]+(?:\s+[A-Z]?[\w\'\-\.]+){1,4})',

        # Professional title patterns
        r'(?:Author|Writer|Journalist|Reporter|Professor|Comedian|Director|Actor)\s+'
        r'([A-Z][\w\'\-\.]+(?:\s+[A-Z]?[\w\'\-\.]+){1,4})\s+(?:joins|returns|stops by)',
    ]

    for pattern in patterns:
        match = re.search(pattern, desc, re.UNICODE)
        if match:
            guest = match.group(1).strip()
            guest = re.sub(r'\s+(?:for|to|from|about|of|on)$', '', guest)
            if len(guest.split()) >= 2:
                return guest

    return None
