"""
Feed analysis utilities for tracking podcast progress.
"""

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any
import feedparser


def get_book_scores() -> Dict[str, int]:
    """
    Get book recommendation likelihood scores for podcasts.

    Returns:
        Dictionary mapping podcast name to score (1-10)
    """
    return {
        'THE ADAM BUXTON PODCAST': 10,
        'The Louis Theroux Podcast': 9,
        'Grounded with Louis Theroux': 9,
        'RHLSTP with Richard Herring': 8,
        'I Like Films with Jonathan Ross': 8,
        'Odd Lots': 8,
        "Stephen Fry's 7 Deadly Sins": 9,
        'Say Why To Drugs': 7,
        'Things Fell Apart': 7,
        'Talking Politics: HISTORY OF IDEAS': 8,
        'Blowback': 6,
        'Chapo Trap House': 7,
        'TRUE ANON TRUTH FEED': 6,
        'TrueAnon': 6,
        'The Adam Friedland Show Podcast': 3,
        'Hello Internet': 8,
        'Bad Bets': 7,
        'Cyber Hack': 6,
        'The Missing Cryptoqueen': 7,
        'Fear&': 6,
        'Block Stars with David Schwartz': 6,
        'Witch': 6,
        'Burn Wild': 5,
        'A Podcast Of Unnecessary Detail': 4,
        'The Loud And Quiet Podcast': 4,
        'My Friend Podcast with Paige Elkington with Ruby Caster': 2,
        'Couples Therapy with Candice and Casey': 2,
        'The Always Sunny Podcast': 3,
        'The Yard': 2,
        'Sad Boyz': 2,
        'Cox n Crendor Show': 2,
        'Jimquisition': 2,
        'Arseblog Arsecast, The Arsenal Podcast': 1,
        'Joshua Citarella': 5,
        'Multipolarity': 5,
        'Fin vs History': 4,
        '5CAST w Andrew Callaghan': 5,
    }


def normalize_title(title: str) -> str:
    """
    Normalize episode title for comparison.

    Args:
        title: Episode title

    Returns:
        Normalized title (lowercase, alphanumeric only)
    """
    title = title.lower()
    title = re.sub(r'[^a-z0-9]', '', title)
    return title


def count_rss_duplicates(url: str) -> int:
    """
    Count duplicate entries in an RSS feed.

    Args:
        url: RSS feed URL

    Returns:
        Number of duplicate entries
    """
    try:
        feed = feedparser.parse(url)
        seen_titles = set()
        duplicates = 0

        for entry in feed.entries:
            title = entry.get('title', '')
            normalized = normalize_title(title)

            if normalized in seen_titles:
                duplicates += 1
            else:
                seen_titles.add(normalized)

        return duplicates
    except Exception:
        return 0


def fetch_rss_totals() -> Dict[str, int]:
    """
    Fetch episode counts from all RSS feeds.

    Returns:
        Dictionary mapping podcast name to episode count
    """
    print("Fetching RSS episode counts...", end='', flush=True)

    opml_path = Path('podocasts.opml')
    metadata_dir = Path('podcast_metadata')
    totals: Dict[str, int] = {}
    failed_feeds: List[str] = []
    feeds_with_duplicates: List[tuple] = []

    # Manual adjustments for feeds with known issues
    rss_adjustments = {
        'Blowback': 10,  # Archived episodes not in RSS
        'Hello Internet': 1,  # Missing archived episode
    }

    if not opml_path.exists():
        print(" no OPML file found")
        return totals

    tree = ET.parse(opml_path)
    root = tree.getroot()

    for outline in root.findall('.//outline[@type="rss"]'):
        title = outline.get('text', '')
        url = outline.get('xmlUrl', '')

        if title and url:
            try:
                feed = feedparser.parse(url)

                # Count episodes with audio only
                audio_episodes = []
                for entry in feed.entries:
                    has_audio = False
                    if hasattr(entry, 'enclosures') and entry.enclosures:
                        for enclosure in entry.enclosures:
                            if 'audio' in enclosure.get('type', ''):
                                has_audio = True
                                break
                    if has_audio:
                        audio_episodes.append(entry)

                entry_count = len(audio_episodes)

                # Check if RSS feed failed
                if entry_count == 0 or getattr(feed, 'status', 200) >= 400:
                    # Fallback to cached metadata
                    metadata_file = metadata_dir / f"{title}.json"
                    if metadata_file.exists():
                        with open(metadata_file, 'r') as f:
                            data = json.load(f)
                            cached_count = len(data.get('episodes', []))
                            totals[title] = cached_count
                            failed_feeds.append(title)
                    else:
                        totals[title] = 0
                else:
                    # Count duplicates
                    duplicate_count = count_rss_duplicates(url)

                    # Subtract duplicates from total
                    adjusted_count = entry_count - duplicate_count

                    # Apply manual adjustment
                    if title in rss_adjustments:
                        adjustment = rss_adjustments[title]
                        adjusted_count += adjustment

                    totals[title] = adjusted_count

                    if duplicate_count > 0:
                        feeds_with_duplicates.append((title, duplicate_count))

            except Exception:
                # Fallback to cached metadata
                metadata_file = metadata_dir / f"{title}.json"
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        data = json.load(f)
                        totals[title] = len(data.get('episodes', []))
                        failed_feeds.append(title)
                else:
                    totals[title] = 0

    status_msg = f" done ({len(totals)} feeds"
    if failed_feeds:
        status_msg += f", {len(failed_feeds)} using cached"
    if feeds_with_duplicates:
        status_msg += f", {len(feeds_with_duplicates)} with duplicates"
    status_msg += ")\n"
    print(status_msg)

    return totals


