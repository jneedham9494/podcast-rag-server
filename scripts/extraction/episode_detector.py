"""
Episode type detection for identifying non-guest episodes.

Detects compilations, trailers, AMAs, and other episode types
that don't have specific guests.
"""

from typing import Tuple, Optional


def is_non_guest_episode(
    title: str,
    description: str,
    podcast_name: str
) -> Tuple[bool, Optional[str]]:
    """
    Detect if an episode is a non-guest episode.

    Args:
        title: Episode title
        description: Episode description
        podcast_name: Name of the podcast

    Returns:
        Tuple of (is_non_guest, episode_type) where episode_type
        describes why it's a non-guest episode (or None if it has guests)
    """
    title_lower = title.lower()
    desc_lower = description.lower() if description else ""

    # Compilation/Best of episodes
    if any(pattern in title_lower for pattern in [
        'best of', 'highlights', 'compilation', 'emergency questions'
    ]):
        return (True, "compilation")

    # Season announcements and trailers
    if any(pattern in title_lower for pattern in [
        'season', 'incoming', 'returns', 'preview', 'welcome to', 'introducing'
    ]) and any(pattern in title_lower or pattern in desc_lower for pattern in [
        'new season', 'coming soon', 'tune in', 'join', 'returns with'
    ]):
        return (True, "trailer/announcement")

    # AMA and Q&A episodes
    if any(pattern in title_lower for pattern in ['ama', 'q&a', 'q and a']):
        return (True, "ama/q&a")

    # Bonus/special episodes without specific guests
    if 'bonus' in title_lower and 'acast' in title_lower:
        return (True, "bonus/special")

    # RHLSTP specific: Emergency Questions compilations
    if 'emergency questions' in title_lower:
        return (True, "emergency_questions")

    # Check description for compilation indicators
    if 'best of' in desc_lower or 'compilation' in desc_lower:
        return (True, "compilation")

    # Cross-promotion episodes
    if any(pattern in title_lower for pattern in [
        'introducing:', 'big take:', "everybody's business:"
    ]):
        return (True, "cross_promotion")

    # Rereleases
    if '(rerelease)' in title_lower or 're-release' in title_lower:
        return (True, "rerelease")

    # Sponsored content
    if 'sponsored content' in title_lower:
        return (True, "sponsored")

    # Podcast-specific patterns
    result = _check_podcast_specific_patterns(
        title_lower, desc_lower, podcast_name.lower()
    )
    if result[0]:
        return result

    return (False, None)


def _check_podcast_specific_patterns(
    title_lower: str,
    desc_lower: str,
    podcast_lower: str
) -> Tuple[bool, Optional[str]]:
    """
    Check podcast-specific patterns for non-guest episodes.

    Args:
        title_lower: Lowercase episode title
        desc_lower: Lowercase episode description
        podcast_lower: Lowercase podcast name

    Returns:
        Tuple of (is_non_guest, episode_type)
    """
    # Odd Lots "Lots More" roundup episodes
    if 'odd lots' in podcast_lower and title_lower.startswith('lots more on'):
        return (True, "roundup")

    # Joshua Citarella solo/theory episodes
    if 'joshua citarella' in podcast_lower or 'citarella' in podcast_lower:
        solo_patterns = [
            "josh's theory", "josh's political", "class fantasy game",
            "vilem flusser", "deep research:", "my political journey:"
        ]
        if any(pattern in title_lower for pattern in solo_patterns):
            return (True, "solo/theory")

    # Chapo Trap House special series
    if 'chapo' in podcast_lower:
        series_patterns = [
            "movie mindset", "seeking a fren", "the players club",
            "teaser", "call-in show", "panic world"
        ]
        if any(pattern in title_lower for pattern in series_patterns):
            return (True, "special_series")

    # Sad Boyz solo episodes
    if 'sad boyz' in podcast_lower or 'sadboyz' in podcast_lower:
        if '(w/' not in title_lower and 'w/ ' not in title_lower:
            if desc_lower and (
                'jarvis and jordan' in desc_lower or
                'the boys discuss' in desc_lower
            ):
                return (True, "solo_hosts")

    # The Yard solo episodes
    if 'the yard' in podcast_lower or 'yard' in podcast_lower:
        has_guest_indicator = any(
            x in title_lower for x in ['(ft.', '(w/', 'w/ ', 'ft. ']
        )
        if not has_guest_indicator:
            if desc_lower and (
                'the boys talk about' in desc_lower or
                'this week, the boys' in desc_lower
            ):
                return (True, "solo_hosts")

    # TRUE ANON Tip Line episodes
    if 'true anon' in podcast_lower or 'trueanon' in podcast_lower:
        if 'tip line' in title_lower:
            return (True, "tip_line")

    return (False, None)
