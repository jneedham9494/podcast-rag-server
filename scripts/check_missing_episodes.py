#!/usr/bin/env python3
"""
Check the 3 missing episodes to see if they have downloadable audio
"""

import feedparser
import re

def sanitize_filename(title):
    filename = re.sub(r'[<>:"/\\|?*]', '', title)
    filename = re.sub(r'\s+', ' ', filename)
    filename = filename[:150]
    return filename.strip()

rss_url = "https://www.patreon.com/rss/TrueAnonPod?auth=u4Mg8CRw-MuQG_VOQpVyNVOnURwSzLc8&show=875184"

print("Fetching RSS feed...")
feed = feedparser.parse(rss_url)
print(f"Total entries: {len(feed.entries)}\n")

# Look for the 3 specific episodes
missing_episodes = [
    "Episode 502 Red Scare",
    "[911 Week] Bush Did 911 Part 2",
    "[911 Week] Bush Did 911 Part 3"
]

print("=" * 100)
print("CHECKING MISSING EPISODES")
print("=" * 100)

for target in missing_episodes:
    print(f"\nSearching for: {target}")
    print("-" * 100)

    found = False
    for entry in feed.entries:
        title = entry.get('title', '')
        safe_title = sanitize_filename(title)

        if safe_title == target:
            found = True
            print(f"✓ FOUND IN RSS")
            print(f"  Original title: {title}")
            print(f"  Sanitized: {safe_title}")
            print(f"  Published: {entry.get('published', 'Unknown')}")

            # Check for enclosures (audio files)
            if 'enclosures' in entry and entry.enclosures:
                print(f"  Enclosures: {len(entry.enclosures)}")
                for i, enc in enumerate(entry.enclosures):
                    print(f"    [{i+1}] Type: {enc.get('type', 'Unknown')}")
                    print(f"        URL: {enc.get('href', 'N/A')[:80]}...")
                    print(f"        Length: {enc.get('length', 'Unknown')}")
            else:
                print(f"  ❌ NO ENCLOSURES - CAN'T DOWNLOAD")

            # Check all fields
            print(f"  All fields: {list(entry.keys())}")
            break

    if not found:
        print(f"❌ NOT FOUND in RSS feed")

print("\n" + "=" * 100)
