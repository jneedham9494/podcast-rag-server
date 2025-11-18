#!/usr/bin/env python3
"""
Podcast Metadata Scraper
Scrapes all episode metadata from podcast RSS feeds and saves to JSON files
"""

import xml.etree.ElementTree as ET
import feedparser
from pathlib import Path
import json
import sys
from datetime import datetime


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


def sanitize_filename(title):
    """Convert podcast title to safe filename"""
    import re
    # Remove or replace invalid filename characters
    filename = re.sub(r'[<>:"/\\|?*]', '', title)
    # Replace multiple spaces with single space
    filename = re.sub(r'\s+', ' ', filename)
    # Limit length
    filename = filename[:150]
    return filename.strip()


def scrape_feed_metadata(feed_url, podcast_title):
    """
    Scrape all episode metadata from a podcast RSS feed

    Returns:
        Dictionary with podcast info and all episodes
    """
    print(f"Scraping: {podcast_title}")

    try:
        feed = feedparser.parse(feed_url)

        # Get podcast-level metadata
        podcast_metadata = {
            'podcast_title': podcast_title,
            'podcast_description': feed.feed.get('subtitle', feed.feed.get('description', '')),
            'podcast_author': feed.feed.get('author', ''),
            'podcast_language': feed.feed.get('language', ''),
            'podcast_image': feed.feed.get('image', {}).get('href', ''),
            'feed_url': feed_url,
            'last_checked': datetime.now().isoformat(),
            'total_episodes': len(feed.entries),
            'episodes': []
        }

        # Get all episode metadata
        for entry in feed.entries:
            # Find audio URL and file size
            audio_url = None
            audio_size = None
            audio_type = None

            if hasattr(entry, 'enclosures') and entry.enclosures:
                for enclosure in entry.enclosures:
                    if 'audio' in enclosure.get('type', ''):
                        audio_url = enclosure.get('href', '')
                        audio_size = enclosure.get('length', 0)
                        audio_type = enclosure.get('type', '')
                        break

            # Calculate duration if available
            duration = None
            if hasattr(entry, 'itunes_duration'):
                duration = entry.itunes_duration

            episode = {
                'title': entry.get('title', 'Unknown'),
                'published': entry.get('published', 'Unknown date'),
                'published_parsed': entry.get('published_parsed', None),
                'description': entry.get('summary', ''),
                'audio_url': audio_url,
                'audio_size_bytes': int(audio_size) if audio_size else None,
                'audio_size_mb': round(int(audio_size) / (1024*1024), 1) if audio_size else None,
                'audio_type': audio_type,
                'duration': duration,
                'guid': entry.get('id', entry.get('link', '')),
                'link': entry.get('link', ''),
                'author': entry.get('author', ''),
                'season': entry.get('itunes_season', None),
                'episode_number': entry.get('itunes_episode', None),
            }

            podcast_metadata['episodes'].append(episode)

        print(f"  ✓ Found {len(feed.entries)} episodes")
        return podcast_metadata

    except Exception as e:
        print(f"  ✗ Error scraping feed: {e}")
        return {
            'podcast_title': podcast_title,
            'feed_url': feed_url,
            'last_checked': datetime.now().isoformat(),
            'error': str(e),
            'total_episodes': 0,
            'episodes': []
        }


def scrape_all_feeds(opml_file, output_dir="podcast_metadata"):
    """
    Scrape metadata from all feeds in OPML file

    Args:
        opml_file: Path to OPML file
        output_dir: Directory to save metadata files
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    print("Parsing OPML file...")
    feeds = parse_opml(opml_file)
    print(f"Found {len(feeds)} podcast feeds\n")

    print("=" * 80)
    print("Scraping metadata from all feeds...")
    print("=" * 80)

    results = []
    successful = 0
    failed = 0

    for i, feed in enumerate(feeds, 1):
        print(f"\n[{i}/{len(feeds)}]")

        metadata = scrape_feed_metadata(feed['url'], feed['title'])

        if metadata.get('error'):
            failed += 1
        else:
            successful += 1

        # Save individual podcast metadata file
        safe_filename = sanitize_filename(feed['title'])
        metadata_file = output_path / f"{safe_filename}.json"

        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False, default=str)

        results.append({
            'podcast': feed['title'],
            'episodes': metadata.get('total_episodes', 0),
            'file': str(metadata_file)
        })

    # Create index file
    index = {
        'generated_at': datetime.now().isoformat(),
        'total_podcasts': len(feeds),
        'successful': successful,
        'failed': failed,
        'podcasts': results
    }

    index_file = output_path / "index.json"
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80)
    print(f"✓ Scraping complete!")
    print(f"  Podcasts processed: {len(feeds)}")
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")
    print(f"  Total episodes found: {sum(r['episodes'] for r in results)}")
    print(f"  Metadata saved to: {output_dir}/")
    print(f"  Index file: {index_file}")
    print("=" * 80)


def search_metadata(search_term, metadata_dir="podcast_metadata"):
    """
    Search through all podcast metadata for episodes matching search term

    Args:
        search_term: Term to search for in titles/descriptions
        metadata_dir: Directory containing metadata files
    """
    metadata_path = Path(metadata_dir)

    if not metadata_path.exists():
        print(f"✗ Metadata directory not found: {metadata_dir}")
        print("  Run scraper first to generate metadata")
        return

    print(f"Searching for: '{search_term}'")
    print("=" * 80)

    results = []
    metadata_files = list(metadata_path.glob("*.json"))
    metadata_files = [f for f in metadata_files if f.name != "index.json"]

    for metadata_file in metadata_files:
        with open(metadata_file, 'r', encoding='utf-8') as f:
            podcast = json.load(f)

        for episode in podcast.get('episodes', []):
            title = episode.get('title', '').lower()
            description = episode.get('description', '').lower()

            if search_term.lower() in title or search_term.lower() in description:
                results.append({
                    'podcast': podcast['podcast_title'],
                    'episode': episode['title'],
                    'published': episode['published'],
                    'size_mb': episode.get('audio_size_mb'),
                    'description': episode['description'][:200] + '...' if len(episode.get('description', '')) > 200 else episode.get('description', '')
                })

    print(f"Found {len(results)} matching episodes:\n")

    for i, result in enumerate(results[:50], 1):  # Limit to 50 results
        print(f"{i}. [{result['podcast']}] {result['episode']}")
        print(f"   Published: {result['published']}")
        if result['size_mb']:
            print(f"   Size: {result['size_mb']} MB")
        print(f"   {result['description']}\n")

    if len(results) > 50:
        print(f"... and {len(results) - 50} more results")


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Podcast Metadata Scraper")
        print("\nUsage:")
        print("  Scrape all feeds:  python podcast_metadata_scraper.py scrape")
        print("  Search metadata:   python podcast_metadata_scraper.py search <term>")
        print("\nExamples:")
        print("  python podcast_metadata_scraper.py scrape")
        print("  python podcast_metadata_scraper.py search 'artificial intelligence'")
        print("  python podcast_metadata_scraper.py search 'music'")
        return

    command = sys.argv[1]

    if command == "scrape":
        opml_path = Path(__file__).parent / "podocasts.opml"
        scrape_all_feeds(opml_path)

    elif command == "search":
        if len(sys.argv) < 3:
            print("✗ Please provide a search term")
            print("  Example: python podcast_metadata_scraper.py search 'books'")
            return

        search_term = sys.argv[2]
        search_metadata(search_term)

    else:
        print(f"✗ Unknown command: {command}")
        print("  Use 'scrape' or 'search'")


if __name__ == "__main__":
    main()
