#!/usr/bin/env python3
"""
Patreon Podcast Downloader using Playwright (Real Browser)
Downloads Patreon podcast episodes by scraping download URLs from the website
Uses real Firefox browser to bypass Cloudflare bot detection
"""

import sys
import json
import re
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

def sanitize_filename(title):
    """Convert episode title to safe filename"""
    filename = re.sub(r'[<>:"/\\|?*]', '', title)
    filename = re.sub(r'\s+', ' ', filename)
    filename = filename[:150]
    return filename.strip()


def get_episode_urls_from_rss(rss_url):
    """
    Fetch episode list from RSS feed to get post IDs
    Returns list of (title, post_id) tuples
    """
    import feedparser

    print(f"Fetching RSS feed to get episode list...")
    feed = feedparser.parse(rss_url)

    episodes = []
    for entry in feed.entries:
        title = entry.get('title', 'Unknown')

        # Extract audio URL from enclosures
        audio_url = None
        if hasattr(entry, 'enclosures') and entry.enclosures:
            for enclosure in entry.enclosures:
                if 'audio' in enclosure.get('type', ''):
                    audio_url = enclosure.get('href', '')
                    break

        # Extract post ID from entry link or audio URL
        post_id = None

        # Try to get from link
        link = entry.get('link', '')
        if '/posts/' in link:
            # Extract just the numeric ID from URLs like /posts/episode-418-115925479
            full_id = link.split('/posts/')[-1].split('?')[0]
            # Get just the numbers at the end
            import re
            numbers = re.findall(r'\d+$', full_id)
            if numbers:
                post_id = numbers[0]
            else:
                post_id = full_id

        # Try to get from audio URL if no post ID yet
        if not post_id and audio_url and '/e/' in audio_url:
            post_id = audio_url.split('/e/')[1].split('?')[0]

        if post_id or audio_url:
            episodes.append({
                'title': title,
                'post_id': post_id,
                'audio_url': audio_url,
                'published': entry.get('published', 'Unknown date'),
                'description': entry.get('summary', '')
            })

    print(f"✓ Found {len(episodes)} episodes in RSS feed")
    return episodes


