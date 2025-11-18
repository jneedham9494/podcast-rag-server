#!/usr/bin/env python3
"""
Guest and Twitter Handle Extractor
Extracts guests from titles AND descriptions, plus finds Twitter handles in metadata
"""

import json
import re
from pathlib import Path
from collections import defaultdict


def is_non_guest_episode(title, description, podcast_name):
    """
    Detect if an episode is a non-guest episode (compilation, trailer, AMA, etc.)
    Returns (is_non_guest, episode_type) where episode_type describes why
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

    # Cross-promotion episodes (Introducing other shows, Big Take, etc.)
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

    # Odd Lots "Lots More" roundup episodes (usually no specific guest)
    if 'odd lots' in podcast_name.lower() and title_lower.startswith('lots more on'):
        return (True, "roundup")

    # Joshua Citarella solo/theory episodes
    if 'joshua citarella' in podcast_name.lower() or 'citarella' in podcast_name.lower():
        solo_patterns = [
            "josh's theory", "josh's political", "class fantasy game",
            "vilem flusser", "deep research:", "my political journey:"
        ]
        if any(pattern in title_lower for pattern in solo_patterns):
            return (True, "solo/theory")

    # Chapo Trap House special series (non-guest episodes)
    if 'chapo' in podcast_name.lower():
        series_patterns = [
            "movie mindset", "seeking a fren", "the players club",
            "teaser", "call-in show", "panic world"
        ]
        if any(pattern in title_lower for pattern in series_patterns):
            return (True, "special_series")
        # Note: Don't check description for "call-in show" - episodes often mention
        # upcoming call-in shows even when they have guests

    # Sad Boyz solo episodes (no guest)
    # Most episodes are just hosts Jarvis and Jordan; only episodes with "(w/ " have guests
    if 'sad boyz' in podcast_name.lower() or 'sadboyz' in podcast_name.lower():
        # If title doesn't have "(w/ " format, it's likely a solo episode
        if '(w/' not in title_lower and 'w/ ' not in title_lower:
            # Check description to confirm it's Jarvis and Jordan only
            if desc_lower and ('jarvis and jordan' in desc_lower or 'the boys discuss' in desc_lower):
                return (True, "solo_hosts")

    # The Yard solo episodes (no guest)
    # Most episodes are just the 4 hosts (Ludwig, Slime, Nick, Aiden); only episodes with "(ft. " or "(w/ " have guests
    if 'the yard' in podcast_name.lower() or 'yard' in podcast_name.lower():
        # If title doesn't have "(ft. " or "w/ " format, it's a solo hosts episode
        if '(ft.' not in title_lower and '(w/' not in title_lower and 'w/ ' not in title_lower and 'ft. ' not in title_lower:
            # Check description to confirm (usually says "the boys talk about")
            if desc_lower and ('the boys talk about' in desc_lower or 'this week, the boys' in desc_lower):
                return (True, "solo_hosts")

    # TRUE ANON Tip Line episodes (call-in shows, no specific guest)
    if 'true anon' in podcast_name.lower() or 'trueanon' in podcast_name.lower():
        if 'tip line' in title_lower:
            return (True, "tip_line")

    return (False, None)


def extract_guest_from_title(title, podcast_name):
    """Extract guest name from episode title"""
    title_clean = title.strip()
    podcast_lower = podcast_name.lower()

    # Adam Friedland Show: Multiple formats
    if 'friedland' in podcast_lower:
        # Format 1: "GUEST NAME Talks/talks Topic" (case-insensitive)
        match = re.match(r'^([A-Z][A-Z\s\'-]+)\s+[Tt]alks\s+', title_clean)
        if match:
            return match.group(1).strip().title()
        # Format 2: "GUEST NAME | Topic"
        match = re.match(r'^([A-Z][A-Z\s\'-]+)\s*\|\s*', title_clean)
        if match:
            return match.group(1).strip().title()
        # Format 3: "The Adam Friedland Show Podcast - Guest Name - Episode ##"
        match = re.match(r'The Adam Friedland Show(?:\s+Podcast)?\s+-\s+(.+?)\s+-\s+(?:Episode|The Lost Episodes)', title_clean, re.IGNORECASE)
        if match:
            guest = match.group(1).strip()
            # Clean up any trailing whitespace or special chars
            if len(guest.split()) >= 2 or len(guest) > 5:
                return guest
        # Format 4: "Episode ## Featuring Guest Name"
        match = re.search(r'Episode \d+\s+(?:Featuring|featuring|Ft\.|ft\.)\s+(.+?)$', title_clean)
        if match:
            return match.group(1).strip()

    # Odd Lots: Multiple title patterns
    if 'odd lots' in podcast_lower:
        # Pattern 1: "Lots More With GUEST on/about..."
        match = re.match(r'^Lots More [Ww]ith\s+([A-Z][a-zA-Z\'\-\.]+(?:\s+(?:van|de|von|di|da|del)?[A-Z]?[a-zA-Z\'\-\.]+)+)(?:\s+on|\s+about|\s*$)', title_clean, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        # Pattern 2: "GUEST on Topic" (original pattern)
        match = re.match(r'^([A-Z][a-zA-Z\'\-\.]+(?:\s+(?:van|de|von|di|da|del)?[A-Z]?[a-zA-Z\'\-\.]+)+)\s+on\s+', title_clean, re.IGNORECASE)
        if match:
            guest = match.group(1).strip()
            if not any(x in guest for x in ['Big Take', 'Everybody', 'Why ', 'How ', 'Inside ', 'What ', 'Lots More']):
                return guest

        # Pattern 3: "Topic With GUEST Name"
        match = re.search(r'\s+[Ww]ith\s+([A-Z][a-zA-Z\'\-\.]+(?:\s+(?:van|de|von)?[A-Z]?[a-zA-Z\'\-\.]+)+)(?:\s+on|\s*$)', title_clean)
        if match:
            guest = match.group(1).strip()
            if not any(x in guest for x in ['The ', 'A Trip', 'President', 'Fed ', 'CEO']):
                return guest

        # Pattern 4: "GUEST Is/Was/Wants..." (handles "Austan Goolsbee Is Still Concerned...")
        match = re.match(r'^([A-Z][a-zA-Z\'\-\.]+(?:\s+(?:van|de|von)?[A-Z]?[a-zA-Z\'\-\.]+)+)\s+(?:Is|Was|Wants|Thinks|Says|Explains)\s+', title_clean)
        if match:
            guest = match.group(1).strip()
            # Filter out obvious non-names
            if not any(x in guest for x in ['The ', 'Why ', 'What ', 'How ', 'This ', 'These ']):
                return guest

        # Pattern 5: "GUEST: Topic" (handles "David Woo: What Trump Started...")
        match = re.match(r'^([A-Z][a-zA-Z\'\-\.]+(?:\s+(?:van|de|von)?[A-Z]?[a-zA-Z\'\-\.]+)):\s+', title_clean)
        if match:
            guest = match.group(1).strip()
            # Filter out obvious non-names
            if not any(x in guest for x in ['Lots More', 'Big Take', 'The ', 'Why ', 'What ']):
                return guest

    # Adam Buxton: "EP.198 - GUEST NAME"
    if 'adam buxton' in podcast_lower:
        match = re.match(r'EP\.\d+\s*-\s*(.+?)(?:\s*@|\s*\d{4}|$)', title_clean, re.IGNORECASE)
        if match:
            return match.group(1).strip().title()

    # Louis Theroux: "S1 EP1: Guest Name on/discusses..."
    if 'louis theroux' in podcast_lower:
        match = re.match(r'S\d+\s+EP\d+:\s+([^,]+?)\s+(?:on|discusses|talks)', title_clean, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    # Grounded: "18. Guest Name"
    if 'grounded' in podcast_lower:
        match = re.match(r'^\d+\.\s+(.+?)$', title_clean)
        if match:
            return match.group(1).strip()

    # I Like Films: "1 Guest Name"
    if 'i like films' in podcast_lower or 'jonathan ross' in podcast_lower:
        match = re.match(r'^\d+\s+(.+?)$', title_clean)
        if match:
            guest = match.group(1).strip()
            if len(guest.split()) >= 2:
                return guest

    # RHLSTP: "RHLSTP 587 - Guest Name"
    if 'rhlstp' in podcast_lower or 'richard herring' in podcast_lower:
        match = re.match(r'RHLSTP\s+(?:Book Club\s+)?\d+\s+-\s+(.+?)(?:\s*\(Part\s+\d+\))?$', title_clean, re.IGNORECASE)
        if match:
            guest = match.group(1).strip()
            if not any(x in guest.lower() for x in ['best of', 'emergency', 'live from']):
                return guest

        match = re.match(r'Retro\s+RHLSTP\s+\d+\s+-\s+(.+?)$', title_clean, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    # Chapo: "feat. Guest Name" or "feat. Guest Name (date)"
    if 'chapo' in podcast_lower:
        # Match feat. Guest Name, optionally followed by (date) or (episode#)
        match = re.search(r'feat\.\s+(.+?)(?:\s*\([\d/]+\))?$', title_clean, re.IGNORECASE)
        if match:
            guest = match.group(1).strip()
            # Skip if it's a host name (Felix, Will, Matt, Chris)
            if guest.lower() in ['felix', 'will', 'matt', 'chris', 'amber']:
                return None
            # Skip if it looks like a film/show title (title case with prepositions)
            # e.g. "How to Blow Up A Pipeline"
            if any(x in guest for x in [' to ', ' a ', ' the ', ' Up A ', ' of the ']):
                return None
            return guest

    # Joshua Citarella: Multiple formats
    if 'joshua citarella' in podcast_lower or 'citarella' in podcast_lower:
        # Pattern 1: "Doomscroll 31.5: Guest Name"
        match = re.match(r'Doomscroll\s+[\d\.]+:\s+(.+?)$', title_clean, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        # Pattern 2: "Topic w/ Guest Name" (case-sensitive 'w/')
        match = re.search(r'\s+w/\s+([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+)+)', title_clean)
        if match:
            guest = match.group(1).strip()
            # Remove trailing info like ": Live at..."
            guest = re.sub(r':\s+Live.*$', '', guest, flags=re.IGNORECASE)
            if len(guest.split()) >= 2:
                return guest

        # Pattern 3: "GUEST on Topic" (e.g. "Alex Hochuli on the End of History")
        match = re.match(r'^([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+)+)\s+on\s+', title_clean)
        if match:
            guest = match.group(1).strip()
            # Filter out episode series names
            if not any(x in guest for x in ['Deep Research', 'My Political']):
                return guest

    # Generic: "(w/ Guest Name)" or "ft. Guest Name"
    match = re.search(r'\(w(?:ith)?\/?\s+([^\)]+)\)', title_clean, re.IGNORECASE)
    if match:
        guest = match.group(1).strip()
        guest = re.sub(r'\s*\(\d+\)$', '', guest)
        if len(guest.split()) >= 2 or (len(guest) > 3 and len(guest.split()) == 1):
            return guest

    match = re.search(r'\s+[Ff]t\.?\s+(.+?)(?:\s*\||$)', title_clean)
    if match:
        guest = match.group(1).strip()
        guest = re.sub(r'\s*[-:].*$', '', guest)
        if len(guest) > 3:
            return guest

    return None


def extract_twitter_handles(text):
    """Extract Twitter handles from text (@username format)"""
    # Find @username patterns (1-15 characters, alphanumeric + underscore)
    handles = re.findall(r'@([A-Za-z0-9_]{1,15})\b', text)

    # Filter out common false positives
    filtered = []
    blacklist = ['googlemail', 'gmail', 'email', 'twitter', 'instagram', 'facebook']

    for handle in handles:
        if handle.lower() not in blacklist and not handle.isdigit():
            filtered.append(handle)

    return filtered


def extract_guest_from_description(description, podcast_name):
    """Extract guest name from episode description"""
    if not description:
        return None

    # Remove HTML tags
    desc_clean = re.sub(r'<[^>]+>', '', description)
    # Remove special unicode characters that might interfere
    desc_clean = re.sub(r'[\u200b-\u200f\u202a-\u202e]', '', desc_clean)

    podcast_lower = podcast_name.lower()

    # Podcast-specific patterns (most reliable)

    # Adam Buxton: Multiple patterns for different episode formats
    if 'adam buxton' in podcast_lower:
        # Pattern 1: "Adam talks with [descriptor] GUEST NAME [delimiter]"
        # Handles: "Adam talks with British comedian, actor and writer Guz Khan about..."
        # Also handles: "old friend", "Dr Title", and missing spaces before Thanks/Recorded
        # Split into two sub-patterns for better accuracy

        # Sub-pattern 1a: Handle "old friend GUEST" or "Dr GUEST" specifically
        match = re.search(r'Adam talks with\s+(?:old friend|Dr\.?)\s+([A-Z][a-zA-Z\'\-]+(?:\s+(?:van|de|von)?\s*[A-Z][a-zA-Z\'\-]+)+?)(?:\s+about|\s+in front|\s+at|\s*,|\s*\()', desc_clean)
        if not match:
            # Sub-pattern 1b: Generic descriptor + guest pattern
            match = re.search(r'Adam talks with\s+(?:[a-zA-Z\s,\(\)]+?)?([A-Z][a-zA-Z\'\-]+(?:\s+(?:van|de|von)?\s*[A-Z][a-zA-Z\'\-]+)+?)(?:\s+about|\s+in front|\s+live|\s*,|\s*\(|Recorded|Thanks|\.|\s+and\s+)', desc_clean)
        if match:
            guest = match.group(1).strip()
            # Clean up descriptors - keep only the capitalized name part
            words = guest.split()
            name_words = []
            for word in reversed(words):
                word_clean = word.strip()
                if word_clean and word_clean[0].isupper() and word_clean.lower() not in ['british', 'american', 'english', 'canadian', 'australian', 'and', 'the', 'dr']:
                    name_words.insert(0, word_clean)
                elif word_clean.lower() in ['van', 'de', 'von']:
                    # Keep particles
                    name_words.insert(0, word_clean)
                else:
                    break
            guest_clean = ' '.join(name_words) if name_words else guest
            if len(guest_clean) > 3:
                return guest_clean

        # Pattern 2: "Adam rambles with [descriptor] GUEST NAME"
        match = re.search(r'Adam rambles with\s+.+?([A-Z][a-zA-Z\'\-]+(?:\s+[A-Z][a-zA-Z\'\-]+)+?)(?:\s+about|\s*\(|Recorded|\.)', desc_clean)
        if match:
            guest = match.group(1).strip()
            words = guest.split()
            name_words = []
            for word in reversed(words):
                if word[0].isupper() and word.lower() not in ['british', 'american', 'english', 'canadian', 'australian', 'comedian', 'and', 'the']:
                    name_words.insert(0, word)
                else:
                    break
            guest_clean = ' '.join(name_words) if name_words else guest
            if len(guest_clean) > 3:
                return guest_clean

        # Pattern 3: "Adam enjoys a [rambly] conversation with GUEST NAME"
        match = re.search(r'Adam enjoys a (?:rambly )?conversation with\s+.+?([A-Z][a-zA-Z\'\-]+(?:\s+[A-Z][a-zA-Z\'\-]+)+?)(?:\s+in front|\s+about|\s*\(|\.)', desc_clean)
        if match:
            guest = match.group(1).strip()
            words = guest.split()
            name_words = []
            for word in reversed(words):
                if word[0].isupper() and word.lower() not in ['british', 'american', 'english', 'and', 'writer', 'comedian']:
                    name_words.insert(0, word)
                else:
                    break
            guest_clean = ' '.join(name_words) if name_words else guest
            if len(guest_clean) > 3:
                return guest_clean

        # Pattern 4: "Adam enjoys a short ramble with GUEST NAME"
        match = re.search(r'Adam enjoys a short ramble with\s+.+?([A-Z][a-zA-Z\'\-]+(?:\s+[A-Z][a-zA-Z\'\-]+)+?)(?:Recorded|\.)', desc_clean)
        if match:
            guest = match.group(1).strip()
            words = guest.split()
            name_words = []
            for word in reversed(words):
                if word[0].isupper() and word.lower() not in ['american', 'humorist']:
                    name_words.insert(0, word)
                else:
                    break
            guest_clean = ' '.join(name_words) if name_words else guest
            if len(guest_clean) > 3:
                return guest_clean

        # Pattern 5: "Adam's talk with GUEST NAME"
        match = re.search(r"Adam's talk with\s+.+?([A-Z][a-zA-Z\'\-]+(?:\s+[A-Z][a-zA-Z\'\-]+)+?)(?:\s*,|\.|$)", desc_clean)
        if match:
            guest = match.group(1).strip()
            words = guest.split()
            name_words = []
            for word in reversed(words):
                if word[0].isupper() and word.lower() not in ['composer', 'radiohead', 'man', 'and']:
                    name_words.insert(0, word)
                else:
                    break
            guest_clean = ' '.join(name_words) if name_words else guest
            if len(guest_clean) > 3:
                return guest_clean

        # Pattern 6: "Adam and Joe" co-host episodes - extract Joe Cornish
        if 'Adam and Joe' in desc_clean:
            return "Joe Cornish"

    # Joshua Citarella: "My guest is GUEST NAME, a"
    if 'joshua citarella' in podcast_lower or 'citarella' in podcast_lower:
        match = re.search(r'My guest is\s+([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,4}),', desc_clean)
        if match:
            return match.group(1).strip()

    # Louis Theroux and Grounded: Multiple patterns
    if 'louis theroux' in podcast_lower or 'theroux' in podcast_lower or 'grounded' in podcast_lower:
        # Pattern 1: "Louis sits down with [descriptor] GUEST, ..."
        match = re.search(r'Louis sits down with\s+(?:[a-zA-Z\s,\(\)-]+?)?([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,4}),', desc_clean)
        if match:
            guest = match.group(1).strip()
            words = guest.split()
            name_words = []
            for word in reversed(words):
                if word and word[0].isupper():
                    name_words.insert(0, word)
                else:
                    break
            guest_clean = ' '.join(name_words) if name_words else guest
            if len(guest_clean) > 3:
                return guest_clean

        # Pattern 2: "Louis speaks with/to GUEST, ..." (comma or period)
        match = re.search(r'Louis speaks (?:with|to)\s+([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,4})(?:,|\.)', desc_clean)
        if match:
            return match.group(1).strip()

        # Pattern 3: "Louis is joined by [descriptor] GUEST." (comma or period)
        match = re.search(r'Louis is joined (?:in the studio )?by\s+(?:[a-zA-Z\s,\(\)-]+?)?([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,4})(?:,|\.)', desc_clean)
        if match:
            guest = match.group(1).strip()
            words = guest.split()
            name_words = []
            for word in reversed(words):
                if word and word[0].isupper():
                    name_words.insert(0, word)
                else:
                    break
            guest_clean = ' '.join(name_words) if name_words else guest
            if len(guest_clean) > 3:
                return guest_clean

        # Pattern 4: Reverse - "GUEST talks to Louis" (for Grounded especially)
        match = re.search(r'([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,4})\s+talks to Louis', desc_clean)
        if match:
            return match.group(1).strip()

    # RHLSTP: Multiple patterns for Richard Herring's podcast
    if 'rhlstp' in podcast_lower or 'richard herring' in podcast_lower:
        # Pattern 1: "Richard talks to [descriptor] GUEST about..."
        match = re.search(r'Richard talks to\s+(?:[a-zA-Z\s,\(\)-]+?)?([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,4})\s+about', desc_clean)
        if match:
            guest = match.group(1).strip()
            # Clean up descriptors
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

        # Pattern 2: "His guest is [descriptor] GUEST. They talk..."
        match = re.search(r'His guest is\s+(?:[a-zA-Z\s,\(\)-]+?)?([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,4})\.', desc_clean)
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

        # Pattern 3: Generic "talks to", "chats with", "interviews"
        match = re.search(r'(?:talks to|chats with|interviews)\s+([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,4})', desc_clean)
        if match:
            return match.group(1).strip()

    # Odd Lots: Multiple patterns
    if 'odd lots' in podcast_lower:
        # Pattern 1: "we speak with GUEST, a..."
        match = re.search(r'we speak with\s+([A-Z][a-zA-Z\'\-\.]+(?:\s+(?:van|de|von|di|da|del)?\s*[A-Z][a-zA-Z\'\-\.]+)+),\s+(?:a|an|the|who)', desc_clean)
        if match:
            return match.group(1).strip()

        # Pattern 2: "Tracy and Joe speak with GUEST"
        match = re.search(r'(?:Tracy and Joe speak with|speak with|talk to|talk with)\s+([A-Z][a-zA-Z\'\-\.]+(?:\s+(?:van|de|von|di|da|del)?[A-Z]?[a-zA-Z\'\-\.]+){1,4})', desc_clean)
        if match:
            return match.group(1).strip()

        # Pattern 3: Job title before name - "Federal Reserve Bank President GUEST"
        # Handles: "Richmond Federal Reserve Bank President Tom Barkin", "Chicago Fed President Austan Goolsbee"
        match = re.search(r'(?:Federal Reserve Bank|Fed|Federal Reserve|San Francisco Fed|Chicago Fed|Richmond Fed|New York Fed)\s+President\s+([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,3})', desc_clean)
        if match:
            return match.group(1).strip()

        # Pattern 4: "In this episode" + guest patterns
        match = re.search(r'In this episode[^\.]+(?:speak with|talk to|talk with)\s+([A-Z][a-zA-Z\'\-\.]+(?:\s+(?:van|de|von|di|da|del)?[A-Z]?[a-zA-Z\'\-\.]+){1,4})', desc_clean)
        if match:
            return match.group(1).strip()

        # Pattern 5: "According to GUEST, ..." (first sentence patterns)
        match = re.search(r'^According to\s+([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,3}),', desc_clean)
        if match:
            return match.group(1).strip()

        # Pattern 6: "GUEST is the/a [profession]" (handles "Zichen Wang is the writer...")
        match = re.search(r'^([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,3})\s+is\s+(?:the|a)\s+', desc_clean)
        if match:
            guest = match.group(1).strip()
            # Filter out obvious non-names
            if not any(x in guest for x in ['The ', 'This ', 'These ', 'That ']):
                return guest

        # Pattern 7: "GUEST has built/is/was..." (handles "Don Wilson has built a career...")
        match = re.search(r'^([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,3})\s+(?:has|is|was)\s+', desc_clean)
        if match:
            guest = match.group(1).strip()
            # Filter carefully - avoid phrases like "Some economists expected"
            if not any(x in guest for x in ['Some ', 'The ', 'This ', 'That ', 'Many ', 'Few ']):
                return guest

        # Pattern 8: "GUEST of [company/org]" (handles "David Johnson of Resolution Financial...")
        match = re.search(r'\s+([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,3})\s+of\s+[A-Z][a-zA-Z\s]+(?:,|\.|\s+)', desc_clean)
        if match:
            guest = match.group(1).strip()
            # Filter out generic phrases
            if len(guest.split()) >= 2 and not any(x in guest for x in ['CEO', 'President', 'director']):
                return guest

    # Chapo Trap House: Multiple patterns
    if 'chapo' in podcast_lower:
        # Pattern 1: "We're joined by GUEST" (handles Unicode names like Aída)
        match = re.search(r"We're joined by\s+(?:[\w\s,\(\)-]+?)?([A-Z][\w\'\-\.]+(?:\s+[A-Z]?[\w\'\-\.]+){1,4})", desc_clean, re.UNICODE)
        if match:
            guest = match.group(1).strip()
            # Clean up - remove trailing " for" or " to"
            guest = re.sub(r'\s+(?:for|to|from)$', '', guest)
            if len(guest.split()) >= 2:
                return guest

        # Pattern 2: "GUEST is back with"
        match = re.search(r'^([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,4})\s+is back with', desc_clean)
        if match:
            return match.group(1).strip()

        # Pattern 3: "Will welcomes [descriptor] GUEST to the show"
        match = re.search(r'Will welcomes\s+(?:[a-zA-Z\s,\(\)-]+?)?([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,4})\s+to the show', desc_clean)
        if match:
            guest = match.group(1).strip()
            if len(guest.split()) >= 2:
                return guest

        # Pattern 4: "[profession] GUEST joins us"
        match = re.search(r'(?:Author|Writer|Journalist|Sports journalist|Professor|Organizer|Comedian)\s+([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,4})\s+joins us', desc_clean)
        if match:
            return match.group(1).strip()

        # Pattern 5: "GUEST returns to the show"
        match = re.search(r'^([A-Z][\w\'\-\.]+(?:\s+[A-Z]?[\w\'\-\.]+){1,4})\s+returns to the show', desc_clean, re.UNICODE)
        if match:
            return match.group(1).strip()

        # Pattern 6: "[profession] GUEST returns to the show"
        match = re.search(r'(?:Author|Writer|Journalist|Professor|Comedian|Tech reporter)\s+([A-Z][\w\'\-\.]+(?:\s+[A-Z]?[\w\'\-\.]+){1,4})\s+returns to the show', desc_clean, re.UNICODE)
        if match:
            return match.group(1).strip()

        # Pattern 7: "[profession] GUEST stops by the pod"
        match = re.search(r'(?:Comedian|Author|Writer|Journalist)\s+([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,4})\s+stops by the pod', desc_clean)
        if match:
            return match.group(1).strip()

        # Pattern 8: "GUEST joins us to discuss" or "GUEST (descriptor) joins us to discuss"
        # Handles: "Blake Masters (NOT THAT ONE, Blake is the creator...) joins us to discuss"
        match = re.search(r'^([A-Z][\w\'\-\.]+(?:\s+[A-Z]?[\w\'\-\.]+){1,4})(?:\s+\([^)]+\))?\s+joins us to discuss', desc_clean, re.UNICODE)
        if match:
            return match.group(1).strip()

        # Pattern 9: "GUEST joins us this week"
        match = re.search(r'^([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,4})\s+joins us this week', desc_clean)
        if match:
            return match.group(1).strip()

        # Pattern 10: "GUEST joins us"
        match = re.search(r'^([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,4})\s+joins us', desc_clean)
        if match:
            return match.group(1).strip()

        # Pattern 11: Title format "BONUS - Name: Title" or "BONUS: Letter for Name"
        # Handles "BONUS - Zohran: The Final Stretch" → Zohran Mamdani (from description)
        if desc_clean:
            match = re.search(r'^([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,4})\s+joins', desc_clean)
            if match:
                return match.group(1).strip()

    # TRUE ANON: Multiple patterns
    if 'true anon' in podcast_lower or 'trueanon' in podcast_lower:
        # Pattern 1: "We're joined by [descriptor] GUEST"
        match = re.search(r"We're joined(?:\s+again)?\s+by\s+(?:[a-zA-Z\s,\(\)-]+?)?([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,4})", desc_clean)
        if match:
            guest = match.group(1).strip()
            # Remove trailing prepositions
            guest = re.sub(r'\s+(?:to|from|of|about)$', '', guest)
            if len(guest.split()) >= 2:
                return guest

        # Pattern 2: "We talk to [descriptor] GUEST"
        match = re.search(r'We talk to\s+(?:[a-zA-Z\s,\(\)-]+?)?([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,4})', desc_clean)
        if match:
            guest = match.group(1).strip()
            guest = re.sub(r'\s+(?:about|to|from)$', '', guest)
            if len(guest.split()) >= 2:
                return guest

        # Pattern 3: "We bring back... GUEST, to talk" or "We bring back... GUEST to talk"
        match = re.search(r'We bring back\s+(?:the\s+)?(?:[a-zA-Z\s,\(\)-]+?)([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,4}),?\s+to talk', desc_clean)
        if match:
            guest = match.group(1).strip()
            if len(guest.split()) >= 2:
                return guest

        # Pattern 4: "An interview with GUEST:"
        match = re.search(r'An interview with\s+([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,4}):', desc_clean)
        if match:
            return match.group(1).strip()

        # Pattern 5: "We welcome back... GUEST"
        match = re.search(r'We welcome back\s+(?:[a-zA-Z\s,\(\)-]+?)?([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,4})', desc_clean)
        if match:
            guest = match.group(1).strip()
            if len(guest.split()) >= 2:
                return guest

        # Pattern 6: "with GUEST, the subject"
        match = re.search(r'with\s+([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,4}),\s+the\s+subject', desc_clean)
        if match:
            return match.group(1).strip()

        # Pattern 6b: "with GUEST to talk" (e.g. "We head to the cave with Daniel Kolitz to talk about...")
        match = re.search(r'with\s+([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,4})\s+to talk', desc_clean)
        if match:
            return match.group(1).strip()

        # Pattern 7: "[profession] GUEST joins us"
        match = re.search(r'(?:Author|Writer|Journalist|Reporter|Correspondent|Activist|Professor)\s+([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,4})\s+joins us', desc_clean)
        if match:
            return match.group(1).strip()

        # Pattern 8: "GUEST joins us to talk"
        match = re.search(r'^([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,4})\s+joins us to talk', desc_clean)
        if match:
            return match.group(1).strip()

        # Pattern 9: "GUEST joins us"
        match = re.search(r'^([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,4})\s+joins us', desc_clean)
        if match:
            return match.group(1).strip()

        # Pattern 10: "GUEST is back" or "with GUEST to"
        match = re.search(r'^([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,4})\s+is back', desc_clean)
        if match:
            return match.group(1).strip()

        # Pattern 11: Title format "GUEST & Topic"
        match = re.search(r'^([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,3})\s+&\s+', desc_clean)
        if match:
            return match.group(1).strip()

    # ENHANCED: Generic patterns (use as fallback for ALL podcasts)
    # These apply AFTER podcast-specific patterns fail
    patterns = [
        # Existing patterns
        r'(?:guest|Guest):\s+([A-Z][\w\'\-\.]+(?:\s+[A-Z]?[\w\'\-\.]+){1,3})',
        r'(?:talks with|speaks with|joined by|interview with|conversation with)\s+([A-Z][\w\'\-\.]+(?:\s+[A-Z]?[\w\'\-\.]+){1,3})',
        r'^([A-Z][\w\'\-\.]+(?:\s+[A-Z]?[\w\'\-\.]+){1,3})\s+(?:joins|discusses|talks about)',

        # NEW: Additional universal patterns from our Chapo/TRUE ANON successes
        r"(?:We're|we're)\s+joined\s+by\s+(?:[\w\s,]+?)?([A-Z][\w\'\-\.]+(?:\s+[A-Z]?[\w\'\-\.]+){1,4})",
        r'(?:We|we)\s+talk\s+to\s+(?:[\w\s,]+?)?([A-Z][\w\'\-\.]+(?:\s+[A-Z]?[\w\'\-\.]+){1,4})',
        r'with\s+([A-Z][\w\'\-\.]+(?:\s+[A-Z]?[\w\'\-\.]+){1,4})\s+(?:to talk|about)',
        r'(?:An|an)\s+interview\s+with\s+([A-Z][\w\'\-\.]+(?:\s+[A-Z]?[\w\'\-\.]+){1,4})',
        r'(?:We|we)\s+welcome\s+(?:[\w\s,]+?)?([A-Z][\w\'\-\.]+(?:\s+[A-Z]?[\w\'\-\.]+){1,4})',
        r'This\s+week:\s+([A-Z][\w\'\-\.]+(?:\s+[A-Z]?[\w\'\-\.]+){1,4})',
    ]

    for pattern in patterns:
        match = re.search(pattern, desc_clean, re.UNICODE)
        if match:
            guest = match.group(1).strip()
            # Clean up trailing prepositions
            guest = re.sub(r'\s+(?:for|to|from|about|of)$', '', guest)
            if len(guest.split()) >= 2:  # Require at least 2 words (reduce false positives)
                return guest

    return None


def clean_guest_name(name):
    """Clean and normalize guest names"""
    if not name:
        return None

    name = re.sub(r'^(?:with\s+|featuring\s+|ft\.?\s+)', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\([^)]*\)', '', name)
    name = re.sub(r'\s+(?:returns?|part\s+\d+|#\d+)$', '', name, flags=re.IGNORECASE)
    name = ' '.join(name.split())

    if len(name) < 3:
        return None

    name_lower = name.lower()

    # Skip generic terms
    skip_terms = ['podcast', 'show', 'episode', 'special', 'bonus', 'trailer', 'live',
                  'coming soon', 'listen now', 'doctors', 'diaries', 'journey', 'corp',
                  'world', 'society', 'institute', 'foundation', 'models', 'research']

    if any(term in name_lower for term in skip_terms):
        return None

    # Skip if starts with question words/articles
    if any(name_lower.startswith(q) for q in ['how ', 'why ', 'what ', 'the ', 'a ', 'an ']):
        return None

    if ' vs ' in name_lower or name[0].isdigit():
        return None

    return name


def extract_guests_with_twitter():
    """Extract guests and Twitter handles from all podcast metadata"""

    metadata_dir = Path("podcast_metadata")
    if not metadata_dir.exists():
        print("❌ podcast_metadata directory not found")
        return

    guests = defaultdict(lambda: {
        'appearances': 0,
        'podcasts': set(),
        'episodes': [],
        'twitter_handles': set(),
        'twitter_from_metadata': False
    })

    total_episodes = 0
    total_extracted = 0
    total_twitter_handles = 0
    total_non_guest_episodes = 0
    non_guest_episodes_by_type = defaultdict(int)
    podcast_stats = {}

    for metadata_file in sorted(metadata_dir.glob("*.json")):
        podcast_name = metadata_file.stem
        print(f"\n📻 Processing: {podcast_name}")

        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)

            episodes = metadata.get('episodes', [])
            episode_count = len(episodes)
            extracted_count = 0
            twitter_count = 0
            non_guest_count = 0

            for episode in episodes:
                title = episode.get('title', '')
                description = episode.get('description', '')
                total_episodes += 1

                # Check if this is a non-guest episode first
                is_non_guest, episode_type = is_non_guest_episode(title, description, podcast_name)

                if is_non_guest:
                    non_guest_count += 1
                    total_non_guest_episodes += 1
                    non_guest_episodes_by_type[episode_type] += 1
                    continue  # Skip guest extraction for non-guest episodes

                # Extract guest from BOTH title and description
                guest_from_desc = extract_guest_from_description(description, podcast_name)
                guest_from_title = extract_guest_from_title(title, podcast_name)

                # For Chapo, prefer title (feat. Guest Name format is highly reliable)
                # For others, prefer description as it's often more complete/accurate
                if 'chapo' in podcast_name.lower():
                    guest_name = guest_from_title if guest_from_title else guest_from_desc
                else:
                    guest_name = guest_from_desc if guest_from_desc else guest_from_title

                # Extract Twitter handles from description and title
                twitter_handles = extract_twitter_handles(title + ' ' + description)

                if guest_name:
                    guest_name = clean_guest_name(guest_name)

                    if guest_name:
                        guests[guest_name]['appearances'] += 1
                        guests[guest_name]['podcasts'].add(podcast_name)
                        guests[guest_name]['episodes'].append({
                            'title': title,
                            'podcast': podcast_name
                        })

                        # Associate Twitter handles with this guest
                        if twitter_handles:
                            for handle in twitter_handles:
                                guests[guest_name]['twitter_handles'].add(handle)
                                guests[guest_name]['twitter_from_metadata'] = True
                            twitter_count += len(twitter_handles)

                        extracted_count += 1
                        total_extracted += 1

            guest_episodes = episode_count - non_guest_count
            extraction_rate = (extracted_count/guest_episodes*100) if guest_episodes > 0 else 0

            # Store stats for later reporting
            podcast_stats[podcast_name] = {
                'total': episode_count,
                'extracted': extracted_count,
                'non_guest': non_guest_count,
                'guest_episodes': guest_episodes,
                'missing': guest_episodes - extracted_count,
                'extraction_rate': extraction_rate
            }

            print(f"  Extracted {extracted_count} guests, {non_guest_count} non-guest episodes ({extraction_rate:.1f}% of guest episodes), {twitter_count} Twitter handles")
            total_twitter_handles += twitter_count

        except Exception as e:
            print(f"  ⚠️  Error: {e}")

    total_guest_episodes = total_episodes - total_non_guest_episodes

    print(f"\n✓ Total: {total_extracted} guest appearances from {total_episodes} episodes")
    print(f"✓ Non-guest episodes: {total_non_guest_episodes} (compilations, trailers, etc.)")
    print(f"✓ Guest episodes: {total_guest_episodes}")
    print(f"✓ Overall extraction rate: {(total_extracted/total_guest_episodes*100) if total_guest_episodes > 0 else 0:.1f}% of guest episodes")
    print(f"✓ Unique guests: {len(guests)}")
    print(f"✓ Twitter handles found: {total_twitter_handles}")

    # Print non-guest episode breakdown
    if total_non_guest_episodes > 0:
        print(f"\n📊 Non-Guest Episode Breakdown:")
        for episode_type, count in sorted(non_guest_episodes_by_type.items(), key=lambda x: x[1], reverse=True):
            print(f"   • {episode_type}: {count} episodes")

    # Print top podcasts with best extraction rates
    print(f"\n📊 Top Extraction Rates (Guest Episodes Only):")
    sorted_podcasts = sorted(podcast_stats.items(), key=lambda x: x[1]['extraction_rate'], reverse=True)
    for podcast_name, stats in sorted_podcasts[:10]:
        if stats['guest_episodes'] > 0:
            print(f"   • {podcast_name}: {stats['extraction_rate']:.1f}% ({stats['extracted']}/{stats['guest_episodes']} guest episodes, {stats['non_guest']} non-guest)")

    # Show podcasts with most missing guest episodes
    print(f"\n📊 Podcasts with Most Missing Guest Episodes:")
    sorted_missing = sorted(podcast_stats.items(), key=lambda x: x[1]['missing'], reverse=True)
    for podcast_name, stats in sorted_missing[:5]:
        if stats['missing'] > 0 and stats['guest_episodes'] > 10:
            print(f"   • {podcast_name}: {stats['missing']} missing ({stats['extraction_rate']:.1f}% of {stats['guest_episodes']} guest episodes)")

    # Convert to list
    guests_list = []
    metadata_twitter_count = 0

    for name, data in guests.items():
        guest_entry = {
            'name': name,
            'appearances': data['appearances'],
            'podcasts': sorted(list(data['podcasts'])),
            'episodes': data['episodes']
        }

        # Add Twitter info if found
        if data['twitter_handles']:
            # If multiple handles, pick most common or first
            handles_list = list(data['twitter_handles'])
            guest_entry['twitter'] = {
                'potential_handles': handles_list,
                'verified': False,
                'from_metadata': True
            }
            metadata_twitter_count += 1

        guests_list.append(guest_entry)

    guests_list.sort(key=lambda x: x['appearances'], reverse=True)

    # Save
    output = {
        'total_guests': len(guests_list),
        'total_episodes': total_episodes,
        'guests_with_twitter_from_metadata': metadata_twitter_count,
        'guests': guests_list
    }

    with open('guest_directory_complete.json', 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n✓ Saved to guest_directory_complete.json")
    print(f"✓ Guests with Twitter handles from metadata: {metadata_twitter_count}")

    # Show some examples
    print(f"\nSample guests with Twitter handles from metadata:")
    count = 0
    for guest in guests_list:
        if guest.get('twitter', {}).get('from_metadata'):
            handles = guest['twitter']['potential_handles']
            print(f"  • {guest['name']}: @{', @'.join(handles)}")
            count += 1
            if count >= 15:
                break


if __name__ == "__main__":
    extract_guests_with_twitter()
