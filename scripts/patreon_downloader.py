#!/usr/bin/env python3
"""
Patreon Podcast Downloader with Browser Cookie Authentication
Downloads Patreon podcast episodes using browser cookies to bypass API restrictions
"""

import sys
import json
import re
import requests
import feedparser
from pathlib import Path
from urllib.parse import urlparse

try:
    import browser_cookie3
    BROWSER_COOKIE_AVAILABLE = True
except ImportError:
    BROWSER_COOKIE_AVAILABLE = False
    print("⚠️  browser-cookie3 not installed. Install with: pip3 install browser-cookie3")


def sanitize_filename(title):
    """Convert episode title to safe filename"""
    filename = re.sub(r'[<>:"/\\|?*]', '', title)
    filename = re.sub(r'\s+', ' ', filename)
    filename = filename[:150]
    return filename.strip()


def get_manual_cookies():
    """
    Load cookies from patreon_cookies.txt file

    Returns:
        dict with cookies or None
    """
    cookie_file = Path(__file__).parent.parent / "patreon_cookies.txt"

    if not cookie_file.exists():
        print(f"✗ Cookie file not found: {cookie_file}")
        print("  Create patreon_cookies.txt with your browser cookies")
        print("  See PATREON_COOKIE_GUIDE.md for instructions")
        return None

    try:
        with open(cookie_file, 'r') as f:
            cookie_string = f.read().strip()

        if not cookie_string:
            print("✗ Cookie file is empty")
            return None

        # Parse cookie string into dict
        cookies = {}
        for item in cookie_string.split(';'):
            item = item.strip()
            if '=' in item:
                key, value = item.split('=', 1)
                cookies[key.strip()] = value.strip()

        print(f"✓ Loaded {len(cookies)} cookies from file")
        return cookies

    except Exception as e:
        print(f"✗ Error reading cookie file: {e}")
        return None


def get_browser_cookies(domain='patreon.com', browser='chrome'):
    """
    Extract cookies from browser for specified domain

    Args:
        domain: Domain to get cookies for
        browser: Browser to extract from ('chrome', 'firefox', 'safari', 'edge', 'chromium')

    Returns:
        RequestsCookieJar with cookies
    """
    if not BROWSER_COOKIE_AVAILABLE:
        print("✗ browser-cookie3 library not available")
        return None

    try:
        print(f"Extracting cookies from {browser.title()}...")

        if browser.lower() == 'chrome':
            cookies = browser_cookie3.chrome(domain_name=domain)
        elif browser.lower() == 'firefox':
            cookies = browser_cookie3.firefox(domain_name=domain)
        elif browser.lower() == 'safari':
            cookies = browser_cookie3.safari(domain_name=domain)
        elif browser.lower() == 'edge':
            cookies = browser_cookie3.edge(domain_name=domain)
        elif browser.lower() == 'chromium':
            cookies = browser_cookie3.chromium(domain_name=domain)
        else:
            # Try all browsers
            cookies = browser_cookie3.load(domain_name=domain)

        cookie_count = len(list(cookies))
        if cookie_count > 0:
            print(f"✓ Found {cookie_count} cookies for {domain}")
            return cookies
        else:
            print(f"✗ No cookies found for {domain}. Make sure you're logged into Patreon in {browser.title()}.")
            return None

    except Exception as e:
        print(f"✗ Error extracting cookies: {e}")
        print(f"   Make sure {browser.title()} is closed and you've logged into Patreon at least once.")
        return None


def fetch_patreon_feed(rss_url, cookies=None):
    """
    Fetch Patreon RSS feed with authentication

    Args:
        rss_url: Patreon RSS feed URL
        cookies: Optional browser cookies (dict or RequestsCookieJar)

    Returns:
        tuple: (episodes list, session with cookies)
    """
    print(f"Fetching Patreon RSS feed...")

    session = requests.Session()

    # Add cookies if provided
    if cookies:
        if isinstance(cookies, dict):
            # Manual cookies from file
            session.cookies.update(cookies)
            print("✓ Using manual cookies for authentication")
        else:
            # Browser-extracted cookies (RequestsCookieJar)
            session.cookies = cookies
            print("✓ Using browser cookies for authentication")

    # Set headers to mimic Firefox with all security headers that Cloudflare expects
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:145.0) Gecko/20100101 Firefox/145.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'DNT': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Sec-GPC': '1',
        'Upgrade-Insecure-Requests': '1',
        'Priority': 'u=0, i',
    })

    try:
        response = session.get(rss_url, timeout=30)
        response.raise_for_status()

        feed = feedparser.parse(response.content)

        episodes = []
        for entry in feed.entries:
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

        print(f"✓ Found {len(episodes)} episodes in feed")
        return episodes, session

    except Exception as e:
        print(f"✗ Error fetching RSS feed: {e}")
        return [], None