def download_episode_with_browser(episode, podcast_name, page, output_dir=None):
    """
    Download episode using Playwright browser automation

    Args:
        episode: Episode dict with title, post_id, etc.
        podcast_name: Name of the podcast
        page: Playwright page object (already authenticated)
        output_dir: Optional output directory

    Returns:
        Path to downloaded file or None
    """
    post_id = episode['post_id']
    title = episode['title']

    # Default to project root episodes folder
    if output_dir is None:
        script_dir = Path(__file__).parent
        output_dir = script_dir.parent / "episodes"

    # Create podcast-specific directory
    podcast_dir = Path(output_dir) / sanitize_filename(podcast_name)
    podcast_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename
    safe_title = sanitize_filename(title)
    filename = podcast_dir / f"{safe_title}.mp3"

    # Check if already downloaded
    if filename.exists():
        file_size_mb = filename.stat().st_size / (1024 * 1024)
        if file_size_mb < 1.0:
            print(f"⚠️  Partial download detected ({file_size_mb:.2f} MB), re-downloading: {filename.name}")
            filename.unlink()
        else:
            print(f"✓ Already downloaded: {filename.name} ({file_size_mb:.1f} MB)")
            return filename

    print(f"\nDownloading: {title}")

    try:
        # Use audio URL from RSS feed if available
        download_url = episode.get('audio_url')

        if download_url:
            print(f"  Using audio URL from RSS feed")
        else:
            print(f"  No audio URL in RSS feed, cannot download")
            return None

        print(f"  Download URL: {download_url[:100]}...")

        # Use the browser context's request API to download
        # This uses all cookies/headers but doesn't navigate the page (avoids Cloudflare)
        print(f"  Fetching audio file...")
        response = page.request.get(download_url)

        if response.status != 200:
            print(f"✗ Download failed with status {response.status}")
            return None

        # Write the file
        with open(filename, 'wb') as f:
            f.write(response.body())

        file_size_mb = filename.stat().st_size / (1024 * 1024)
        print(f"✓ Downloaded: {filename.name} ({file_size_mb:.1f} MB)")

        # Save metadata
        metadata = {
            'title': episode['title'],
            'published': episode['published'],
            'description': episode['description'],
            'audio_file': str(filename),
            'post_id': post_id,
            'download_url': download_url
        }

        metadata_file = filename.with_suffix('.json')
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        return filename

    except Exception as e:
        print(f"✗ Error downloading episode: {e}")
        if filename.exists():
            filename.unlink()  # Remove partial download
        return None


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Patreon Podcast Downloader with Browser Automation")
        print("\nUsage: python patreon_browser_downloader.py <rss_feed_url> [episode_limit]")
        print("\nThis script uses Firefox automation to download episodes.")
        print("You must be logged into Patreon in Firefox first.")
        print("\nExamples:")
        print("  python patreon_browser_downloader.py 'https://www.patreon.com/rss/...'")
        print("  python patreon_browser_downloader.py 'https://www.patreon.com/rss/...' 5")
        return

    rss_url = sys.argv[1]
    episode_limit = int(sys.argv[2]) if len(sys.argv) > 2 else None

    print("=" * 80)
    print("Patreon Podcast Downloader (Browser Automation)")
    print("=" * 80)

    # Get episode list from RSS
    episodes = get_episode_urls_from_rss(rss_url)

    if not episodes:
        print("✗ No episodes found in RSS feed")
        return

    # Limit episodes if specified
    if episode_limit:
        episodes = episodes[:episode_limit]
        print(f"Limiting to {episode_limit} episodes")

    # Launch browser
    print("\nLaunching browser...")

    with sync_playwright() as p:
        # Launch Firefox in non-headless mode to allow manual login if needed
        browser = p.firefox.launch(
            headless=False
        )

        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:145.0) Gecko/20100101 Firefox/145.0'
        )

        page = context.new_page()

        # Try to load cookies from file first
        cookie_file = Path(__file__).parent.parent / "patreon_cookies.txt"
        if cookie_file.exists():
            print("Loading cookies from file...")
            try:
                with open(cookie_file, 'r') as f:
                    cookie_string = f.read().strip()

                cookies = []
                for item in cookie_string.split(';'):
                    item = item.strip()
                    if '=' in item:
                        key, value = item.split('=', 1)
                        cookies.append({
                            'name': key.strip(),
                            'value': value.strip(),
                            'domain': '.patreon.com',
                            'path': '/'
                        })

                context.add_cookies(cookies)
                print(f"✓ Loaded {len(cookies)} cookies")
            except Exception as e:
                print(f"⚠️  Could not load cookies: {e}")

        # Test authentication by visiting Patreon
        print("Checking Patreon authentication...")
        page.goto("https://www.patreon.com", wait_until="networkidle")

        # Check if logged in (look for login button)
        if page.locator('a:has-text("Log in"), button:has-text("Log in")').count() > 0:
            print("\n⚠️  Not logged into Patreon!")
            print("Please log in to Patreon in the browser window that just opened.")
            print("Press Enter after logging in...")
            input()
            page.reload(wait_until="networkidle")

        print("✓ Authenticated with Patreon")

        # Download episodes
        print("\n" + "=" * 80)
        print("Starting downloads...")
        print("=" * 80)

        downloaded = []
        for i, episode in enumerate(episodes, 1):
            print(f"\n[{i}/{len(episodes)}]")
            result = download_episode_with_browser(
                episode,
                "TRUE ANON TRUTH FEED",
                page
            )
            if result:
                downloaded.append(result)

            # Small delay between downloads
            time.sleep(2)

        browser.close()

    print("\n" + "=" * 80)
    print(f"✓ Download complete! {len(downloaded)}/{len(episodes)} episodes downloaded")
    print(f"  Location: episodes/TRUE ANON TRUTH FEED/")
    print("=" * 80)


if __name__ == "__main__":
    main()
