"""
Host detection utilities for podcast transcripts.
"""

import subprocess
from collections import Counter
from typing import Dict, List

from .json_utils import parse_json_safely


def detect_hosts_from_intro(text: str, model: str = "llama3:8b") -> Dict:
    """
    Dynamically detect podcast hosts from the episode intro.

    Args:
        text: Transcript text
        model: Ollama model to use

    Returns:
        Dictionary with hosts, producer, podcast_name
    """
    # Get first ~3000 chars (intro section)
    intro = text[:3000]

    prompt = f"""Analyze this podcast intro and extract the hosts' names.

Look for phrases like:
- "My name is X" or "I'm X"
- "joined by X" or "with me is X"
- "This is X and Y"
- "your hosts X and Y"

Intro transcript:
{intro}

Based on the intro above, identify the actual names mentioned. If you cannot find specific names, return an empty hosts array.

Return ONLY valid JSON with no extra text:
{{"podcast_name": "name or null", "hosts": ["FirstName LastName", "FirstName LastName"], "producer": "name or null"}}

JSON:"""

    try:
        result = subprocess.run(
            ['ollama', 'run', model],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=60
        )

        response = result.stdout.strip()
        detected = parse_json_safely(response, default={})

        # Validate that hosts are actual names, not placeholders
        if detected.get('hosts'):
            valid_hosts = []
            for host in detected['hosts']:
                # Skip placeholders and generic values
                if host and isinstance(host, str):
                    host_lower = host.lower()
                    placeholders = [
                        'name1', 'name2', 'firstname', 'lastname',
                        'host', 'unknown'
                    ]
                    if not any(p in host_lower for p in placeholders):
                        valid_hosts.append(host)
            detected['hosts'] = valid_hosts

        return detected if detected else {}

    except Exception as e:
        print(f"  WARNING: Host detection failed: {e}")

    return {}


def detect_hosts_from_entities(entities: Dict, text: str) -> List[str]:
    """
    Fallback: detect likely hosts from most frequently mentioned people.

    Args:
        entities: Dictionary with 'people' key
        text: Full transcript text

    Returns:
        List of likely host names
    """
    if not entities.get('people'):
        return []

    # Negative filter: Common non-host names
    NON_HOST_PATTERNS = [
        # US Politicians
        'trump', 'biden', 'obama', 'clinton', 'bush', 'reagan', 'nixon',
        'kennedy', 'pelosi', 'schumer', 'mcconnell', 'harris', 'pence',
        'cheney', 'rumsfeld', 'pompeo', 'blinken', 'sanders', 'warren',
        'aoc', 'ocasio',
        # International figures
        'putin', 'xi', 'netanyahu', 'zelensky', 'saddam', 'hussein',
        'castro', 'kim jong', 'bin laden', 'gaddafi', 'assad', 'khamenei',
        # Historical figures
        'hitler', 'stalin', 'mao', 'churchill', 'fdr', 'lincoln',
        'washington', 'jefferson', 'napoleon', 'caesar', 'marx', 'lenin',
        # Media/celebrities often discussed
        'musk', 'bezos', 'zuckerberg', 'jobs', 'gates', 'epstein',
        'maxwell', 'weinstein', 'cosby',
        # Common false positives
        'god', 'jesus', 'christ', 'allah', 'buddha',
    ]

    # Count occurrences of each person in the text
    person_counts = Counter()
    text_lower = text.lower()

    for person in entities['people']:
        # Skip single-character or very short names
        if len(person) < 3:
            continue

        # Skip names that are clearly not hosts
        person_lower = person.lower()
        if any(pattern in person_lower for pattern in NON_HOST_PATTERNS):
            continue

        # Count occurrences (case-insensitive)
        count = text_lower.count(person_lower)
        if count > 0:
            # Boost score for full names (2+ words)
            words = person.split()
            if len(words) >= 2:
                count = int(count * 1.5)
            person_counts[person] = count

    # Get top candidates
    top_people = person_counts.most_common(5)

    # Filter: hosts are usually mentioned many times
    if not top_people:
        return []

    max_count = top_people[0][1]
    threshold = max_count * 0.3  # At least 30% as frequent as most mentioned

    likely_hosts = [
        person for person, count in top_people
        if count >= threshold and count >= 5  # Minimum 5 mentions
    ]

    return likely_hosts[:3]  # Maximum 3 hosts
