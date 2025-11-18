#!/usr/bin/env python3
"""
3-Way RSS-to-Downloads Reconciliation
Compare RSS feed entries to downloaded files to find exact mismatches
"""

import feedparser
import re
from pathlib import Path
from collections import defaultdict

def sanitize_filename(title):
    """Same sanitization as downloader"""
    filename = re.sub(r'[<>:"/\\|?*]', '', title)
    filename = re.sub(r'\s+', ' ', filename)
    filename = filename[:150]
    return filename.strip()

def main():
    rss_url = "https://www.patreon.com/rss/TrueAnonPod?auth=u4Mg8CRw-MuQG_VOQpVyNVOnURwSzLc8&show=875184"

    print("=" * 100)
    print("RSS-TO-DOWNLOADS RECONCILIATION - TRUE ANON TRUTH FEED")
    print("=" * 100)
    print()

    # Fetch RSS feed
    print("Fetching RSS feed...")
    feed = feedparser.parse(rss_url)
    print(f"✓ RSS feed has {len(feed.entries)} entries")
    print()

    # Get downloaded files
    episodes_dir = Path(__file__).parent.parent / "episodes" / "TRUE ANON TRUTH FEED"
    downloaded_files = {}

    for ext in ['*.mp3', '*.m4a', '*.wav']:
        for f in episodes_dir.glob(ext):
            downloaded_files[f.stem] = f.suffix

    print(f"✓ Found {len(downloaded_files)} downloaded files")
    print()

    # Build RSS title map
    rss_titles = {}
    rss_duplicates = []

    for entry in feed.entries:
        title = entry.get('title', 'Unknown')
        safe_title = sanitize_filename(title)

        if safe_title in rss_titles:
            rss_duplicates.append(safe_title)
        else:
            rss_titles[safe_title] = entry

    print(f"✓ RSS has {len(rss_titles)} unique titles")
    if rss_duplicates:
        print(f"  (Found {len(rss_duplicates)} duplicates)")
    print()

    # Find mismatches
    print("=" * 100)
    print("FINDING MISMATCHES")
    print("=" * 100)
    print()

    # In RSS but not downloaded
    in_rss_not_downloaded = []
    for title in rss_titles:
        if title not in downloaded_files:
            in_rss_not_downloaded.append(title)

    # Downloaded but not in RSS
    downloaded_not_in_rss = []
    for title in downloaded_files:
        if title not in rss_titles:
            downloaded_not_in_rss.append(title)

    # Report
    if in_rss_not_downloaded:
        print(f"⚠️  IN RSS BUT NOT DOWNLOADED ({len(in_rss_not_downloaded)} files):")
        print("-" * 100)
        for i, title in enumerate(sorted(in_rss_not_downloaded), 1):
            entry = rss_titles[title]
            print(f"\n[{i}] {title}")
            print(f"    Full title: {entry.get('title', 'Unknown')}")
            print(f"    Published: {entry.get('published', 'Unknown')}")

            # Check if enclosure exists
            if 'enclosures' in entry and entry.enclosures:
                enc = entry.enclosures[0]
                print(f"    Audio URL: {enc.get('href', 'N/A')[:80]}...")
                print(f"    Audio type: {enc.get('type', 'Unknown')}")
            else:
                print(f"    Audio URL: ❌ NO ENCLOSURE FOUND")
        print()
    else:
        print("✅ All RSS entries are downloaded!")
        print()

    if downloaded_not_in_rss:
        print("=" * 100)
        print(f"⚠️  DOWNLOADED BUT NOT IN RSS ({len(downloaded_not_in_rss)} files):")
        print("-" * 100)
        for i, title in enumerate(sorted(downloaded_not_in_rss), 1):
            ext = downloaded_files[title]
            print(f"[{i}] {title}{ext}")
        print()
    else:
        print("✅ All downloaded files are in RSS!")
        print()

    # Duplicates detail
    if rss_duplicates:
        print("=" * 100)
        print(f"ℹ️  RSS DUPLICATE ENTRIES ({len(rss_duplicates)} duplicates):")
        print("-" * 100)
        for dup in rss_duplicates:
            print(f"  - {dup}")
        print()

    # Summary
    print("=" * 100)
    print("SUMMARY")
    print("=" * 100)
    print(f"RSS entries (total): {len(feed.entries)}")
    print(f"RSS entries (unique): {len(rss_titles)}")
    print(f"Downloaded files: {len(downloaded_files)}")
    print(f"Missing from downloads: {len(in_rss_not_downloaded)}")
    print(f"Extra in downloads: {len(downloaded_not_in_rss)}")
    print()

    # Calculate expected adjustment
    expected_adjustment = len(feed.entries) - len(downloaded_files)
    print(f"Expected RSS adjustment: {expected_adjustment:+d}")
    print(f"  (RSS total {len(feed.entries)} - Downloaded {len(downloaded_files)} = {expected_adjustment:+d})")
    print()
    print("=" * 100)

if __name__ == "__main__":
    main()
