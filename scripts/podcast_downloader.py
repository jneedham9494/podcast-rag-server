#!/usr/bin/env python3
"""
Podcast Downloader
Downloads and organizes podcast episodes from OPML feed list
"""

import xml.etree.ElementTree as ET
import feedparser
import requests
from pathlib import Path
import json
import re
from urllib.parse import urlparse
import sys


def parse_opml(opml_file):
    """Parse OPML file and extract podcast RSS feeds"""
    tree = ET.parse(opml_file)
    root = tree.getroot()

    feeds = []
    for outline in root.findall('.//outline[@type="rss"]'):
        feed_info = {
            'title': outline.get('text', ''),
            'url': outline.get('xmlUrl', '')
        }
        feeds.append(feed_info)

    return feeds


def get_feed_by_name(opml_file, podcast_name):
    """Extract a specific podcast feed by name"""
    feeds = parse_opml(opml_file)

    for feed in feeds:
        if podcast_name.lower() in feed['title'].lower():
            return feed

    return None


def fetch_episodes(rss_url, limit=None, start_index=None, end_index=None):
    """Fetch and parse RSS feed to get episode information

    Args:
        rss_url: RSS feed URL
        limit: Maximum episodes to fetch (deprecated, use start/end instead)
        start_index: Starting episode index (0-based, inclusive)
        end_index: Ending episode index (0-based, exclusive)

    Returns:
        tuple: (episodes list, session object or None)
    """
    print(f"Fetching RSS feed from {rss_url}...")

    # Detect Patreon feeds and create session for authentication
    is_patreon = 'patreon.com' in rss_url.lower()
    session = None

    if is_patreon:
        # Use requests session to maintain cookies for Patreon
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'PocketCasts/1.0',
            'Accept': '*/*',
        })
        # Fetch RSS with session to get cookies
        response = session.get(rss_url, timeout=30)
        response.raise_for_status()
        feed = feedparser.parse(response.content)
        print("✓ Using authenticated session for Patreon feed")
    else:
        feed = feedparser.parse(rss_url)

    episodes = []

    # Handle range slicing
    if start_index is not None and end_index is not None:
        entries = feed.entries[start_index:end_index]
    elif limit:
        entries = feed.entries[:limit]
    else:
        entries = feed.entries

    for entry in entries:
        # Find audio URL in enclosures
        audio_url = None
        if hasattr(entry, 'enclosures') and entry.enclosures:
            for enclosure in entry.enclosures:
                if 'audio' in enclosure.get('type', ''):
                    audio_url = enclosure.get('href', '')
                    break

        episode = {
            'title': entry.get('title', 'Unknown'),
            'published': entry.get('published', 'Unknown date'),
            'audio_url': audio_url,
            'description': entry.get('summary', '')
        }
        episodes.append(episode)

    return episodes, session


def sanitize_filename(title):
    """Convert episode title to safe filename"""
    # Remove or replace invalid filename characters
    filename = re.sub(r'[<>:"/\\|?*]', '', title)
    # Replace multiple spaces with single space
    filename = re.sub(r'\s+', ' ', filename)
    # Limit length
    filename = filename[:150]
    return filename.strip()


