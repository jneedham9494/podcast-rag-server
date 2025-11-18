#!/usr/bin/env python3
"""
ALL PATTERNS ON ALL PODCASTS
Removes podcast-specific checks - tries EVERY pattern on EVERY podcast
"""

import json
import re
from pathlib import Path
from collections import defaultdict

def is_non_guest_episode(title, description, podcast_name):
    """Universal non-guest detection"""
    title_lower = title.lower()
    
    if any(p in title_lower for p in ['best of', 'compilation', 'trailer', 'teaser', 'ama', 'q&a', 'roundup']):
        return (True, "non_guest")
    return (False, None)

def extract_guest_from_title(title, podcast_name):
    """Try ALL title patterns on ALL podcasts"""
    if not title:
        return None
    
    title_clean = title.strip()
    
    # RHLSTP pattern (try on ALL podcasts)
    match = re.match(r'^#?(\d+)\s+(.+?)$', title_clean)
    if match:
        guest = match.group(2).strip()
        if len(guest.split()) >= 2:
            return guest
    
    # Adam Buxton pattern (try on ALL podcasts)
    match = re.match(r'^Ep(?:isode)?\s*\d+:\s+(.+?)$', title_clean, re.IGNORECASE)
    if match:
        guest = match.group(1).strip()
        if len(guest.split()) >= 2:
            return guest
    
    # Joshua Citarella patterns (try on ALL podcasts)
    match = re.match(r'Doomscroll\s+[\d\.]+:\s+(.+?)$', title_clean)
    if match:
        return match.group(1).strip()
    
    match = re.search(r'\s+w/\s+([A-Z][\w\'\-\.]+(?:\s+[A-Z][\w\'\-\.]+)+)', title_clean)
    if match:
        guest = match.group(1).strip()
        if len(guest.split()) >= 2:
            return guest
    
    # Chapo pattern (try on ALL podcasts)
    match = re.search(r'[Ff]eat?\.\s+(.+?)(?:\s*\([\d/]+\))?$', title_clean)
    if match:
        guest = match.group(1).strip()
        if ' to ' not in guest and ' the ' not in guest:
            return guest
    
    # Generic patterns
    match = re.search(r'\(w(?:ith)?\/?\s+([^\)]+)\)', title_clean, re.IGNORECASE)
    if match:
        guest = match.group(1).strip()
        if len(guest.split()) >= 2:
            return guest
    
    return None

def extract_guest_from_description(description, podcast_name):
    """Try ALL description patterns on ALL podcasts"""
    if not description:
        return None
    
    desc_clean = re.sub(r'<[^>]+>', '', description)
    desc_clean = re.sub(r'[\u200b-\u200f\u202a-\u202e]', '', desc_clean)
    
    # ALL Podcast Patterns (no if checks!)
    
    # Adam Buxton patterns
    match = re.search(r'(?:Adam|Host)\s+talks with\s+(?:[\w\s,\(\)-]+?)?([A-Z][\w\'\-\.]+(?:\s+[A-Z]?[\w\'\-\.]+){1,4})', desc_clean, re.UNICODE)
    if match:
        guest = match.group(1).strip()
        if len(guest.split()) >= 2:
            return guest
    
    # Odd Lots patterns
    match = re.search(r'(?:Federal Reserve|Fed|Chicago Fed|San Francisco Fed)\s+President\s+([A-Z][\w\'\-\.]+(?:\s+[A-Z][\w\'\-\.]+){1,3})', desc_clean)
    if match:
        return match.group(1).strip()
    
    match = re.search(r'^([A-Z][\w\'\-\.]+(?:\s+[A-Z][\w\'\-\.]+){1,3})\s+is\s+(?:the|a)\s+', desc_clean, re.UNICODE)
    if match:
        guest = match.group(1).strip()
        if 'The ' not in guest and 'This ' not in guest:
            return guest
    
    # Chapo/TRUE ANON patterns
    match = re.search(r"We're joined(?:\s+again)?\s+by\s+(?:[\w\s,\(\)-]+?)?([A-Z][\w\'\-\.]+(?:\s+[A-Z]?[\w\'\-\.]+){1,4})", desc_clean, re.UNICODE)
    if match:
        guest = match.group(1).strip()
        guest = re.sub(r'\s+(?:for|to|from|of|about)$', '', guest)
        if len(guest.split()) >= 2:
            return guest
    
    match = re.search(r'We talk to\s+(?:[\w\s,\(\)-]+?)?([A-Z][\w\'\-\.]+(?:\s+[A-Z]?[\w\'\-\.]+){1,4})', desc_clean, re.UNICODE)
    if match:
        guest = match.group(1).strip()
        guest = re.sub(r'\s+(?:about|to|from)$', '', guest)
        if len(guest.split()) >= 2:
            return guest
    
    match = re.search(r'with\s+([A-Z][\w\'\-\.]+(?:\s+[A-Z]?[\w\'\-\.]+){1,4})\s+to talk', desc_clean, re.UNICODE)
    if match:
        return match.group(1).strip()
    
    match = re.search(r'^([A-Z][\w\'\-\.]+(?:\s+[A-Z]?[\w\'\-\.]+){1,4})\s+joins us', desc_clean, re.UNICODE)
    if match:
        return match.group(1).strip()
    
    match = re.search(r'^([A-Z][\w\'\-\.]+(?:\s+[A-Z]?[\w\'\-\.]+){1,4})\s+returns to the show', desc_clean, re.UNICODE)
    if match:
        return match.group(1).strip()
    
    match = re.search(r'(?:An|an)\s+interview\s+with\s+([A-Z][\w\'\-\.]+(?:\s+[A-Z]?[\w\'\-\.]+){1,4})', desc_clean, re.UNICODE)
    if match:
        return match.group(1).strip()
    
    return None

