#!/usr/bin/env python3
"""
False Positive Cleanup Script - CORRECTED VERSION
Removes false positives from guest_directory_complete.json

FIXES:
- Correctly extracts PERSON names from "Company CEO Name" patterns
- Keeps person name, removes organization/title prefix
"""

import json
import re
from collections import defaultdict


def clean_guest_name(name):
    """
    Clean guest names by removing false positive patterns.
    Returns cleaned name or None if should be skipped.
    """
    if not name:
        return None

    original_name = name

    # 1. SAFE: Remove trailing prepositions (68 entries - highest impact)
    name = re.sub(r'\s+to\s+(?:discuss|talk|chat|look|preview|review)$', '', name, flags=re.IGNORECASE)

    # 2. SAFE: Remove media organization suffixes (2 entries)
    name = re.sub(r'\s+of\s+(?:CBS|ESPN|The Athletic|Second Captains)$', '', name, flags=re.IGNORECASE)

    # 3. SAFE: Remove "from the [location]" suffixes
    name = re.sub(r'\s+from\s+the\s+\w+$', '', name, flags=re.IGNORECASE)

    # 4. SAFE: Remove professional title prefixes (5 entries)
    name = re.sub(r'^(?:Author|Writer|Journalist|Professor|Director|Comedian|Reporter|Activist)\s+', '', name)

    # 5. SAFE: Remove work description suffixes
    name = re.sub(r'\s+about\s+(?:her|his|their)\s+work$', '', name, flags=re.IGNORECASE)

    # 6. CORRECTED: Fed President titles (extract PERSON name, not organization)
    # "Chicago Fed President Austan Goolsbee" → "Austan Goolsbee"
    match = re.match(r'^(Chicago|Dallas|Richmond|San Francisco|New York)\s+Fed\s+President\s+(.+)$', name)
    if match:
        name = match.group(2)  # Keep the PERSON name (group 2)

    # 7. CORRECTED: CEO/Executive titles (extract PERSON name, not company)
    # "Mercury Group CEO Anton Posner" → "Anton Posner"
    # "AIKON CEO Marc Blinder" → "Marc Blinder"
    # "Tether CEO Paolo Ardoino about" → "Paolo Ardoino"
    match = re.match(r'^(.+?)\s+(CEO|Founder|President|Director)\s+(.+?)(?:\s+about)?$', name)
    if match:
        person = match.group(3)
        # Always extract the person name when this pattern matches
        name = person.strip()

    # Clean up whitespace
    name = ' '.join(name.split())

    # Validation: Skip if became too short
    if len(name) < 3:
        return None

    # Validation: Skip if no change and appears to be invalid
    name_lower = name.lower()
    skip_terms = ['podcast', 'show', 'episode', 'economics and']
    if any(term in name_lower for term in skip_terms):
        return None

    return name


def merge_duplicates():
    """
    Load guest directory, clean names, and merge duplicates.
    """
    print("🧹 FALSE POSITIVE CLEANUP - CORRECTED VERSION")
    print("=" * 80)

    with open('guest_directory_complete.json', 'r') as f:
        data = json.load(f)

    print(f"\n📊 Before cleanup:")
    print(f"   Total guests: {data['total_guests']}")

    # Track changes
    cleaned_guests = defaultdict(lambda: {
        'appearances': 0,
        'podcasts': set(),
        'episodes': [],
        'twitter_handles': set(),
        'twitter_from_metadata': False
    })

    false_positives = []
    cleaning_examples = defaultdict(list)

    # Process each guest
    for guest in data['guests']:
        original_name = guest['name']
        cleaned_name = clean_guest_name(original_name)

        if cleaned_name is None:
            # Skip entirely (invalid entry)
            false_positives.append({
                'original': original_name,
                'action': 'REMOVED',
                'reason': 'Invalid entry'
            })
            continue

        # Track if name changed
        if cleaned_name != original_name:
            cleaning_examples[f"{original_name} → {cleaned_name}"].append(guest['podcasts'])

        # Merge into cleaned entry
        cleaned_guests[cleaned_name]['appearances'] += guest['appearances']
        cleaned_guests[cleaned_name]['podcasts'].update(guest['podcasts'])
        cleaned_guests[cleaned_name]['episodes'].extend(guest['episodes'])
        cleaned_guests[cleaned_name]['twitter_handles'].update(guest.get('twitter_handles', []))
        if guest.get('twitter_from_metadata'):
            cleaned_guests[cleaned_name]['twitter_from_metadata'] = True

    # Build output
    output = {
        'total_guests': len(cleaned_guests),
        'total_episodes': data['total_episodes'],
        'guests_with_twitter_from_metadata': sum(1 for g in cleaned_guests.values() if g['twitter_from_metadata']),
        'guests': []
    }

    for name, info in sorted(cleaned_guests.items()):
        output['guests'].append({
            'name': name,
            'appearances': info['appearances'],
            'podcasts': sorted(list(info['podcasts'])),
            'episodes': info['episodes'],
            'twitter_handles': sorted(list(info['twitter_handles']))
        })

    # Save cleaned version
    with open('guest_directory_complete_CLEANED.json', 'w') as f:
        json.dump(output, f, indent=2)

    # Print results
    print(f"\n📊 After cleanup:")
    print(f"   Total guests: {output['total_guests']}")
    print(f"   False positives merged: {data['total_guests'] - output['total_guests']}")

    if cleaning_examples:
        print(f"\n✨ Cleaning Examples (showing first 20):")
        for i, (change, podcasts) in enumerate(list(cleaning_examples.items())[:20], 1):
            print(f"   {i}. {change}")

    print(f"\n✅ Saved to: guest_directory_complete_CLEANED.json")
    print("\n💡 Review the cleaned file before replacing the original.")


if __name__ == "__main__":
    merge_duplicates()
