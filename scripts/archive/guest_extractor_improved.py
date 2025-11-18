#!/usr/bin/env python3
"""
Guest Extractor - IMPROVED VERSION
Adds support for more podcast formats
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

    # Adam Friedland Show: "GUEST NAME Talks Topic"
    if 'adam friedland' in podcast_lower or 'friedland' in podcast_lower:
        match = re.match(r'^([A-Z][A-Z\s\'-]+)\s+Talks\s+', title_clean)
        if match:
            guest = match.group(1).strip().title()  # Convert from ALL CAPS
            return guest

    # Odd Lots: "Guest Name on Topic"
    if 'odd lots' in podcast_lower:
        match = re.match(r'^([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+)+)\s+on\s+', title_clean)
        if match:
            guest = match.group(1).strip()
            if not any(x in guest for x in ['Big Take', 'Everybody', 'The ', 'Why ', 'How ', 'Inside ', 'What ']):
                return guest

    # Adam Buxton: "EP.198 - GUEST NAME"
    if 'adam buxton' in podcast_lower:
        match = re.match(r'EP\.\d+\s*-\s*(.+?)(?:\s*@|\s*\d{4}|$)', title_clean, re.IGNORECASE)
        if match:
            guest = match.group(1).strip().title()
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
            if len(guest.split()) >= 2:
                return guest

    # RHLSTP: "RHLSTP 587 - Guest Name"
    if 'rhlstp' in podcast_lower or 'richard herring' in podcast_lower:
        match = re.match(r'RHLSTP\s+(?:Book Club\s+)?\d+\s+-\s+(.+?)(?:\s*\(Part\s+\d+\))?$', title_clean, re.IGNORECASE)
        if match:
            guest = match.group(1).strip()
            if not any(x in guest.lower() for x in ['best of', 'emergency', 'live from']):
                return guest

        # Retro RHLSTP: "Retro RHLSTP 101 - Guest Name"
        match = re.match(r'Retro\s+RHLSTP\s+\d+\s+-\s+(.+?)$', title_clean, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    # Chapo Trap House: "975 - Title feat. Guest Name"
    if 'chapo' in podcast_lower:
        match = re.search(r'feat\.\s+(.+?)(?:\s*\(\d+\))?$', title_clean, re.IGNORECASE)
        if match:
            guest = match.group(1).strip()
            return guest

    # Joshua Citarella: "Doomscroll 31.5: Guest Name" (FIXED - added colon!)
    if 'joshua citarella' in podcast_lower or 'citarella' in podcast_lower:
        match = re.match(r'Doomscroll\s+[\d\.]+:\s+(.+?)$', title_clean, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    # Multipolarity: "Topic With Guest Name"
    if 'multipolarity' in podcast_lower:
        match = re.search(r'\s+With\s+(.+?)$', title_clean, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    # The Loud And Quiet: "Guest Name: topic" or "Guest Name topic"
    if 'loud and quiet' in podcast_lower:
        match = re.match(r'^([A-Z][a-z]+(?:\s+and\s+the\s+[A-Z][a-z]+|\s+[A-Z][a-z]+)+)[\:\s]', title_clean)
        if match:
            return match.group(1).strip()

    # ==== GENERIC PATTERNS (MULTIPLE PODCASTS) ====

    # Pattern: "(w/ Guest Name)" or "(with Guest Name)"
    # Used by: Jimquisition, The Yard, Sad Boyz, etc.
    match = re.search(r'\(w(?:ith)?\/?\s+([^\)]+)\)', title_clean, re.IGNORECASE)
    if match:
        guest = match.group(1).strip()
        # Clean up common suffixes
        guest = re.sub(r'\s*\(\d+\)$', '', guest)  # Remove date
        if len(guest.split()) >= 2 or (len(guest) > 3 and len(guest.split()) == 1):
            return guest

    # Pattern: "ft. Guest Name" or "Ft. Guest Name"
    # Used by: Fear&, 5CAST, etc.
    match = re.search(r'\s+[Ff]t\.?\s+(.+?)(?:\s*\||$)', title_clean)
    if match:
        guest = match.group(1).strip()
        # Remove trailing description markers
        guest = re.sub(r'\s*[-:].*$', '', guest)
        if len(guest) > 3:
            return guest

    # Generic: "Episode ##: Guest Name" (fallback)
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

    # Skip names with 'vs' or very long names with 'and'
    if ' vs ' in name_lower or (len(name) > 30 and ' and ' in name_lower):
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


def extract_guests_from_metadata():
    """Extract guests from all podcast metadata files"""

    metadata_dir = Path("podcast_metadata")
    if not metadata_dir.exists():
        print("❌ podcast_metadata directory not found")
        return

    guests = defaultdict(lambda: {
        'appearances': 0,
        'podcasts': set(),
        'episodes': []
    })

    total_episodes = 0
    total_extracted = 0

    # Process each podcast metadata file
    for metadata_file in sorted(metadata_dir.glob("*.json")):
        podcast_name = metadata_file.stem
        print(f"\n📻 Processing: {podcast_name}")

        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)

            episodes = metadata.get('episodes', [])
            episode_count = len(episodes)
            extracted_count = 0

            for episode in episodes:
                title = episode.get('title', '')
                total_episodes += 1

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

            print(f"  Extracted {extracted_count} guests from {episode_count} episodes ({extracted_count/episode_count*100:.1f}%)")

        except Exception as e:
            print(f"  ⚠️  Error processing {metadata_file.name}: {e}")

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

    with open('guest_directory_improved.json', 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n✓ Saved to guest_directory_improved.json")


if __name__ == "__main__":
    extract_guests_from_metadata()
