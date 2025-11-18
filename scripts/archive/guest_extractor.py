#!/usr/bin/env python3
"""
Guest Extractor & Twitter Finder
Extracts guest names from podcast metadata and finds their Twitter/X accounts
"""

import json
import re
from pathlib import Path
from collections import defaultdict
import time


def extract_guest_from_title(title, podcast_name):
    """Extract guest name from episode title based on podcast format"""

    # Remove common prefixes
    title_clean = title.strip()

    # Pattern 1: "S6 EP5: Guest Name on/discusses/talks..."
    # Used by: Louis Theroux, Grounded
    match = re.match(r'S\d+\s+EP\d+:\s+([^,]+?)\s+(?:on|discusses|talks|reveals|shares|reflects)', title_clean, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # Pattern 2: "RHLSTP 587 - Guest Name"
    # Used by: RHLSTP
    match = re.match(r'RHLSTP\s+(?:Book Club\s+)?\d+\s+-\s+(.+?)$', title_clean, re.IGNORECASE)
    if match:
        guest = match.group(1).strip()
        # Skip if it's a special episode
        if not any(x in guest.lower() for x in ['retro', 'sports bar', 'emergency', 'live']):
            return guest

    # Pattern 3: "Episode Number: Guest Name"
    # Used by: I Like Films, some others
    match = re.match(r'^\d+[:]?\s+(.+?)$', title_clean)
    if match:
        guest = match.group(1).strip()
        # Filter out non-guest episodes
        if len(guest.split()) >= 2 and not any(x in guest.lower() for x in ['trailer', 'bonus', 'special']):
            return guest

    # Pattern 4: "Guest Name - Topic" or "Guest Name:"
    match = re.match(r'^([A-Z][a-zA-Z\s\'-]+(?:\s+[A-Z][a-zA-Z\s\'-]+)*)\s*[-:]', title_clean)
    if match:
        guest = match.group(1).strip()
        if len(guest.split()) >= 2:
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

    # Skip names with prepositions (usually concepts not people)
    prepositions = [' of ', ' in ', ' on ', ' at ', ' to ', ' for ', ' as ', ' by ']
    if any(prep in f' {name_lower} ' for prep in prepositions):
        return None

    # Skip extremely long names (likely episode titles)
    if len(name) > 60:
        return None

    # Skip names with trailing punctuation (malformed extractions)
    if name.endswith(('-', ':', ',', '.')):
        return None

    # Skip names that start with "- " (episode titles with featured guests)
    if name.startswith('- '):
        return None

    # Skip episode-like patterns
    episode_patterns = [
        r'^The .+ (Truth|Story|Tale|Case|Mystery)',  # "The Dark Truth about..."
        r'^How (a|to|the)',  # "How a Method Actor..."
        r'^(Premier|Arsenal|Women)',  # Podcast-specific episodes
        r'Horizons$',  # "Blockchain Horizons"
        r' feat\.',  # "feat." indicates episode with guest
        r'^Tokenizing',  # Crypto episode titles
        r'Gets Whacked$',  # Episode titles
        r'preview pod$',  # Podcast episode descriptions
    ]
    for pattern in episode_patterns:
        if re.search(pattern, name, re.IGNORECASE):
            return None

    # Skip things that start with "The" + generic noun (likely not a person)
    if re.match(r'^the\s+(?![\w]+\s+[\w]+)', name_lower):
        # Allow "The Rock" or "The Weeknd" (stage names) but not "The Podcast"
        if not re.match(r'^the\s+\w+$', name_lower):
            return None

    # Skip single words unless it's a known mononym format
    word_count = len(name.split())
    if word_count == 1:
        # Allow if it looks like a stage name (capitalized, 4+ chars)
        if not (name[0].isupper() and len(name) >= 4 and name.isalpha()):
            return None

    # Skip all-caps names (usually acronyms or show segments)
    if name.isupper() and len(name.split()) > 1:
        return None

    # Require at least one capital letter (proper name)
    if not any(c.isupper() for c in name):
        return None

    # Skip names with too many special characters (likely not a person)
    special_char_count = sum(1 for c in name if not c.isalnum() and c != ' ' and c != '-' and c != "'")
    if special_char_count > 2:
        return None

    return name


def extract_all_guests(metadata_dir="podcast_metadata"):
    """Extract all guests from all podcast metadata files"""

    metadata_path = Path(metadata_dir)
    all_guests = defaultdict(lambda: {
        'podcasts': [],
        'episodes': [],
        'first_appearance': None
    })

    # Process each podcast metadata file
    for metadata_file in sorted(metadata_path.glob("*.json")):
        try:
            with open(metadata_file, 'r') as f:
                data = json.load(f)

            podcast_name = data.get('podcast_title', metadata_file.stem)
            print(f"Processing: {podcast_name}")

            for episode in data.get('episodes', []):
                title = episode.get('title', '')
                published = episode.get('published', '')

                # Extract guest name
                guest = extract_guest_from_title(title, podcast_name)
                guest = clean_guest_name(guest)

                if guest:
                    # Normalize for deduplication
                    guest_key = guest.lower()

                    # Store appearance
                    all_guests[guest_key]['podcasts'].append(podcast_name)
                    all_guests[guest_key]['episodes'].append({
                        'podcast': podcast_name,
                        'episode_title': title,
                        'published': published
                    })

                    # Track first appearance
                    if not all_guests[guest_key]['first_appearance']:
                        all_guests[guest_key]['first_appearance'] = guest

        except Exception as e:
            print(f"  ✗ Error processing {metadata_file.name}: {e}")
            continue

    # Convert to final format
    guests_list = []
    for guest_key, info in all_guests.items():
        guests_list.append({
            'name': info['first_appearance'],
            'appearances': len(info['episodes']),
            'podcasts': list(set(info['podcasts'])),
            'episodes': info['episodes']
        })

    # Sort by number of appearances
    guests_list.sort(key=lambda x: x['appearances'], reverse=True)

    return guests_list


def search_twitter_handle(guest_name):
    """
    Search for Twitter/X handle for a guest
    Returns potential Twitter handle or None
    """
    # Clean the name for search
    search_name = guest_name.strip()

    # Common patterns for Twitter handles
    # This is a placeholder - in production you'd use Twitter API or web scraping
    # For now, we'll just format the name as a potential handle

    # Convert to potential handle format
    parts = search_name.split()

    # Strategy 1: FirstnameLastname
    potential_handles = []
    if len(parts) >= 2:
        potential_handles.append(f"@{''.join(parts[:2])}")
        potential_handles.append(f"@{parts[0]}{parts[-1]}")
    elif len(parts) == 1:
        potential_handles.append(f"@{parts[0]}")

    # Strategy 2: Firstname_Lastname
    if len(parts) >= 2:
        potential_handles.append(f"@{parts[0]}_{parts[-1]}")

    # Strategy 3: FirstInitialLastname
    if len(parts) >= 2:
        potential_handles.append(f"@{parts[0][0]}{parts[-1]}")

    return {
        'potential_handles': potential_handles,
        'needs_verification': True,
        'search_query': f"{search_name} twitter"
    }


def generate_guest_directory(output_file="guest_directory.json"):
    """Generate complete guest directory with Twitter info"""

    print("=" * 80)
    print("EXTRACTING GUESTS FROM PODCAST METADATA")
    print("=" * 80)
    print()

    # Extract all guests
    guests = extract_all_guests()

    print()
    print(f"✓ Found {len(guests)} unique guests")
    print()

    # Add Twitter lookup for top guests
    print("=" * 80)
    print("GENERATING TWITTER HANDLES (Top 100)")
    print("=" * 80)
    print()

    for i, guest in enumerate(guests[:100]):  # Top 100 guests
        guest['twitter'] = search_twitter_handle(guest['name'])
        if (i + 1) % 20 == 0:
            print(f"  Processed {i + 1}/100 guests...")

    # Save to JSON
    output_path = Path(output_file)
    with open(output_path, 'w') as f:
        json.dump({
            'total_guests': len(guests),
            'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'guests': guests
        }, f, indent=2)

    print()
    print(f"✓ Guest directory saved to: {output_path}")

    # Generate summary report
    print()
    print("=" * 80)
    print("GUEST DIRECTORY SUMMARY")
    print("=" * 80)
    print()
    print(f"Total unique guests: {len(guests)}")
    print()
    print("Top 20 most frequent guests:")
    print("-" * 80)
    for i, guest in enumerate(guests[:20], 1):
        podcasts_str = ", ".join(guest['podcasts'][:2])
        if len(guest['podcasts']) > 2:
            podcasts_str += f" +{len(guest['podcasts'])-2} more"
        print(f"{i:2}. {guest['name']:<30} ({guest['appearances']} appearances on {podcasts_str})")

    print()
    print(f"Full guest directory with Twitter handles: {output_path}")

    return guests


def main():
    """Main function"""
    guests = generate_guest_directory()

    # Also create a simple CSV for easy viewing
    csv_path = Path("guest_directory.csv")
    with open(csv_path, 'w') as f:
        f.write("Name,Appearances,Podcasts,Potential Twitter Handles\n")
        for guest in guests[:200]:  # Top 200
            podcasts = "; ".join(guest['podcasts'][:3])
            handles = "; ".join(guest.get('twitter', {}).get('potential_handles', [])[:3])
            f.write(f'"{guest["name"]}",{guest["appearances"]},"{podcasts}","{handles}"\n')

    print(f"✓ CSV export: {csv_path}")


if __name__ == "__main__":
    main()
