"""
Extraction package for guest and Twitter handle extraction from podcast metadata.

This package provides utilities for:
- Detecting non-guest episodes (compilations, trailers, etc.)
- Extracting guest names from titles and descriptions
- Finding Twitter handles in metadata
- Cleaning and normalizing guest names
"""

from .episode_detector import is_non_guest_episode
from .name_cleaner import clean_guest_name
from .twitter_finder import extract_twitter_handles
from .title_extractor import extract_guest_from_title
from .description_extractor import extract_guest_from_description
from .main import extract_guests_with_twitter

__all__ = [
    'is_non_guest_episode',
    'clean_guest_name',
    'extract_twitter_handles',
    'extract_guest_from_title',
    'extract_guest_from_description',
    'extract_guests_with_twitter',
]
