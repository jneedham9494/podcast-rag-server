#!/usr/bin/env python3
"""
Podcast Transcription and Recommendation Extractor
Starts with Louis Theroux Podcast as proof of concept
"""

import xml.etree.ElementTree as ET
import feedparser
import requests
from pathlib import Path
import json
import re
from urllib.parse import urlparse


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


def get_louis_theroux_feed(opml_file):
    """Extract specifically the Louis Theroux Podcast feed"""
    feeds = parse_opml(opml_file)

    for feed in feeds:
        if 'Louis Theroux Podcast' in feed['title']:
            print(f"Found: {feed['title']}")
            print(f"RSS URL: {feed['url']}")
            return feed

    return None


def fetch_episodes(rss_url, limit=None):
    """Fetch and parse RSS feed to get episode information"""
    print(f"\nFetching RSS feed from {rss_url}...")
    feed = feedparser.parse(rss_url)

    episodes = []
    entries = feed.entries[:limit] if limit else feed.entries

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
            'description': entry.get('summary', '')[:200] + '...' if entry.get('summary') else ''
        }
        episodes.append(episode)

    return episodes


def sanitize_filename(title):
    """Convert episode title to safe filename"""
    # Remove or replace invalid filename characters
    filename = re.sub(r'[<>:"/\\|?*]', '', title)
    # Replace multiple spaces with single space
    filename = re.sub(r'\s+', ' ', filename)
    # Limit length
    filename = filename[:150]
    return filename.strip()


def download_episode(episode, output_dir="episodes"):
    """Download a podcast episode"""
    if not episode['audio_url']:
        print(f"✗ No audio URL found for episode: {episode['title']}")
        return None

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # Generate filename
    safe_title = sanitize_filename(episode['title'])
    file_extension = Path(urlparse(episode['audio_url']).path).suffix or '.mp3'
    filename = output_path / f"{safe_title}{file_extension}"

    # Check if already downloaded
    if filename.exists():
        print(f"✓ Episode already downloaded: {filename}")
        return filename

    # Download the file
    print(f"\nDownloading: {episode['title']}")
    print(f"URL: {episode['audio_url']}")

    try:
        response = requests.get(episode['audio_url'], stream=True)
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

        print(f"\n✓ Downloaded successfully: {filename}")
        return filename

    except Exception as e:
        print(f"\n✗ Error downloading episode: {e}")
        if filename.exists():
            filename.unlink()  # Remove partial download
        return None


if __name__ == "__main__":
    opml_path = Path(__file__).parent / "podocasts.opml"

    print("Parsing OPML file...")
    louis_feed = get_louis_theroux_feed(opml_path)

    if louis_feed:
        print("\n✓ Successfully extracted Louis Theroux Podcast feed!")
        print(f"  Title: {louis_feed['title']}")
        print(f"  URL: {louis_feed['url']}")

        # Fetch recent episodes
        episodes = fetch_episodes(louis_feed['url'], limit=10)
        print(f"\n✓ Found {len(episodes)} recent episodes:")
        print("=" * 80)

        for i, ep in enumerate(episodes, 1):
            print(f"\n{i}. {ep['title']}")
            print(f"   Published: {ep['published']}")
            print(f"   Audio URL: {ep['audio_url'][:60]}..." if ep['audio_url'] else "   Audio URL: Not found")
            if ep['description']:
                print(f"   Description: {ep['description']}")

        # Download the first episode as a test
        if episodes:
            print("\n" + "=" * 80)
            print("Downloading first episode for testing...")
            print("=" * 80)
            downloaded_file = download_episode(episodes[0])

            if downloaded_file:
                print(f"\n✓ Test episode ready for transcription: {downloaded_file}")
            else:
                print("\n✗ Failed to download test episode")

    else:
        print("✗ Could not find Louis Theroux Podcast in OPML file")
