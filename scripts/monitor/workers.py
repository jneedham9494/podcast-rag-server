"""
Worker management for download and transcription processes.
"""

import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Tuple, Set, Optional, Dict, Any


def get_worker_counts() -> Tuple[int, int, int, Set[str], Set[str], Set[str]]:
    """
    Count active download, transcription, and enrichment workers.

    Returns:
        Tuple of:
        - dl_count: Number of download workers
        - tr_count: Number of transcription workers
        - en_count: Number of enrichment workers
        - dl_feeds: Set of feed names being downloaded
        - tr_feeds: Set of feed names being transcribed
        - en_feeds: Set of feed names being enriched
    """
    result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)

    dl_count = 0
    tr_count = 0
    en_count = 0

    dl_feeds: Set[str] = set()
    tr_feeds: Set[str] = set()
    en_feeds: Set[str] = set()

    for line in result.stdout.split('\n'):
        if 'podcast_downloader.py' in line and 'grep' not in line:
            dl_count += 1
            if 'podcast_downloader.py' in line:
                parts = line.split('podcast_downloader.py')
                if len(parts) > 1:
                    feed_name = parts[1].strip()
                    if feed_name:
                        dl_feeds.add(feed_name)

        elif 'patreon_downloader.py' in line and 'grep' not in line:
            dl_count += 1
            dl_feeds.add('TRUE ANON TRUTH FEED')

        elif 'patreon_browser_downloader.py' in line and 'grep' not in line:
            dl_count += 1
            dl_feeds.add('TRUE ANON TRUTH FEED')

        elif 'podcast_transcriber.py' in line and 'grep' not in line:
            tr_count += 1
            if 'episodes/' in line:
                parts = line.split('episodes/')
                if len(parts) > 1:
                    remaining = parts[1]
                    if ' base' in remaining:
                        feed_name = remaining.split(' base')[0].strip()
                    elif ' large' in remaining:
                        feed_name = remaining.split(' large')[0].strip()
                    else:
                        feed_name = ' '.join(remaining.split()[:-1]).strip()
                    if feed_name:
                        tr_feeds.add(feed_name)

        elif 'enrich_transcript.py' in line and 'grep' not in line:
            en_count += 1
            if 'transcripts/' in line:
                parts = line.split('transcripts/')
                if len(parts) > 1:
                    remaining = parts[1]
                    feed_name = remaining.split('/')[0].strip()
                    if feed_name:
                        en_feeds.add(feed_name)

    return dl_count, tr_count, en_count, dl_feeds, tr_feeds, en_feeds


def launch_worker(
    feed: Dict[str, Any],
    worker_type: str = 'download'
) -> Optional[int]:
    """
    Launch a download or transcription worker for a feed.

    Args:
        feed: Feed dictionary with 'name' and optionally 'podcast_dir'
        worker_type: 'download' or 'transcription'

    Returns:
        Process PID if successful, None otherwise
    """
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)

    name = feed['name']

    if worker_type == 'download':
        log_file = log_dir / f'download_{name.replace("/", "_")}.log'

        # Use patreon_downloader for Patreon feeds
        if name == 'TRUE ANON TRUTH FEED':
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
                cmd = ['python3', 'patreon_downloader.py', rss_url, '--manual-cookies']
            else:
                cmd = ['python3', 'podcast_downloader.py', name]
        else:
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