def get_feed_progress(
    rss_totals: Dict[str, int],
    book_scores: Dict[str, int]
) -> List[Dict[str, Any]]:
    """
    Get progress for each feed.

    Args:
        rss_totals: RSS episode counts per podcast
        book_scores: Book recommendation scores per podcast

    Returns:
        List of feed progress dictionaries
    """
    episodes_dir = Path('episodes')
    transcripts_dir = Path('transcripts')

    results: List[Dict[str, Any]] = []

    if not episodes_dir.exists():
        return results

    for podcast_dir in sorted(episodes_dir.iterdir()):
        if not podcast_dir.is_dir():
            continue

        name = podcast_dir.name

        # Count downloaded episodes (100KB threshold for valid files)
        audio_files = (
            list(podcast_dir.glob('*.mp3')) +
            list(podcast_dir.glob('*.m4a')) +
            list(podcast_dir.glob('*.wav'))
        )
        valid_files = [f for f in audio_files if f.stat().st_size > 100 * 1024]
        downloaded = len(valid_files)

        if downloaded == 0:
            continue

        # Get total from cached RSS data
        total = rss_totals.get(name, downloaded)

        # Count transcripts and enriched transcripts
        transcribed = 0
        enriched = 0
        if transcripts_dir.exists():
            trans_dirs = list(transcripts_dir.glob(f'*{name}*'))
            if not trans_dirs:
                trans_dir = transcripts_dir / name
                if trans_dir.exists():
                    trans_dirs = [trans_dir]

            if trans_dirs:
                trans_dir = trans_dirs[0]
                txt_files = list(trans_dir.glob('*.txt'))
                transcribed = len(txt_files)
                enriched_files = list(trans_dir.glob('*_enriched.json'))
                enriched = len(enriched_files)

        # Calculate remaining
        remaining = total - downloaded
        trans_remaining = downloaded - transcribed
        enrich_remaining = transcribed - enriched

        # Get book score
        book_score = book_scores.get(name, 3)

        # Cap transcribed at downloaded
        transcribed = min(transcribed, downloaded)
        trans_remaining = downloaded - transcribed

        results.append({
            'name': name,
            'total': total,
            'downloaded': downloaded,
            'transcribed': transcribed,
            'enriched': enriched,
            'remaining': remaining,
            'trans_remaining': trans_remaining,
            'enrich_remaining': enrich_remaining,
            'book_score': book_score,
            'dl_pct': (downloaded / total * 100) if total > 0 else 0,
            'tr_pct': (transcribed / downloaded * 100) if downloaded > 0 else 0,
            'en_pct': (enriched / transcribed * 100) if transcribed > 0 else 0,
            'is_dl_complete': downloaded == total,
            'is_tr_complete': transcribed == downloaded and downloaded > 0,
            'is_en_complete': enriched == transcribed and transcribed > 0
        })

    # Sort by priority
    results.sort(key=lambda x: (x['remaining'], -x['book_score']))
    return results


def check_feed_failure(feed_name: str) -> bool:
    """
    Check if a feed's last download attempt failed.

    Args:
        feed_name: Name of the feed to check

    Returns:
        True if last attempt failed, False otherwise
    """
    log_dir = Path('logs')
    log_file = log_dir / f'download_{feed_name.replace("/", "_")}.log'

    if not log_file.exists():
        return False

    try:
        with open(log_file, 'r') as f:
            lines = f.readlines()
            last_lines = lines[-50:] if len(lines) > 50 else lines

        error_indicators = [
            'rate limit',
            'too many requests',
            '429',
            'HTTPError',
            'ConnectionError',
            'Timeout',
            '✗ Error downloading'
        ]

        for line in last_lines:
            line_lower = line.lower()
            if any(indicator.lower() in line_lower for indicator in error_indicators):
                return True

        # Check if last line indicates completion
        if last_lines and ('Download complete' in last_lines[-1] or '✓' in last_lines[-1]):
            return False

    except Exception:
        pass

    return False
