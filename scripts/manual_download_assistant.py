#!/usr/bin/env python3
"""
Manual Download Assistant for Premium Patreon Episodes
Opens Patreon post URLs in browser, then watches Downloads folder
and automatically moves/renames files when they appear
"""

import time
import webbrowser
import re
import shutil
from pathlib import Path
from difflib import get_close_matches

def sanitize_filename(title):
    """Convert episode title to safe filename"""
    filename = re.sub(r'[<>:"/\\|?*]', '', title)
    filename = re.sub(r'\s+', ' ', filename)
    filename = filename[:150]
    return filename.strip()

def get_missing_episodes(rss_url, episodes_dir):
    """Get episodes from RSS that are not yet downloaded"""
    import feedparser

    feed = feedparser.parse(rss_url)

    if not feed.entries:
        print("ERROR: Could not fetch RSS feed or feed is empty")
        return []

    # Get all downloaded files (without extension)
    downloaded = set()
    for ext in ['*.mp3', '*.m4a', '*.wav']:
        for f in episodes_dir.glob(ext):
            downloaded.add(f.stem.lower())

    print(f"Found {len(downloaded)} downloaded episodes")
    print(f"RSS feed has {len(feed.entries)} entries")

    episodes = []
    for entry in feed.entries:
        title = entry.get('title', '')
        safe_title = sanitize_filename(title)

        # Check if this episode is already downloaded
        # Use lowercase comparison for flexibility
        if safe_title.lower() not in downloaded:
            # Also check for partial matches (in case of slight naming differences)
            found = False
            for dl_file in downloaded:
                # Check if the core title matches (ignoring episode numbers, etc.)
                if safe_title.lower() in dl_file or dl_file in safe_title.lower():
                    found = True
                    break

            if not found:
                # Get Patreon post URL
                post_url = entry.get('link', '')

                episodes.append({
                    'title': title,
                    'safe_title': safe_title,
                    'post_url': post_url,
                    'published': entry.get('published', 'Unknown')
                })

    return episodes

def watch_downloads_folder(expected_files, episodes_dir, timeout=300):
    """
    Watch Downloads folder for files and move them

    Args:
        expected_files: List of expected safe_title filenames
        episodes_dir: Target directory
        timeout: How long to watch (seconds)
    """
    downloads_dir = Path.home() / "Downloads"
    start_time = time.time()
    found_files = set()

    print("\n" + "=" * 80)
    print("WATCHING DOWNLOADS FOLDER")
    print("=" * 80)
    print(f"Watching: {downloads_dir}")
    print(f"Timeout: {timeout} seconds")
    print()
    print("Expected files:")
    for expected in expected_files:
        print(f"  - {expected}.mp3")
    print()
    print("Download the files in your browser, I'll automatically move them...")
    print("Press Ctrl+C to stop watching")
    print()

    try:
        while (time.time() - start_time) < timeout:
            # Check for new MP3 files in Downloads
            mp3_files = list(downloads_dir.glob("*.mp3"))

            for mp3_file in mp3_files:
                filename_stem = mp3_file.stem

                # Skip if already processed
                if filename_stem in found_files:
                    continue

                # Try to match to expected files
                # Use fuzzy matching in case browser renamed it
                matches = get_close_matches(
                    filename_stem,
                    expected_files,
                    n=1,
                    cutoff=0.6
                )

                if matches:
                    matched_title = matches[0]
                    target_file = episodes_dir / f"{matched_title}.mp3"

                    # Wait a moment to ensure download is complete
                    # (file size stops changing)
                    prev_size = 0
                    curr_size = mp3_file.stat().st_size

                    print(f"📥 Found: {mp3_file.name}")
                    print(f"   Waiting for download to complete...", end='', flush=True)

                    while curr_size != prev_size:
                        time.sleep(2)
                        prev_size = curr_size
                        curr_size = mp3_file.stat().st_size
                        print(".", end='', flush=True)

                    print(" Done!")

                    # Move and rename
                    file_size_mb = curr_size / (1024 * 1024)
                    print(f"   Matched to: {matched_title}")
                    print(f"   Size: {file_size_mb:.1f} MB")
                    print(f"   Moving to: {target_file.name}")

                    shutil.move(str(mp3_file), str(target_file))

                    print(f"   ✅ Moved successfully!")
                    print()

                    found_files.add(filename_stem)
                    expected_files.remove(matched_title)

                    # Check if all done
                    if not expected_files:
                        print("🎉 All files downloaded and moved!")
                        return True

            # Sleep before next check
            time.sleep(3)

        # Timeout reached
        print("\n⏱️  Timeout reached")
        if expected_files:
            print(f"\nStill waiting for {len(expected_files)} file(s):")
            for expected in expected_files:
                print(f"  - {expected}.mp3")

        return len(found_files) > 0

    except KeyboardInterrupt:
        print("\n\n⚠️  Stopped watching")
        if found_files:
            print(f"\n✓ Moved {len(found_files)} file(s)")
        if expected_files:
            print(f"\nStill missing {len(expected_files)} file(s):")
            for expected in expected_files:
                print(f"  - {expected}.mp3")
        return len(found_files) > 0

def main():
    rss_url = "https://www.patreon.com/rss/TrueAnonPod?auth=u4Mg8CRw-MuQG_VOQpVyNVOnURwSzLc8&show=875184"
    episodes_dir = Path(__file__).parent.parent / "episodes" / "TRUE ANON TRUTH FEED"

    print("=" * 80)
    print("MANUAL DOWNLOAD ASSISTANT - Premium Patreon Episodes")
    print("=" * 80)
    print()

    # Get episodes that need manual download
    print("Fetching episode information from RSS feed...")
    episodes = get_missing_episodes(rss_url, episodes_dir)

    if not episodes:
        print("✓ No episodes need manual download!")
        return

    print(f"Found {len(episodes)} episode(s) that need manual download:")
    print()

    # Display episodes and open in browser
    for i, episode in enumerate(episodes, 1):
        print(f"[{i}] {episode['title']}")
        print(f"    Published: {episode['published']}")
        print(f"    URL: {episode['post_url']}")
        print()

    print("=" * 80)
    print("Opening URLs in browser in 3 seconds...")
    time.sleep(3)
    print()

    # Open all URLs in browser
    for episode in episodes:
        print(f"Opening: {episode['title']}")
        webbrowser.open(episode['post_url'])
        time.sleep(1)  # Small delay between opens

    print()
    print("✓ Opened all episodes in your browser")
    print()
    print("INSTRUCTIONS:")
    print("1. In your browser, find the download button for each episode")
    print("2. Click download and save to your Downloads folder")
    print("3. I'll automatically detect and move the files")
    print()

    # Prepare expected filenames
    expected_files = [ep['safe_title'] for ep in episodes]

    # Watch Downloads folder
    success = watch_downloads_folder(expected_files, episodes_dir, timeout=600)

    if success:
        print("\n" + "=" * 80)
        print("✅ MANUAL DOWNLOAD COMPLETE")
        print("=" * 80)
        print()
        print("Next steps:")
        print("1. Run comprehensive_verification.py to verify all files")
        print("2. Transcribe the new episodes")
        print()
    else:
        print("\n" + "=" * 80)
        print("⚠️  INCOMPLETE")
        print("=" * 80)
        print()
        print("You can run organize_downloads.py later to move any remaining files")
        print()

if __name__ == "__main__":
    main()