def clean_guest_name(name):
    """Clean guest names"""
    if not name or len(name) < 3:
        return None
    
    name = re.sub(r'\([^)]*\)', '', name)
    name = ' '.join(name.split())
    
    skip_terms = ['podcast', 'show', 'episode', 'special', 'bonus', 'trailer']
    if any(term in name.lower() for term in skip_terms):
        return None
    
    if any(name.lower().startswith(q) for q in ['how ', 'why ', 'what ', 'the ', 'a ']):
        return None
    
    return name

def extract_all_patterns_all_podcasts():
    """Extract with ALL patterns on ALL podcasts"""
    metadata_dir = Path("podcast_metadata")
    
    guests = defaultdict(lambda: {
        'appearances': 0,
        'podcasts': set(),
        'episodes': []
    })
    
    total_extracted = 0
    total_episodes = 0
    
    print("\n🔄 ALL PATTERNS ON ALL PODCASTS")
    print("=" * 80)
    print("Testing if podcast-specific patterns work on other podcasts\n")
    
    for metadata_file in sorted(metadata_dir.glob("*.json")):
        podcast_name = metadata_file.stem
        
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            episodes = metadata.get('episodes', [])
            extracted_count = 0
            
            for episode in episodes:
                title = episode.get('title', '')
                description = episode.get('description', '')
                total_episodes += 1
                
                is_non_guest, _ = is_non_guest_episode(title, description, podcast_name)
                if is_non_guest:
                    continue
                
                # Try BOTH title and description
                guest_from_desc = extract_guest_from_description(description, podcast_name)
                guest_from_title = extract_guest_from_title(title, podcast_name)
                guest_name = guest_from_desc if guest_from_desc else guest_from_title
                
                if guest_name:
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
            
            print(f"📻 {podcast_name}: {extracted_count} guests")
            
        except Exception as e:
            print(f"❌ {podcast_name}: Error - {e}")
    
    # Save
    output = {
        'total_guests': len(guests),
        'guests': []
    }
    
    for guest_name, data in sorted(guests.items()):
        output['guests'].append({
            'name': guest_name,
            'appearances': data['appearances'],
            'podcasts': sorted(list(data['podcasts'])),
            'episodes': data['episodes']
        })
    
    with open('guest_directory_ALL_ON_ALL.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print("\n" + "=" * 80)
    print(f"✓ Total: {total_extracted} appearances")
    print(f"✓ Unique guests: {len(guests)}")
    print(f"\n✓ Saved to guest_directory_ALL_ON_ALL.json")

if __name__ == "__main__":
    extract_all_patterns_all_podcasts()
