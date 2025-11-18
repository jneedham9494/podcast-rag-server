#!/usr/bin/env python3
"""
Check RSS feed metadata for premium indicators
"""

import feedparser
import re
from pathlib import Path
from pprint import pprint

def sanitize_filename(title):
    filename = re.sub(r'[<>:"/\\|?*]', '', title)
    filename = re.sub(r'\s+', ' ', filename)
    filename = filename[:150]
    return filename.strip()

def main():
    rss_url = "https://www.patreon.com/rss/TrueAnonPod?auth=u4Mg8CRw-MuQG_VOQpVyNVOnURwSzLc8&show=875184"

    print("Fetching RSS feed...")
    feed = feedparser.parse(rss_url)

    # Get downloaded episodes
    episodes_dir = Path(__file__).parent.parent / "episodes" / "TRUE ANON TRUTH FEED"
    downloaded = {f.stem for f in episodes_dir.glob("*.mp3")}

    print(f"\nAnalyzing {len(feed.entries)} episodes in RSS feed...\n")
    print("=" * 100)

    # Collect all unique metadata keys across all episodes
    all_keys = set()
    for entry in feed.entries:
        all_keys.update(entry.keys())

    print(f"Available metadata fields in RSS feed:")
    print(f"  {sorted(all_keys)}\n")
    print("=" * 100)

    # Check a few episodes in detail - both downloaded and missing
    print("\nDETAILED METADATA ANALYSIS:\n")

    downloaded_samples = []
    missing_samples = []

    for entry in feed.entries:
        title = entry.get('title', 'Unknown')
        safe_title = sanitize_filename(title)

        if safe_title in downloaded:
            if len(downloaded_samples) < 3:
                downloaded_samples.append(entry)
        else:
            if len(missing_samples) < 3:
                missing_samples.append(entry)

        if len(downloaded_samples) >= 3 and len(missing_samples) >= 3:
            break

    print("SAMPLE DOWNLOADED EPISODES:")
    print("-" * 100)
    for i, entry in enumerate(downloaded_samples, 1):
        print(f"\n[{i}] {entry.get('title', 'Unknown')}")
        print(f"    Downloaded: YES")

        # Print all metadata
        for key in sorted(entry.keys()):
            value = entry[key]
            # Truncate long values
            if isinstance(value, str) and len(value) > 200:
                value = value[:200] + "..."
            print(f"    {key}: {value}")

    print("\n" + "=" * 100)
    print("\nSAMPLE MISSING EPISODES:")
    print("-" * 100)
    for i, entry in enumerate(missing_samples, 1):
        print(f"\n[{i}] {entry.get('title', 'Unknown')}")
        print(f"    Downloaded: NO")

        # Print all metadata
        for key in sorted(entry.keys()):
            value = entry[key]
            # Truncate long values
            if isinstance(value, str) and len(value) > 200:
                value = value[:200] + "..."
            print(f"    {key}: {value}")

    print("\n" + "=" * 100)
    print("\nKEY COMPARISONS:")
    print("-" * 100)

    # Compare specific fields that might indicate premium status
    fields_to_check = ['title', 'summary', 'tags', 'category', 'author',
                       'published', 'enclosures', 'links', 'media_content']

    for field in fields_to_check:
        print(f"\n{field.upper()}:")

        # Get sample values from both groups
        dl_values = [entry.get(field, 'N/A') for entry in downloaded_samples]
        miss_values = [entry.get(field, 'N/A') for entry in missing_samples]

        print(f"  Downloaded samples: {dl_values[0] if dl_values else 'N/A'}")
        print(f"  Missing samples: {miss_values[0] if miss_values else 'N/A'}")

    # Search for premium-related keywords in all text fields
    print("\n" + "=" * 100)
    print("\nSEARCHING FOR PREMIUM INDICATORS:")
    print("-" * 100)

    premium_keywords = ['premium', 'tier', 'patron', 'subscriber', 'exclusive',
                        'locked', 'members', 'paid', 'paywall']

    for keyword in premium_keywords:
        print(f"\nSearching for '{keyword}'...")
        found_in_downloaded = 0
        found_in_missing = 0

        for entry in feed.entries:
            title = entry.get('title', 'Unknown')
            safe_title = sanitize_filename(title)

            # Search in all text fields
            text_content = str(entry).lower()

            if keyword in text_content:
                if safe_title in downloaded:
                    found_in_downloaded += 1
                else:
                    found_in_missing += 1

        print(f"  Found in {found_in_downloaded} downloaded episodes")
        print(f"  Found in {found_in_missing} missing episodes")

        if found_in_downloaded > 0 or found_in_missing > 0:
            print(f"  ⚠️  KEYWORD FOUND!")

if __name__ == "__main__":
    main()