def download_episode(episode, podcast_name, output_dir=None, rss_url=None, session=None):
    """Download a podcast episode

    Args:
        episode: Episode dict with title, audio_url, etc.
        podcast_name: Name of the podcast
        output_dir: Optional output directory
        rss_url: Optional RSS URL (unused but kept for compatibility)
        session: Optional requests.Session object for authenticated downloads (Patreon)
    """
    if not episode['audio_url']:
        print(f"✗ No audio URL found for episode: {episode['title']}")
        return None

    # Default to project root episodes folder
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "episodes"

    # Create podcast-specific directory
    podcast_dir = Path(output_dir) / sanitize_filename(podcast_name)
    podcast_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename
    safe_title = sanitize_filename(episode['title'])
    file_extension = Path(urlparse(episode['audio_url']).path).suffix or '.mp3'
    filename = podcast_dir / f"{safe_title}{file_extension}"

    # Check if already downloaded
    if filename.exists():
        # Validate file size - podcast episodes should be at least 1MB
        # Anything smaller is likely a partial/corrupted download
        file_size_mb = filename.stat().st_size / (1024 * 1024)

        if file_size_mb < 1.0:
            print(f"⚠️  Partial download detected ({file_size_mb:.2f} MB), re-downloading: {filename.name}")
            filename.unlink()  # Delete partial file
            # Also remove metadata if exists
            metadata_file = filename.with_suffix('.json')
            if metadata_file.exists():
                metadata_file.unlink()
        else:
            print(f"✓ Already downloaded: {filename.name} ({file_size_mb:.1f} MB)")
            return filename

    # Download the file
    print(f"\nDownloading: {episode['title']}")

    # Detect Patreon URLs and use session if available
    is_patreon = 'patreon.com' in episode['audio_url'].lower()

    try:
        if is_patreon and session:
            # Use the authenticated session for Patreon downloads
            print("  [Using authenticated Patreon session]")
            # Update session headers with Patreon-specific values
            session.headers.update({
                'Referer': rss_url if rss_url else 'https://www.patreon.com/',
                'Origin': 'https://www.patreon.com',
                'Accept': 'audio/mpeg,audio/*,*/*',
            })
            response = session.get(episode['audio_url'], stream=True, timeout=60, allow_redirects=True)
        else:
            # Use regular requests for non-Patreon feeds
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://www.google.com/',
            }
            response = requests.get(episode['audio_url'], stream=True, headers=headers, timeout=60)

        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0

        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\rProgress: {percent:.1f}% ({downloaded / (1024*1024):.1f} MB)", end='')

        print(f"\n✓ Downloaded: {filename.name}")

        # Save metadata
        metadata = {
            'title': episode['title'],
            'published': episode['published'],
            'description': episode['description'],
            'audio_file': str(filename)
        }

        metadata_file = filename.with_suffix('.json')
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        return filename

    except Exception as e:
        print(f"\n✗ Error downloading episode: {e}")
        if filename.exists():
            filename.unlink()  # Remove partial download
        return None


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python podcast_downloader.py <podcast_name> [episode_limit | start:end]")
        print("\nExample:")
        print("  python podcast_downloader.py 'Louis Theroux' 5")
        print("  python podcast_downloader.py 'TrueAnon'")
        print("  python podcast_downloader.py 'Chapo' 0:100  # Episodes 0-99")
        print("  python podcast_downloader.py 'Chapo' 100:200  # Episodes 100-199")
        return

    podcast_search = sys.argv[1]
    episode_limit = None
    start_index = None
    end_index = None

    # Parse episode range or limit
    if len(sys.argv) > 2:
        range_arg = sys.argv[2]
        if ':' in range_arg:
            # Range format: start:end
            parts = range_arg.split(':')
            start_index = int(parts[0])
            end_index = int(parts[1])
        else:
            # Legacy limit format
            episode_limit = int(range_arg)

    opml_path = Path(__file__).parent.parent / "podocasts.opml"  # OPML is in project root

    print(f"Searching for podcast: {podcast_search}")
    feed = get_feed_by_name(opml_path, podcast_search)

    if not feed:
        print(f"✗ Could not find podcast matching '{podcast_search}'")
        print("\nAvailable podcasts:")
        feeds = parse_opml(opml_path)
        for f in sorted(feeds, key=lambda x: x['title']):
            print(f"  - {f['title']}")
        return

    print(f"✓ Found: {feed['title']}")

    # Fetch episodes
    episodes, session = fetch_episodes(feed['url'], limit=episode_limit, start_index=start_index, end_index=end_index)

    if start_index is not None and end_index is not None:
        print(f"\n✓ Found {len(episodes)} episodes (range {start_index}:{end_index})")
    else:
        print(f"\n✓ Found {len(episodes)} episodes")

    if not episodes:
        print("No episodes found")
        return

    # Download episodes
    print("\n" + "=" * 80)
    print("Starting downloads...")
    print("=" * 80)

    downloaded = []
    for i, episode in enumerate(episodes, 1):
        print(f"\n[{i}/{len(episodes)}]")
        result = download_episode(episode, feed['title'], rss_url=feed['url'], session=session)
        if result:
            downloaded.append(result)

    print("\n" + "=" * 80)
    print(f"✓ Download complete! {len(downloaded)}/{len(episodes)} episodes downloaded")
    print(f"  Location: episodes/{sanitize_filename(feed['title'])}/")
    print("=" * 80)


if __name__ == "__main__":
    main()
