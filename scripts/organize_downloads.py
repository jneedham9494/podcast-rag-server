#!/usr/bin/env python3
"""
Organize manually downloaded Patreon episodes
Moves files from Downloads to episodes folder with proper naming
"""

import re
from pathlib import Path
import shutil

def sanitize_filename(title):
    """Convert episode title to safe filename"""
    filename = re.sub(r'[<>:"/\\|?*]', '', title)
    filename = re.sub(r'\s+', ' ', filename)
    filename = filename[:150]
    return filename.strip()

def extract_episode_number(filename):
    """Extract episode number from filename"""
    # Try patterns like "418 - midtown martini"
    match = re.match(r'(\d+)\s*[-_\s]', filename.lower())
    if match:
        return int(match.group(1))
    return None

def find_matching_episode(episode_num, rss_feed_url):
    """Find the episode in RSS feed by number"""
    import feedparser

    feed = feedparser.parse(rss_feed_url)

    for entry in feed.entries:
        title = entry.get('title', '')
        # Check if title contains the episode number
        if f"Episode {episode_num} " in title:
            return title

    return None

def find_matching_episode_by_title(filename, rss_feed_url):
    """Find episode in RSS feed by fuzzy title matching"""
    import feedparser

    feed = feedparser.parse(rss_feed_url)

    # Clean up filename for matching
    search_terms = filename.lower().replace('(1)', '').replace('(2)', '').strip()
    search_terms = re.sub(r'[_\-]', ' ', search_terms)

    best_match = None
    best_score = 0

    for entry in feed.entries:
        title = entry.get('title', '').lower()

        # Split words that end with digits in search terms
        search_terms_split = re.sub(r'([a-z]+)(\d+)', r'\1 \2', search_terms)

        # Simple similarity check - count matching words
        search_words = set(search_terms_split.split())
        title_words = set(title.split())

        if len(search_words) > 0:
            matching_words = search_words.intersection(title_words)
            score = len(matching_words) / len(search_words)

            if score > best_score and score > 0.25:  # At least 25% word match
                best_score = score
                best_match = entry.get('title', '')

    return best_match

def main():
    downloads_dir = Path.home() / "Downloads"
    episodes_dir = Path(__file__).parent.parent / "episodes" / "TRUE ANON TRUTH FEED"

    rss_url = "https://www.patreon.com/rss/TrueAnonPod?auth=u4Mg8CRw-MuQG_VOQpVyNVOnURwSzLc8&show=875184"

    print("=" * 80)
    print("ORGANIZE PATREON DOWNLOADS")
    print("=" * 80)
    print()

    # Find all mp3 files in Downloads
    mp3_files = list(downloads_dir.glob("*.mp3"))

    if not mp3_files:
        print("No MP3 files found in Downloads folder")
        return

    print(f"Found {len(mp3_files)} MP3 file(s) in Downloads")
    print()

    # Process each file
    moved = []
    skipped = []

    for mp3_file in mp3_files:
        filename = mp3_file.stem  # Without extension

        # Try to extract episode number
        episode_num = extract_episode_number(filename)

        print(f"Processing: {mp3_file.name}")

        proper_title = None

        if episode_num:
            print(f"  Detected episode number: {episode_num}")
            # Find proper title from RSS feed by episode number
            proper_title = find_matching_episode(episode_num, rss_url)
        else:
            print(f"  No episode number found, trying title matching...")
            # Try fuzzy title matching
            proper_title = find_matching_episode_by_title(filename, rss_url)

        if proper_title:
            print(f"  Matched to: {proper_title}")
            safe_title = sanitize_filename(proper_title)
            target_file = episodes_dir / f"{safe_title}.mp3"

            # Check if already exists
            if target_file.exists():
                existing_size = target_file.stat().st_size / (1024 * 1024)
                print(f"  ⏭️  Already exists: {safe_title}.mp3 ({existing_size:.1f} MB)")
                print(f"  Removing duplicate from Downloads...")
                mp3_file.unlink()
                skipped.append(filename)
            else:
                # Move and rename
                print(f"  Moving to: {safe_title}.mp3")
                shutil.move(str(mp3_file), str(target_file))
                file_size = target_file.stat().st_size / (1024 * 1024)
                print(f"  ✓ Moved: {file_size:.1f} MB")
                moved.append(safe_title)
        else:
            if episode_num:
                print(f"  ⚠️  Could not find episode {episode_num} in RSS feed")
            else:
                print(f"  ⚠️  Could not find matching episode in RSS feed")
            print(f"  Skipping: {mp3_file.name}")
            skipped.append(filename)

        print()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✓ Moved: {len(moved)} files")
    if moved:
        for title in moved:
            print(f"  - {title}")

    print(f"\n⏭️  Skipped: {len(skipped)} files")
    if skipped:
        for title in skipped:
            print(f"  - {title}")

    print("=" * 80)

if __name__ == "__main__":
    main()
