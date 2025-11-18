#!/usr/bin/env python3
"""
Live Progress Monitor
Displays real-time progress of podcast downloads and transcriptions per feed
"""

import os
import sys
import time
import subprocess
import json
from pathlib import Path
from datetime import datetime
import xml.etree.ElementTree as ET
import feedparser

def clear_screen():
    os.system('clear' if os.name != 'nt' else 'cls')

def get_worker_counts():
    """Count active download, transcription, and enrichment workers and get their feed names"""
    result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)

    # Count actual processes (not unique feeds)
    dl_count = 0
    tr_count = 0
    en_count = 0

    # Track unique feed names for display
    dl_feeds = set()
    tr_feeds = set()
    en_feeds = set()

    for line in result.stdout.split('\n'):
        if 'podcast_downloader.py' in line and 'grep' not in line:
            dl_count += 1
            # Extract feed name - it comes after 'podcast_downloader.py'
            if 'podcast_downloader.py' in line:
                parts = line.split('podcast_downloader.py')
                if len(parts) > 1:
                    # Everything after podcast_downloader.py is the feed name
                    feed_name = parts[1].strip()
                    if feed_name:
                        dl_feeds.add(feed_name)
        elif 'patreon_downloader.py' in line and 'grep' not in line:
            dl_count += 1
            # Patreon downloader is hardcoded to TRUE ANON TRUTH FEED
            dl_feeds.add('TRUE ANON TRUTH FEED')
        elif 'patreon_browser_downloader.py' in line and 'grep' not in line:
            dl_count += 1
            # Patreon browser downloader is also hardcoded to TRUE ANON TRUTH FEED
            dl_feeds.add('TRUE ANON TRUTH FEED')
        elif 'podcast_transcriber.py' in line and 'grep' not in line:
            tr_count += 1
            # Extract feed name from directory path
            if 'episodes/' in line:
                parts = line.split('episodes/')
                if len(parts) > 1:
                    # Get the directory name after episodes/ up to ' base' or ' large'
                    remaining = parts[1]
                    # Split on ' base' or ' large' to get just the feed name
                    if ' base' in remaining:
                        feed_name = remaining.split(' base')[0].strip()
                    elif ' large' in remaining:
                        feed_name = remaining.split(' large')[0].strip()
                    else:
                        # Fallback: take everything before last space (model name)
                        feed_name = ' '.join(remaining.split()[:-1]).strip()

                    if feed_name:
                        tr_feeds.add(feed_name)
        elif 'enrich_transcript.py' in line and 'grep' not in line:
            en_count += 1
            # Extract feed name from transcript path
            if 'transcripts/' in line:
                parts = line.split('transcripts/')
                if len(parts) > 1:
                    # Get the directory name after transcripts/
                    remaining = parts[1]
                    # Feed name is the first path component
                    feed_name = remaining.split('/')[0].strip()
                    if feed_name:
                        en_feeds.add(feed_name)

    return dl_count, tr_count, en_count, dl_feeds, tr_feeds, en_feeds

def get_book_scores():
    """Book recommendation likelihood scores"""
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
        'Fin vs History': 6,
        'The Loud And Quiet Podcast': 6,
        'A Podcast Of Unnecessary Detail': 5,
        'Multipolarity': 9,
        'Bad Bets': 5,
        'The Missing Cryptoqueen': 6,
        'Cyber Hack': 4,
        'Burn Wild': 5,
        'Witch': 4,
        '5CAST w/ Andrew Callaghan': 7,
        # Political/theory podcasts (book-heavy)
        'Chapo Trap House': 8,
        'TrueAnon': 9,
        'TRUE ANON TRUTH FEED': 9,
        'The Adam Friedland Show Podcast': 2,
        'Jimquisition': 2,
        'The Always Sunny Podcast': 3,
        'Cox n\' Crendor Show': 2,
        'Sad Boyz': 2,
        'The Yard': 2,
        'Joshua Citarella': 3,
        'Fear&': 3,
        'Arseblog Arsecast, The Arsenal Podcast': 1,
        'Couples Therapy with Candice and Casey': 2,
        'Block Stars with David Schwartz': 2,
        'My Friend Podcast with Paige Elkington with Ruby Caster': 2,
        'Hello Internet': 4,
    }