def download_episode(episode, podcast_name, session, output_dir=None, rss_url=None):
    """
    Download a Patreon podcast episode using authenticated session

    Args:
        episode: Episode dict with title, audio_url, etc.
        podcast_name: Name of the podcast
        session: Requests session with authentication cookies
        output_dir: Optional output directory
        rss_url: RSS feed URL (to refetch fresh download URLs if needed)

    Returns:
        Path to downloaded file or None
    """
    if not episode['audio_url']:
        print(f"✗ No audio URL found for episode: {episode['title']}")
        return None

    # Default to project root episodes folder
    if output_dir is None:
        script_dir = Path(__file__).parent
        output_dir = script_dir.parent / "episodes"

    # Create podcast-specific directory
    podcast_dir = Path(output_dir) / sanitize_filename(podcast_name)
    podcast_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename
    safe_title = sanitize_filename(episode['title'])
    file_extension = Path(urlparse(episode['audio_url']).path).suffix or '.mp3'
    filename = podcast_dir / f"{safe_title}{file_extension}"

    # Check if already downloaded
    if filename.exists():
        file_size_mb = filename.stat().st_size / (1024 * 1024)
        if file_size_mb < 1.0:
            print(f"⚠️  Partial download detected ({file_size_mb:.2f} MB), re-downloading: {filename.name}")
            filename.unlink()
        else:
            print(f"✓ Already downloaded: {filename.name} ({file_size_mb:.1f} MB)")
            return filename

    # Refetch RSS feed to get fresh download URL with valid signature
    if rss_url:
        print(f"  [Fetching fresh download URL...]")
        try:
            response = session.get(rss_url, timeout=30)
            response.raise_for_status()
            feed = feedparser.parse(response.content)

            # Find matching episode by title
            for entry in feed.entries:
                if entry.get('title', '') == episode['title']:
                    # Update with fresh audio URL
                    if hasattr(entry, 'enclosures') and entry.enclosures:
                        for enclosure in entry.enclosures:
                            if 'audio' in enclosure.get('type', ''):
                                episode['audio_url'] = enclosure.get('href', '')
                                print(f"  [Got fresh URL with new signature]")
                                break
                    break
        except Exception as e:
            print(f"  [Warning: Could not refetch feed: {e}]")

    # Download the file
    print(f"\nDownloading: {episode['title']}")
    print(f"  From: {episode['audio_url'][:80]}...")

    try:
        # Use the authenticated session
        response = session.get(episode['audio_url'], stream=True, timeout=120, allow_redirects=True)

        # Check if we got redirected to actual file
        if response.status_code == 200:
            print(f"  [Download URL resolved successfully]")

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
                        print(f"\r  Progress: {percent:.1f}% ({downloaded / (1024*1024):.1f} MB)", end='')

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
        print("Patreon Podcast Downloader with Cookie Authentication")
        print("\nUsage: python patreon_downloader.py <rss_feed_url> [episode_limit] [OPTIONS]")
        print("\nOptions:")
        print("  --manual-cookies    Use cookies from patreon_cookies.txt file")
        print("  --browser=BROWSER   Extract cookies from browser (chrome, firefox, safari, edge)")
        print("\nExamples:")
        print("  python patreon_downloader.py 'https://www.patreon.com/rss/...' --manual-cookies")
        print("  python patreon_downloader.py 'https://www.patreon.com/rss/...' 5 --manual-cookies")
        print("  python patreon_downloader.py 'https://www.patreon.com/rss/...' --browser=firefox")
        print("\nFor manual cookies, see PATREON_COOKIE_GUIDE.md for setup instructions")
        return

    rss_url = sys.argv[1]
    episode_limit = None
    browser = 'chrome'
    use_manual = False

    # Parse arguments
    for arg in sys.argv[2:]:
        if arg == '--manual-cookies':
            use_manual = True
        elif arg.startswith('--browser='):
            browser = arg.split('=')[1].lower()
        elif arg.isdigit():
            episode_limit = int(arg)

    print("=" * 80)
    print("Patreon Podcast Downloader")
    print("=" * 80)

    # Get cookies
    if use_manual:
        cookies = get_manual_cookies()
        if not cookies:
            print("\n⚠️  Could not load manual cookies. Please:")
            print("  1. Create patreon_cookies.txt in the project root")
            print("  2. Add your browser cookies to the file")
            print("  3. See PATREON_COOKIE_GUIDE.md for instructions")
            return
    else:
        # Extract cookies from browser
        cookies = get_browser_cookies(domain='patreon.com', browser=browser)
        if not cookies:
            print("\n⚠️  Could not extract cookies from browser. Try --manual-cookies instead:")
            print("  python patreon_downloader.py <rss_url> --manual-cookies")
            print("\n  Or ensure:")
            print("  1. You're logged into Patreon in your browser")
            print("  2. Your browser is completely closed")
            print("  3. You have browser-cookie3 installed: pip3 install browser-cookie3")
            return

    # Fetch episodes
    episodes, session = fetch_patreon_feed(rss_url, cookies=cookies)

    if not episodes:
        print("✗ No episodes found or feed inaccessible")
        return

    # Limit episodes if specified
    if episode_limit:
        episodes = episodes[:episode_limit]
        print(f"Limiting to {episode_limit} episodes")

    # Download episodes
    print("\n" + "=" * 80)
    print("Starting downloads...")
    print("=" * 80)

    downloaded = []
    for i, episode in enumerate(episodes, 1):
        print(f"\n[{i}/{len(episodes)}]")
        result = download_episode(episode, "TRUE ANON TRUTH FEED", session, rss_url=rss_url)
        if result:
            downloaded.append(result)

    print("\n" + "=" * 80)
    print(f"✓ Download complete! {len(downloaded)}/{len(episodes)} episodes downloaded")
    print(f"  Location: episodes/TRUE ANON TRUTH FEED/")
    print("=" * 80)


if __name__ == "__main__":
    main()
