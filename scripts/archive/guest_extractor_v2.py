#!/usr/bin/env python3
"""
Guest Extractor V2 - Improved extraction for Odd Lots and other podcasts
"""

import json
import re
from pathlib import Path
from collections import defaultdict


def extract_guest_from_title(title, podcast_name):
    """Extract guest name from episode title based on podcast-specific format"""

    title_clean = title.strip()
    podcast_lower = podcast_name.lower()

    # ==== PODCAST-SPECIFIC PATTERNS ====

    # Odd Lots: "Guest Name on Topic"
    if 'odd lots' in podcast_lower:
        match = re.match(r'^([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+)+)\s+on\s+', title_clean)
        if match:
            guest = match.group(1).strip()
            # Filter out obvious non-names
            if not any(x in guest for x in ['Big Take', 'Everybody', 'The ', 'Why ', 'How ', 'Inside ', 'What ']):
                return guest

    # Adam Buxton: "EP.198 - GUEST NAME" (all caps)
    if 'adam buxton' in podcast_lower:
        match = re.match(r'EP\.\d+\s*-\s*(.+?)(?:\s*@|\s*\d{4}|$)', title_clean, re.IGNORECASE)
        if match:
            guest = match.group(1).strip().title()  # Convert from ALL CAPS to Title Case
            return guest

    # Louis Theroux: "S1 EP1: Guest Name on/discusses..."
    if 'louis theroux' in podcast_lower:
        match = re.match(r'S\d+\s+EP\d+:\s+([^,]+?)\s+(?:on|discusses|talks)', title_clean, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    # Grounded with Louis Theroux: "18. Guest Name"
    if 'grounded' in podcast_lower:
        match = re.match(r'^\d+\.\s+(.+?)$', title_clean)
        if match:
            return match.group(1).strip()

    # I Like Films: "1 Guest Name" or "10 Guest Name"
    if 'i like films' in podcast_lower or 'jonathan ross' in podcast_lower:
        match = re.match(r'^\d+\s+(.+?)$', title_clean)
        if match:
            guest = match.group(1).strip()
            # Must be 2+ words
            if len(guest.split()) >= 2:
                return guest

    # RHLSTP: "RHLSTP 587 - Guest Name"
    if 'rhlstp' in podcast_lower or 'richard herring' in podcast_lower:
        match = re.match(r'RHLSTP\s+(?:Book Club\s+)?\d+\s+-\s+(.+?)(?:\s*\(Part\s+\d+\))?$', title_clean, re.IGNORECASE)
        if match:
            guest = match.group(1).strip()
            # Skip special episodes
            if not any(x in guest.lower() for x in ['best of', 'emergency', 'live from']):
                return guest

        # Retro RHLSTP: "Retro RHLSTP 101 - Guest Name"
        match = re.match(r'Retro\s+RHLSTP\s+\d+\s+-\s+(.+?)$', title_clean, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    # Chapo Trap House: "975 - Title feat. Guest Name"
    if 'chapo' in podcast_lower:
        match = re.search(r'feat\.\s+(.+?)$', title_clean, re.IGNORECASE)
        if match:
            guest = match.group(1).strip()
            # Remove date in parens at end
            guest = re.sub(r'\s*\(\d+\)$', '', guest)
            return guest

    # Joshua Citarella: "Doomscroll 31.5 Guest Name"
    if 'joshua citarella' in podcast_lower or 'citarella' in podcast_lower:
        match = re.match(r'Doomscroll\s+[\d\.]+\s+(.+?)$', title_clean, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    # Multipolarity: "Topic With Guest Name"
    if 'multipolarity' in podcast_lower:
        match = re.search(r'\s+With\s+(.+?)$', title_clean, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    # The Loud And Quiet: "Guest Name topic" (guest name at start, no punctuation)
    if 'loud and quiet' in podcast_lower:
        # Guest name is first 2-3 words, usually possessive or followed by lowercase
        match = re.match(r'^([A-Z][a-z]+(?:\s+and\s+the\s+[A-Z][a-z]+|\s+[A-Z][a-z]+)+)[\'\s]', title_clean)
        if match:
            return match.group(1).strip()

    # ==== GENERIC PATTERNS (FALLBACK) ====

    # Generic: "Episode ##: Guest Name"
    match = re.match(r'^\d+[\.:]?\s+(.+?)$', title_clean)
    if match:
        guest = match.group(1).strip()
        if len(guest.split()) >= 2 and not any(x in guest.lower() for x in ['trailer', 'bonus', 'special', 'episode']):
            return guest

    return None


def clean_guest_name(name):
    """Clean and normalize guest names"""
    if not name:
        return None

    # Remove common prefixes
    name = re.sub(r'^(?:with\s+|featuring\s+|ft\.?\s+)', '', name, flags=re.IGNORECASE)

    # Remove parenthetical info
    name = re.sub(r'\([^)]*\)', '', name)

    # Remove trailing descriptors
    name = re.sub(r'\s+(?:returns?|part\s+\d+|#\d+)$', '', name, flags=re.IGNORECASE)

    # Clean up whitespace
    name = ' '.join(name.split())

    # Skip if too short
    if len(name) < 3:
        return None

    name_lower = name.lower()

    # EXPANDED FALSE POSITIVE FILTERS

    # Skip podcast/show related terms
    podcast_terms = ['podcast', 'show', 'edition', 'teaser', 'beta', 'episode',
                     'special', 'bonus', 'trailer', 'live', 'announcement']
    if any(term in name_lower for term in podcast_terms):
        return None

    # Skip promotional/generic text
    promo_terms = ['coming soon', 'listen now', 'watch now', 'subscribe',
                   'deep research', 'twitter spaces', 'premium', 'exclusive']
    if any(term in name_lower for term in promo_terms):
        return None

    # Skip generic group/concept names
    generic_terms = ['doctors', 'diaries', 'journey', 'dialogues', 'corp',
                     'world', 'society', 'institute', 'foundation', 'roundtable',
                     'models', 'research', 'money', 'take', 'stars', 'earth',
                     'politics', 'memes', 'crendor']
    if any(term in name_lower for term in generic_terms):
        return None

    # Skip names starting with question words or articles
    question_starters = ['how ', 'why ', 'what ', 'when ', 'where ', 'the ', 'a ', 'an ']
    if any(name_lower.startswith(q) for q in question_starters):
        return None

    # Skip names with 'vs' or 'and' (usually topics)
    if ' vs ' in name_lower or ' and ' in name_lower:
        # Exception: normal names like "John and Mary" are OK if short
        if len(name) > 30:
            return None

    # Skip if starts with a number
    if name[0].isdigit():
        return None

    # Skip episode-like patterns
    episode_patterns = [
        r'^The .+ (Truth|Story|Tale|Case|Mystery)',
        r' feat\.',
        r'Gets (Whacked|Trapped)',
        r'(Fighting|Saving|Killing|Making)',
    ]

    for pattern in episode_patterns:
        if re.search(pattern, name, re.IGNORECASE):
            return None

    return name


def extract_guests_from_episodes():
    """Extract guests from all downloaded episodes"""

    episodes_dir = Path("episodes")
    if not episodes_dir.exists():
        print("❌ Episodes directory not found")
        return

    guests = defaultdict(lambda: {
        'appearances': 0,
        'podcasts': set(),
        'episodes': []
    })

    total_episodes = 0
    total_extracted = 0

    # Process each podcast
    for podcast_dir in sorted(episodes_dir.iterdir()):
        if not podcast_dir.is_dir():
            continue

        podcast_name = podcast_dir.name
        print(f"\n📻 Processing: {podcast_name}")

        episode_count = 0
        extracted_count = 0

        # Process each episode JSON file
        for episode_file in podcast_dir.glob("*.json"):
            try:
                with open(episode_file, 'r') as f:
                    episode_data = json.load(f)

                title = episode_data.get('title', '')
                total_episodes += 1
                episode_count += 1

                # Extract guest name
                guest_name = extract_guest_from_title(title, podcast_name)

                if guest_name:
                    # Clean the name
                    guest_name = clean_guest_name(guest_name)

                    if guest_name:
                        guests[guest_name]['appearances'] += 1
                        guests[guest_name]['podcasts'].add(podcast_name)
                        guests[guest_name]['episodes'].append({
                            'title': title,
                            'podcast': podcast_name
                        })
                        extracted_count += 1
                        total_extracted += 1

            except Exception as e:
                print(f"  ⚠️  Error processing {episode_file.name}: {e}")

        print(f"  Extracted {extracted_count} guests from {episode_count} episodes")

    print(f"\n✓ Total: Extracted {total_extracted} guest appearances from {total_episodes} episodes")
    print(f"✓ Unique guests: {len(guests)}")

    # Convert to list format
    guests_list = []
    for name, data in guests.items():
        guests_list.append({
            'name': name,
            'appearances': data['appearances'],
            'podcasts': sorted(list(data['podcasts'])),
            'episodes': data['episodes']
        })

    # Sort by appearances
    guests_list.sort(key=lambda x: x['appearances'], reverse=True)

    # Save to file
    output = {
        'total_guests': len(guests_list),
        'total_episodes': total_episodes,
        'guests': guests_list
    }

    with open('guest_directory_v2.json', 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n✓ Saved to guest_directory_v2.json")

    # Show top 20
    print(f"\nTop 20 guests by appearances:")
    for i, guest in enumerate(guests_list[:20], 1):
        podcasts = ', '.join(guest['podcasts'][:2])
        print(f"  {i}. {guest['name']} ({guest['appearances']} appearances) - {podcasts}")


if __name__ == "__main__":
    extract_guests_from_episodes()