def normalize_title(title: str) -> str:
    """Normalize title for comparison"""
    import re
    normalized = re.sub(r'[^\w\s-]', '', title.lower())
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized

def count_rss_duplicates(url: str) -> int:
    """Count duplicate episodes in RSS feed"""
    try:
        feed = feedparser.parse(url)

        # Get normalized titles of episodes with audio
        normalized_titles = []
        for entry in feed.entries:
            # Only count entries with audio
            has_audio = False
            if hasattr(entry, 'enclosures') and entry.enclosures:
                for enclosure in entry.enclosures:
                    if 'audio' in enclosure.get('type', ''):
                        has_audio = True
                        break

            if has_audio:
                title = entry.get('title', '')
                normalized = normalize_title(title)
                normalized_titles.append(normalized)

        # Count duplicates: total - unique
        unique_count = len(set(normalized_titles))
        duplicate_count = len(normalized_titles) - unique_count

        return duplicate_count
    except Exception:
        return 0

def fetch_rss_totals():
    """Fetch total episode counts from RSS feeds once on startup, accounting for duplicates"""
    print("Fetching RSS feed totals and detecting duplicates...", end='', flush=True)

    # RSS adjustments for feeds with known issues
    # Positive values = we have more files than RSS shows (old episodes archived)
    # Negative values = RSS has bad entries that shouldn't count
    # This allows new episodes to be reflected dynamically while accounting for known issues
    rss_adjustments = {
        'Block Stars with David Schwartz': -1,  # RSS has 1 generic "Block Stars" entry that's invalid
        'TRUE ANON TRUTH FEED': 0,  # RSS has 559, we have 559 (all episodes downloaded!)
        'Joshua Citarella': +14,  # We have 14 extra old episodes (SoundCloud removed them from RSS)
        'Hello Internet': +50,  # We have full archive (126), RSS only shows recent 76
        'Hello Internet Archive': +77,  # Symlink to HI, RSS shows 49, we have full 126 archive
    }
    opml_path = Path('podocasts.opml')
    metadata_dir = Path('podcast_metadata')

    totals = {}

    if not opml_path.exists():
        print(" OPML not found")
        return totals

    tree = ET.parse(opml_path)
    root = tree.getroot()

    feeds_list = list(root.findall('.//outline[@type="rss"]'))
    failed_feeds = []
    feeds_with_duplicates = []

    for outline in feeds_list:
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

                # Check if RSS feed failed (404, 0 entries, or error)
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

                    # Apply manual adjustment if feed has known issues
                    if title in rss_adjustments:
                        adjustment = rss_adjustments[title]
                        adjusted_count += adjustment
                        if adjustment > 0:
                            print(f"  [Adjusted {title}: +{adjustment} archived episodes]")
                        else:
                            print(f"  [Adjusted {title}: {adjustment} bad RSS entries]")

                    totals[title] = adjusted_count

                    if duplicate_count > 0:
                        feeds_with_duplicates.append((title, duplicate_count))

            except Exception:
                # Fallback to cached metadata on exception
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

    # Show feeds with duplicates
    if feeds_with_duplicates:
        print("  Feeds with duplicate RSS entries (adjusted totals):")
        for feed_name, dup_count in feeds_with_duplicates[:5]:
            print(f"    - {feed_name}: {dup_count} duplicates removed")
        if len(feeds_with_duplicates) > 5:
            print(f"    ... and {len(feeds_with_duplicates) - 5} more")
        print()

    return totals

def make_progress_bar(numerator, denominator, width=20):
    """Create a progress bar string"""
    if denominator == 0:
        progress = 0
    else:
        progress = numerator / denominator
    filled = int(width * progress)
    bar = '█' * filled + '░' * (width - filled)
    pct = (progress * 100) if denominator > 0 else 0
    return f"[{bar}] {numerator:>4}/{denominator:<4} {pct:>5.1f}%"

