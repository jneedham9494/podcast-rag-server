#!/usr/bin/env python3
"""
Universal Guest Extractor
Applies ALL successful patterns to ALL podcasts (no podcast-specific rules)
"""

import json
import re
from pathlib import Path
from collections import defaultdict


def is_non_guest_episode(title, description, podcast_name):
    """Universal non-guest episode detection"""
    title_lower = title.lower()
    desc_lower = description.lower() if description else ""

    # Compilation/Best of episodes
    if any(pattern in title_lower for pattern in [
        'best of', 'highlights', 'compilation', 'emergency questions'
    ]):
        return (True, "compilation")

    # Trailers/announcements
    if any(pattern in title_lower for pattern in [
        'trailer', 'teaser', 'coming soon', 'announcement'
    ]):
        return (True, "trailer")

    # AMA/Q&A episodes
    if any(pattern in title_lower for pattern in ['ama', 'q&a', 'ask me anything']):
        return (True, "ama")

    # Roundup episodes
    if 'roundup' in title_lower or 'round-up' in title_lower:
        return (True, "roundup")

    return (False, None)


def extract_guest_from_title(title, podcast_name):
    """Universal title extraction"""
    if not title:
        return None

    title_clean = title.strip()

    # PATTERN 1: "(w/ Guest Name)" or "(with Guest Name)"
    match = re.search(r'\(w(?:ith)?\/?\s+([^\)]+)\)', title_clean, re.IGNORECASE)
    if match:
        guest = match.group(1).strip()
        guest = re.sub(r'\s*\(\d+\)$', '', guest)
        if len(guest.split()) >= 2 or (len(guest) > 3 and len(guest.split()) == 1):
            return guest

    # PATTERN 2: "feat. Guest Name" or "ft. Guest Name"
    match = re.search(r'[Ff]eat?\.\s+(.+?)(?:\s*\([\d/]+\))?$', title_clean)
    if match:
        guest = match.group(1).strip()
        if any(x in guest for x in [' to ', ' the ', ' Up A ', ' of the ']):
            return None
        return guest

    # PATTERN 3: "Episode #: Guest Name"
    match = re.match(r'^(?:Ep(?:isode)?|E)\s*\d+:\s+(.+?)$', title_clean, re.IGNORECASE)
    if match:
        guest = match.group(1).strip()
        if len(guest.split()) >= 2:
            return guest

    return None


def extract_guest_from_description(description, podcast_name):
    """Universal description extraction"""
    if not description:
        return None

    desc_clean = re.sub(r'<[^>]+>', '', description)
    desc_clean = re.sub(r'[\u200b-\u200f\u202a-\u202e]', '', desc_clean)

    # PATTERN 1: "We're joined by GUEST"
    match = re.search(r"We're joined(?:\s+again)?\s+by\s+(?:[\w\s,\(\)-]+?)?([A-Z][\w\'\-\.]+(?:\s+[A-Z]?[\w\'\-\.]+){1,4})", desc_clean, re.UNICODE)
    if match:
        guest = match.group(1).strip()
        guest = re.sub(r'\s+(?:for|to|from|of|about)$', '', guest)
        if len(guest.split()) >= 2:
            return guest

    # PATTERN 2: "We talk to GUEST"
    match = re.search(r'We talk to\s+(?:[\w\s,\(\)-]+?)?([A-Z][\w\'\-\.]+(?:\s+[A-Z]?[\w\'\-\.]+){1,4})', desc_clean, re.UNICODE)
    if match:
        guest = match.group(1).strip()
        guest = re.sub(r'\s+(?:about|to|from)$', '', guest)
        if len(guest.split()) >= 2:
            return guest

    # PATTERN 3: "with GUEST to talk"
    match = re.search(r'with\s+([A-Z][\w\'\-\.]+(?:\s+[A-Z]?[\w\'\-\.]+){1,4})\s+to talk', desc_clean, re.UNICODE)
    if match:
        return match.group(1).strip()

    # PATTERN 4: "GUEST joins us"
    match = re.search(r'^([A-Z][\w\'\-\.]+(?:\s+[A-Z]?[\w\'\-\.]+){1,4})\s+joins us', desc_clean, re.UNICODE)
    if match:
        return match.group(1).strip()

    # PATTERN 5: "[profession] GUEST joins us"
    match = re.search(r'(?:Author|Writer|Journalist|Reporter|Correspondent|Activist|Professor|Comedian|Tech reporter|Sports journalist)\s+([A-Z][\w\'\-\.]+(?:\s+[A-Z]?[\w\'\-\.]+){1,4})\s+joins us', desc_clean, re.UNICODE)
    if match:
        return match.group(1).strip()

    # PATTERN 6: "GUEST is back"
    match = re.search(r'^([A-Z][\w\'\-\.]+(?:\s+[A-Z]?[\w\'\-\.]+){1,4})\s+is back', desc_clean, re.UNICODE)
    if match:
        return match.group(1).strip()

    # PATTERN 7: "GUEST returns to the show"
    match = re.search(r'^([A-Z][\w\'\-\.]+(?:\s+[A-Z]?[\w\'\-\.]+){1,4})\s+returns to the show', desc_clean, re.UNICODE)
    if match:
        return match.group(1).strip()

    # PATTERN 8: "GUEST joins us to discuss"
    match = re.search(r'^([A-Z][\w\'\-\.]+(?:\s+[A-Z]?[\w\'\-\.]+){1,4})(?:\s+\([^)]+\))?\s+joins us to discuss', desc_clean, re.UNICODE)
    if match:
        return match.group(1).strip()

    # PATTERN 9: "We bring back GUEST"
    match = re.search(r'We bring back\s+(?:[\w\s,\(\)-]+?)([A-Z][\w\'\-\.]+(?:\s+[A-Z]?[\w\'\-\.]+){1,4}),?\s+to', desc_clean, re.UNICODE)
    if match:
        guest = match.group(1).strip()
        if len(guest.split()) >= 2:
            return guest

    # PATTERN 10: "We welcome GUEST" or "welcomes GUEST"
    match = re.search(r'(?:We welcome|welcomes)\s+(?:[\w\s,\(\)-]+?)?([A-Z][\w\'\-\.]+(?:\s+[A-Z]?[\w\'\-\.]+){1,4})\s+to', desc_clean, re.UNICODE)
    if match:
        guest = match.group(1).strip()
        if len(guest.split()) >= 2:
            return guest

    # PATTERN 11: "An interview with GUEST"
    match = re.search(r'An interview with\s+([A-Z][\w\'\-\.]+(?:\s+[A-Z]?[\w\'\-\.]+){1,4})', desc_clean, re.UNICODE)
    if match:
        return match.group(1).strip()

    # PATTERN 12: "talks with GUEST"
    match = re.search(r'talks with\s+(?:[\w\s,\(\)-]+?)?([A-Z][\w\'\-\.]+(?:\s+[A-Z]?[\w\'\-\.]+){1,4})', desc_clean, re.UNICODE)
    if match:
        guest = match.group(1).strip()
        if len(guest.split()) >= 2:
            return guest

    return None


