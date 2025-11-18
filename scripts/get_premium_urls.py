#!/usr/bin/env python3
"""
Get direct download URLs for the 3 premium episodes
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

# The 3 premium episodes
premium_episodes = [
    "Episode 502 Red Scare",
    "[911 Week] Bush Did 911 Part 2",
    "[911 Week] Bush Did 911 Part 3"
]

print("=" * 100)
print("PREMIUM EPISODES - DOWNLOAD INSTRUCTIONS")
print("=" * 100)
print()

for i, target in enumerate(premium_episodes, 1):
    for entry in feed.entries:
        title = entry.get('title', '')
        safe_title = sanitize_filename(title)

        if safe_title == target:
            print(f"[{i}] {title}")
            print(f"    Filename: {safe_title}.mp3")
            print(f"    Published: {entry.get('published', 'Unknown')}")

            if 'enclosures' in entry and entry.enclosures:
                enc = entry.enclosures[0]
                url = enc.get('href', '')
                size_bytes = enc.get('length', 0)
                size_mb = int(size_bytes) / (1024 * 1024) if size_bytes else 0

                print(f"    Size: {size_mb:.1f} MB")
                print(f"    URL: {url}")
                print()
                print(f"    To download manually:")
                print(f"    1. Open Patreon.com in your browser (make sure you're logged in)")
                print(f"    2. Copy this URL and paste it in your browser:")
                print(f"       {url}")
                print(f"    3. Save as: {safe_title}.mp3")
                print(f"    4. Move to: episodes/TRUE ANON TRUTH FEED/")
            print()
            print("-" * 100)
            print()
            break

print()
print("ALTERNATIVE METHOD:")
print("If URLs don't work in browser, you may need to:")
print("1. Go to Patreon.com/TrueAnonPod")
print("2. Find the episodes in the feed")
print("3. Click download button for each")
print()
print("=" * 100)