def get_feed_progress(rss_totals, book_scores):
    """Get progress for each feed using cached RSS totals"""
    episodes_dir = Path('episodes')
    transcripts_dir = Path('transcripts')

    results = []

    # Get all podcast directories
    if not episodes_dir.exists():
        return results

    for podcast_dir in sorted(episodes_dir.iterdir()):
        if not podcast_dir.is_dir():
            continue

        name = podcast_dir.name

        # Count downloaded episodes (use 100KB threshold to filter only corrupted/partial files)
        audio_files = list(podcast_dir.glob('*.mp3')) + list(podcast_dir.glob('*.m4a')) + list(podcast_dir.glob('*.wav'))
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
                # Count enriched files (excluding _detailed.json files)
                enriched_files = list(trans_dir.glob('*_enriched.json'))
                enriched = len(enriched_files)

        # Calculate remaining after we have downloaded and transcribed counts
        remaining = total - downloaded
        trans_remaining = downloaded - transcribed
        enrich_remaining = transcribed - enriched

        # Get book score
        book_score = book_scores.get(name, 3)

        # Cap transcribed count at downloaded to prevent >100% (edge case: small files transcribed but not counted)
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

    # Sort by priority: fewest remaining downloads, then book score
    results.sort(key=lambda x: (x['remaining'], -x['book_score']))
    return results

def check_feed_failure(feed_name):
    """Check if a feed's last download attempt failed (rate limiting or other errors)"""
    log_dir = Path('logs')
    log_file = log_dir / f'download_{feed_name.replace("/", "_")}.log'

    if not log_file.exists():
        return False

    try:
        # Read last 50 lines of log file
        with open(log_file, 'r') as f:
            lines = f.readlines()
            last_lines = lines[-50:] if len(lines) > 50 else lines

        # Check for rate limiting or error indicators
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

    except Exception as e:
        pass

    return False

def launch_worker(feed, worker_type='download'):
    """Launch a download or transcription worker for a feed"""
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)

    name = feed['name']

    if worker_type == 'download':
        log_file = log_dir / f'download_{name.replace("/", "_")}.log'

        # Use patreon_downloader for Patreon feeds (TRUE ANON TRUTH FEED)
        if name == 'TRUE ANON TRUTH FEED':
            # Get RSS URL from OPML
            opml_path = Path('podocasts.opml')
            rss_url = None
            if opml_path.exists():
                tree = ET.parse(opml_path)
                root = tree.getroot()
                for outline in root.findall('.//outline[@type="rss"]'):
                    if outline.get('text', '') == name:
                        rss_url = outline.get('xmlUrl', '')
                        break

            if rss_url:
                # Use patreon_downloader with manual cookies
                cmd = ['python3', 'patreon_downloader.py', rss_url, '--manual-cookies']
            else:
                # Fallback to regular downloader if URL not found
                cmd = ['python3', 'podcast_downloader.py', name]
        else:
            # Use regular downloader for non-Patreon feeds
            cmd = ['python3', 'podcast_downloader.py', name]
    else:  # transcription
        if not feed.get('podcast_dir'):
            return None
        log_file = log_dir / f'transcribe_{name.replace("/", "_")}.log'
        cmd = ['python3', 'podcast_transcriber.py', str(feed['podcast_dir']), 'base']

    try:
        with open(log_file, 'w') as f:
            process = subprocess.Popen(
                cmd,
                cwd=Path('scripts'),
                stdout=f,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL
            )
        return process.pid
    except Exception as e:
        print(f'✗ Failed to launch {worker_type} for {name}: {e}')
        return None