def extract_twitter_handles(text):
    """Extract Twitter handles"""
    handles = re.findall(r'@([A-Za-z0-9_]{1,15})\b', text)
    filtered = []
    blacklist = ['googlemail', 'gmail', 'email', 'twitter', 'instagram', 'facebook']
    for handle in handles:
        if handle.lower() not in blacklist and not handle.isdigit():
            filtered.append(handle)
    return filtered


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
    skip_terms = ['podcast', 'show', 'episode', 'special', 'bonus', 'trailer', 'live',
                  'coming soon', 'listen now', 'doctors', 'diaries', 'journey', 'corp',
                  'world', 'society', 'institute', 'foundation', 'models', 'research']

    if any(term in name_lower for term in skip_terms):
        return None

    if any(name_lower.startswith(q) for q in ['how ', 'why ', 'what ', 'the ', 'a ', 'an ']):
        return None

    if ' vs ' in name_lower or name[0].isdigit():
        return None

    return name


def extract_guests_universal():
    """Extract guests using universal patterns"""
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

    total_extracted = 0
    total_episodes = 0
    total_non_guest_episodes = 0

    print("\n🔄 UNIVERSAL PATTERN EXTRACTION")
    print("=" * 80)
    print("Applying ALL successful patterns to ALL podcasts\n")

    for metadata_file in sorted(metadata_dir.glob("*.json")):
        podcast_name = metadata_file.stem
        print(f"\n📻 Processing: {podcast_name}")

        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)

            episodes = metadata.get('episodes', [])
            extracted_count = 0
            non_guest_count = 0

            for episode in episodes:
                title = episode.get('title', '')
                description = episode.get('description', '')
                total_episodes += 1

                is_non_guest, episode_type = is_non_guest_episode(title, description, podcast_name)
                if is_non_guest:
                    non_guest_count += 1
                    total_non_guest_episodes += 1
                    continue

                guest_from_desc = extract_guest_from_description(description, podcast_name)
                guest_from_title = extract_guest_from_title(title, podcast_name)
                guest_name = guest_from_desc if guest_from_desc else guest_from_title

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

                        if twitter_handles:
                            for handle in twitter_handles:
                                guests[guest_name]['twitter_handles'].add(handle)
                            guests[guest_name]['twitter_from_metadata'] = True

                        extracted_count += 1
                        total_extracted += 1

            guest_episodes = len(episodes) - non_guest_count
            rate = (extracted_count / guest_episodes * 100) if guest_episodes > 0 else 0
            print(f"  Extracted {extracted_count} guests ({rate:.1f}%)")

        except Exception as e:
            print(f"  ❌ Error: {e}")

    # Save results
    output = {
        'total_guests': len(guests),
        'total_episodes': total_episodes,
        'guests': []
    }

    for guest_name, data in sorted(guests.items()):
        output['guests'].append({
            'name': guest_name,
            'appearances': data['appearances'],
            'podcasts': sorted(list(data['podcasts'])),
            'episodes': data['episodes'],
            'twitter_handles': sorted(list(data['twitter_handles']))
        })

    with open('guest_directory_UNIVERSAL.json', 'w') as f:
        json.dump(output, f, indent=2)

    print("\n" + "=" * 80)
    print(f"✓ Total: {total_extracted} guest appearances")
    print(f"✓ Unique guests: {len(guests)}")
    print(f"✓ Overall rate: {(total_extracted / (total_episodes - total_non_guest_episodes) * 100):.1f}%")
    print(f"\n✓ Saved to guest_directory_UNIVERSAL.json")


if __name__ == "__main__":
    extract_guests_universal()