def main():
    refresh_interval = 10  # seconds
    TARGET_DOWNLOADERS = 30
    TARGET_TRANSCRIBERS = 6  # Adjusted to 6 for system capacity
    TARGET_ENRICHERS = 20  # Enrichment is IO-bound (waiting on Ollama), can run many
    STALL_THRESHOLD = 5  # Consider feed stalled after N cycles with no progress
    MIN_EPISODES_FOR_MULTIPLE_WORKERS = 50  # Feeds with 50+ remaining episodes can get multiple workers

    # Track which feeds have active workers
    active_dl_feeds = set()
    # Change: track worker count per feed instead of just presence
    active_tr_feeds_count = {}  # {feed_name: worker_count}
    active_en_feeds = set()  # Track enrichment workers

    # Track progress history to detect stalled feeds
    # Format: {feed_name: [downloaded_count1, downloaded_count2, ...]}
    progress_history = {}

    # Exponential backoff tracking for TRUE ANON TRUTH FEED
    backoff_state = {
        'TRUE ANON TRUTH FEED': {
            'failure_count': 0,
            'last_attempt': None,
            'base_delay': 60,  # Start with 60 second delay
            'max_delay': 1800,  # Cap at 30 minutes
            'manual_mode': False,  # Whether we've switched to manual download assistant
            'manual_pid': None,  # PID of manual download assistant process
        }
    }

    MANUAL_FAILOVER_THRESHOLD = 3  # After this many failures, switch to manual mode

    print("Starting live progress monitor with auto-worker management...")
    print(f"Refresh interval: {refresh_interval} seconds")
    print(f"Target: {TARGET_DOWNLOADERS} downloaders, {TARGET_TRANSCRIBERS} transcribers")
    print("Press Ctrl+C to exit")
    print()

    try:
        # Fetch RSS totals once on startup
        rss_totals = fetch_rss_totals()
        book_scores = get_book_scores()
        time.sleep(1)

        while True:
            clear_screen()

            # Header
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print("=" * 130)
            print(f"PODCAST DOWNLOAD & TRANSCRIPTION MONITOR (Auto-Orchestrator Mode)".center(130))
            print(f"{now}".center(130))
            print("=" * 130)
            print()

            # Worker counts
            dl_workers, tr_workers, en_workers, dl_feeds, tr_feeds, en_feeds = get_worker_counts()
            print(f"⚙️  Active Workers: {dl_workers} downloaders (target: {TARGET_DOWNLOADERS}), {tr_workers} transcribers (target: {TARGET_TRANSCRIBERS}), {en_workers} enrichers (target: {TARGET_ENRICHERS})")
            print()

            # Get feed progress
            feeds = get_feed_progress(rss_totals, book_scores)

            # Update progress history to detect stalled feeds
            stalled_feeds = []
            for feed in feeds:
                name = feed['name']
                downloaded = feed['downloaded']
                total = feed.get('total', downloaded)

                # Initialize history if first time seeing this feed
                if name not in progress_history:
                    progress_history[name] = []

                # Append current count
                progress_history[name].append(downloaded)

                # Keep only last N cycles
                if len(progress_history[name]) > STALL_THRESHOLD:
                    progress_history[name].pop(0)

                # Check if stalled: has enough history and no progress AND not complete AND has remaining downloads
                # BUT: if we've downloaded >= RSS total, feed is actually complete (RSS changed/broke)
                # Also exclude feeds that are >99% complete or within 5 episodes (likely complete, RSS just changed)
                completion_pct = (downloaded / total * 100) if total > 0 else 100
                if (len(progress_history[name]) >= STALL_THRESHOLD and
                    len(set(progress_history[name])) == 1 and  # All values are the same
                    not feed['is_dl_complete'] and
                    feed['remaining'] > 0 and
                    feed['remaining'] > 5 and  # Don't mark as stalled if only a few episodes remaining
                    completion_pct < 99.0 and  # Don't mark as stalled if >99% complete
                    downloaded < total):  # Only stalled if we haven't downloaded all available episodes
                    stalled_feeds.append(name)

            # Update backoff state for TRUE ANON TRUTH FEED
            # Check if worker completed and whether it failed
            if 'TRUE ANON TRUTH FEED' in backoff_state:
                feed_name = 'TRUE ANON TRUTH FEED'
                state = backoff_state[feed_name]

                # If we had an active worker that's now gone, check if it failed
                if state['last_attempt'] and feed_name in active_dl_feeds and feed_name not in dl_feeds:
                    # Worker completed, check for failure
                    if check_feed_failure(feed_name):
                        state['failure_count'] += 1
                        print(f"  ⚠️  {feed_name}: Download failed (failure #{state['failure_count']})")

                        # Check if we should switch to manual mode
                        if state['failure_count'] >= MANUAL_FAILOVER_THRESHOLD and not state['manual_mode']:
                            print(f"  🔄 {feed_name}: Switching to manual download assistant after {state['failure_count']} failures")
                            state['manual_mode'] = True

                            # Launch manual download assistant
                            log_dir = Path('logs')
                            log_file = log_dir / 'manual_download_assistant.log'
                            try:
                                with open(log_file, 'w') as f:
                                    process = subprocess.Popen(
                                        ['python3', 'manual_download_assistant.py'],
                                        cwd=Path('scripts'),
                                        stdout=f,
                                        stderr=subprocess.STDOUT,
                                        stdin=subprocess.DEVNULL
                                    )
                                    state['manual_pid'] = process.pid
                                    print(f"  📋 Launched manual download assistant (PID {process.pid})")
                                    print(f"     Check browser for Patreon download prompts!")
                            except Exception as e:
                                print(f"  ✗ Failed to launch manual download assistant: {e}")
                    else:
                        # Success - reset backoff
                        if state['failure_count'] > 0:
                            print(f"  ✓ {feed_name}: Download succeeded, resetting backoff")
                        state['failure_count'] = 0
                        state['manual_mode'] = False

                    # Remove from active tracking
                    active_dl_feeds.discard(feed_name)

            # Launch workers if needed
            if dl_workers < TARGET_DOWNLOADERS:
                needed = TARGET_DOWNLOADERS - dl_workers
                incomplete_feeds = [f for f in feeds if not f['is_dl_complete']]
                for feed in incomplete_feeds[:needed]:
                    # Special rate limiting for TRUE ANON TRUTH FEED (Patreon feed)
                    # This feed can only handle 1 concurrent download at a time + exponential backoff
                    if feed['name'] == 'TRUE ANON TRUTH FEED':
                        # Check if already active
                        if feed['name'] in active_dl_feeds or feed['name'] in dl_feeds:
                            continue

                        # Check if we're in manual mode (don't launch automated downloads)
                        state = backoff_state[feed['name']]
                        if state['manual_mode']:
                            # Check if manual process is still running
                            if state['manual_pid']:
                                try:
                                    os.kill(state['manual_pid'], 0)  # Check if process exists
                                    print(f"  📋 {feed['name']}: Manual download assistant active (PID {state['manual_pid']})")
                                except OSError:
                                    # Process ended, reset manual mode
                                    print(f"  ℹ️  {feed['name']}: Manual download assistant completed, resuming automated downloads")
                                    state['manual_mode'] = False
                                    state['manual_pid'] = None
                                    state['failure_count'] = 0  # Reset failures after manual intervention
                            continue

                        # Check backoff period
                        if state['last_attempt'] and state['failure_count'] > 0:
                            # Calculate exponential backoff delay
                            delay = min(
                                state['base_delay'] * (2 ** (state['failure_count'] - 1)),
                                state['max_delay']
                            )
                            time_since_attempt = time.time() - state['last_attempt']

                            if time_since_attempt < delay:
                                remaining = int(delay - time_since_attempt)
                                mins, secs = divmod(remaining, 60)
                                print(f"  ⏳ {feed['name']}: In backoff period, retry in {mins}m {secs}s (failure #{state['failure_count']})")
                                continue

                    if feed['name'] not in active_dl_feeds and feed['name'] not in dl_feeds:
                        # Add podcast_dir to feed dict for consistency (relative to scripts directory)
                        episodes_dir = Path('../episodes')
                        podcast_dir = episodes_dir / feed['name']
                        # Check against absolute path, but use relative for command
                        if (Path('episodes') / feed['name']).exists():
                            feed['podcast_dir'] = podcast_dir

                        pid = launch_worker(feed, 'download')
                        if pid:
                            active_dl_feeds.add(feed['name'])

                            # Update backoff state for TRUE ANON TRUTH FEED
                            if feed['name'] == 'TRUE ANON TRUTH FEED':
                                backoff_state[feed['name']]['last_attempt'] = time.time()

                            throttle_msg = " [THROTTLED: 1 at a time]" if feed['name'] == 'TRUE ANON TRUTH FEED' else ""
                            print(f"  📥 Launched downloader: {feed['name']} (PID {pid}){throttle_msg}")

            if tr_workers < TARGET_TRANSCRIBERS:
                slots_available = TARGET_TRANSCRIBERS - tr_workers

                # Prioritize feeds with most remaining work
                transcribe_feeds = [f for f in feeds if f['trans_remaining'] > 0]
                transcribe_feeds.sort(key=lambda x: (-x['trans_remaining'], not x['is_dl_complete'], -x['book_score']))

                for feed in transcribe_feeds:
                    if slots_available <= 0:
                        break

                    feed_name = feed['name']
                    current_workers = active_tr_feeds_count.get(feed_name, 0)
                    trans_remaining = feed['trans_remaining']

                    # Determine max workers for this feed
                    # Feeds with 50+ episodes can get multiple workers
                    if trans_remaining >= MIN_EPISODES_FOR_MULTIPLE_WORKERS:
                        # Allow up to min(slots_available, trans_remaining/50) workers
                        max_workers_for_feed = min(slots_available, max(1, trans_remaining // 50))
                    else:
                        max_workers_for_feed = 1

                    # Launch workers if we can
                    workers_to_launch = max_workers_for_feed - current_workers

                    if workers_to_launch > 0:
                        # Add podcast_dir to feed dict (relative to scripts directory)
                        episodes_dir = Path('../episodes')
                        podcast_dir = episodes_dir / feed_name
                        # Check against absolute path, but use relative for command
                        if (Path('episodes') / feed_name).exists():
                            feed['podcast_dir'] = podcast_dir

                        for _ in range(workers_to_launch):
                            if slots_available <= 0:
                                break

                            pid = launch_worker(feed, 'transcribe')
                            if pid:
                                active_tr_feeds_count[feed_name] = active_tr_feeds_count.get(feed_name, 0) + 1
                                slots_available -= 1
                                status = "✓ COMPLETE" if feed['is_dl_complete'] else "  partial"
                                worker_num = active_tr_feeds_count[feed_name]
                                print(f"  📝 Launched transcriber #{worker_num}: {feed_name} (PID {pid}) {status}")

            # Launch enrichment workers if needed
            if en_workers < TARGET_ENRICHERS:
                slots_available = TARGET_ENRICHERS - en_workers

                # Prioritize feeds with most transcripts needing enrichment
                enrich_feeds = [f for f in feeds if f['enrich_remaining'] > 0]
                enrich_feeds.sort(key=lambda x: (-x['enrich_remaining'], -x['book_score']))

                for feed in enrich_feeds:
                    if slots_available <= 0:
                        break

                    feed_name = feed['name']

                    # Skip if already has an enrichment worker
                    if feed_name in active_en_feeds or feed_name in en_feeds:
                        continue

                    # Find the next transcript to enrich
                    # Use absolute path to avoid cwd issues
                    project_root = Path(__file__).parent.parent
                    trans_dir = project_root / 'transcripts' / feed_name
                    if trans_dir.exists():
                        # Get all txt files that don't have enriched versions
                        txt_files = list(trans_dir.glob('*.txt'))
                        for txt_file in txt_files:
                            enriched_file = txt_file.with_name(txt_file.stem + '_enriched.json')
                            if not enriched_file.exists():
                                # Launch enrichment worker for this file
                                log_dir = project_root / 'logs'
                                log_dir.mkdir(exist_ok=True)
                                log_file = log_dir / f'enrich_{feed_name.replace("/", "_")}.log'

                                try:
                                    with open(log_file, 'w') as f:
                                        process = subprocess.Popen(
                                            ['python3', 'enrich_transcript.py', str(txt_file.absolute())],
                                            cwd=project_root / 'scripts',
                                            stdout=f,
                                            stderr=subprocess.STDOUT,
                                            stdin=subprocess.DEVNULL
                                        )
                                    active_en_feeds.add(feed_name)
                                    slots_available -= 1
                                    print(f"  🔍 Launched enricher: {feed_name} - {txt_file.stem} (PID {process.pid})")
                                except Exception as e:
                                    print(f"  ✗ Failed to launch enricher for {feed_name}: {e}")
                                break  # Only one file per feed at a time

            # Remove completed feeds from active tracking
            for feed in feeds:
                if feed['is_dl_complete'] and feed['name'] in active_dl_feeds:
                    active_dl_feeds.discard(feed['name'])
                if feed['is_tr_complete'] and feed['name'] in active_tr_feeds_count:
                    del active_tr_feeds_count[feed['name']]
                if feed['is_en_complete'] and feed['name'] in active_en_feeds:
                    active_en_feeds.discard(feed['name'])
                # Also remove if worker finished (not in en_feeds anymore)
                if feed['name'] in active_en_feeds and feed['name'] not in en_feeds:
                    active_en_feeds.discard(feed['name'])

            print()

            # Calculate totals
            total_available = sum(f['total'] for f in feeds)
            total_downloaded = sum(f['downloaded'] for f in feeds)
            total_transcribed = sum(f['transcribed'] for f in feeds)
            total_enriched = sum(f['enriched'] for f in feeds)

            dl_overall_pct = total_downloaded/total_available*100 if total_available > 0 else 0
            tr_overall_pct = total_transcribed/total_downloaded*100 if total_downloaded > 0 else 0
            en_overall_pct = total_enriched/total_transcribed*100 if total_transcribed > 0 else 0

            print(f"📊 Overall: ⬇ {total_downloaded}/{total_available} downloaded ({dl_overall_pct:.1f}%), "
                  f"📝 {total_transcribed} transcribed ({tr_overall_pct:.1f}%), "
                  f"🔍 {total_enriched} enriched ({en_overall_pct:.1f}%)")
            print()
            print("=" * 130)

            # Display feeds with progress bars, sorted by priority
            print(f"{'PODCAST FEED':<28} {'BK':<3} {'REM':>4}  {'DOWNLOAD':<28} {'TRANSCRIBE':<28} {'ENRICH':<20}")
            print("-" * 130)

            for feed in feeds:
                name = feed['name'][:27]
                book_score = feed['book_score']
                remaining = feed['remaining']

                # Download progress bar (smaller)
                dl_bar = make_progress_bar(feed['downloaded'], feed['total'], 10)

                # Transcription progress bar (smaller)
                tr_bar = make_progress_bar(feed['transcribed'], feed['downloaded'], 10)

                # Enrichment progress bar (smaller)
                en_bar = make_progress_bar(feed['enriched'], feed['transcribed'], 8)

                # Combined status/worker indicators
                # Complete = ✓, In progress = emoji, Neither = space

                # Download status
                if feed['is_dl_complete']:
                    dl_indicator = "✓ "
                elif feed['name'] in dl_feeds:
                    dl_indicator = "⬇ "
                else:
                    dl_indicator = "  "

                # Transcription status
                if feed['is_tr_complete']:
                    tr_indicator = "✓ "
                elif feed['name'] in tr_feeds:
                    worker_count = sum(1 for f in tr_feeds if f == feed['name'])
                    if worker_count > 1:
                        tr_indicator = f"📝{worker_count}"
                    else:
                        tr_indicator = "📝 "
                else:
                    tr_indicator = "  "

                # Enrichment status
                if feed['is_en_complete']:
                    en_indicator = "✓ "
                elif feed['name'] in en_feeds:
                    en_indicator = "🔍 "
                else:
                    en_indicator = "  "

                # Stalled feed indicator
                if feed['name'] in stalled_feeds:
                    dl_indicator = "⚠️"  # Override with stalled warning

                # Color-code book score
                book_indicator = f"{book_score:>2}"

                print(f"{name:<28} {book_indicator:<3} {remaining:>4}  {dl_bar} {dl_indicator} {tr_bar} {tr_indicator} {en_bar} {en_indicator}")

            print("=" * 130)

            # Display warnings for stalled feeds
            if stalled_feeds:
                print(f"\n⚠️  STALLED FEEDS ({len(stalled_feeds)}): No progress for {STALL_THRESHOLD * refresh_interval}s")
                for stalled in stalled_feeds[:3]:  # Show first 3
                    print(f"   - {stalled}")
                if len(stalled_feeds) > 3:
                    print(f"   ... and {len(stalled_feeds) - 3} more")
                print("\n💡 Run validation to check for incomplete downloads: python3 scripts/validate_feeds_with_rss.py")

            print(f"\nRefreshing every {refresh_interval}s... Auto-launching workers as needed. Ctrl+C to exit. BK=Book Score (1-10), REM=Episodes Remaining")

            time.sleep(refresh_interval)

    except KeyboardInterrupt:
        print("\n\nMonitor stopped.")
        sys.exit(0)

if __name__ == "__main__":
    main()
