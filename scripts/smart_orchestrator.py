#!/usr/bin/env python3
"""
Smart Orchestrator
Continuously monitors progress and dynamically reallocates workers to priority feeds
"""

import os
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime
import xml.etree.ElementTree as ET
import feedparser

# Book recommendation likelihood scores
BOOK_SCORES = {
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
    'Chapo Trap House': 8,
    'TrueAnon': 9,
    'TRUE ANON TRUTH FEED': 9,
    'The Adam Friedland Show Podcast': 2,
    'Monday Morning Podcast': 3,
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

TARGET_DOWNLOADERS = 30
TARGET_TRANSCRIBERS = 15

def get_feed_data():
    """Get current progress and priorities for all feeds"""
    opml_path = Path('podocasts.opml')
    tree = ET.parse(opml_path)
    root = tree.getroot()

    feeds = []
    for outline in root.findall('.//outline[@type="rss"]'):
        title = outline.get('text', '')
        url = outline.get('xmlUrl', '')
        if title and url:
            feeds.append({'name': title, 'url': url})

    episodes_dir = Path('episodes')
    transcripts_dir = Path('transcripts')

    results = []

    for feed in feeds:
        name = feed['name']

        # Get total from RSS (cached from initial fetch)
        try:
            rss_feed = feedparser.parse(feed['url'])
            total = len(rss_feed.entries)
        except:
            total = 0

        # Count downloaded
        downloaded = 0
        podcast_dirs = list(episodes_dir.glob(f'*{name}*'))
        if not podcast_dirs:
            podcast_dir = episodes_dir / name
            if podcast_dir.exists():
                podcast_dirs = [podcast_dir]

        podcast_dir = None
        if podcast_dirs:
            podcast_dir = podcast_dirs[0]
            audio_files = list(podcast_dir.glob('*.mp3')) + list(podcast_dir.glob('*.m4a'))
            valid_files = [f for f in audio_files if f.stat().st_size > 1024 * 1024]
            downloaded = len(valid_files)

        # Count transcripts
        transcribed = 0
        if transcripts_dir.exists():
            trans_dirs = list(transcripts_dir.glob(f'*{name}*'))
            if not trans_dirs:
                trans_dir = transcripts_dir / name
                if trans_dir.exists():
                    trans_dirs = [trans_dir]

            if trans_dirs:
                txt_files = list(trans_dirs[0].glob('*.txt'))
                transcribed = len(txt_files)

        if total > 0:
            remaining = total - downloaded
            book_score = BOOK_SCORES.get(name, 3)

            results.append({
                'name': name,
                'url': feed['url'],
                'total': total,
                'downloaded': downloaded,
                'transcribed': transcribed,
                'remaining': remaining,
                'trans_remaining': downloaded - transcribed,
                'book_score': book_score,
                'podcast_dir': podcast_dir,
                'is_dl_complete': downloaded == total,
                'is_tr_complete': transcribed == downloaded and downloaded > 0
            })

    return results

def get_active_workers():
    """Get PIDs of currently running workers"""
    result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)

    downloaders = {}
    transcribers = {}

    for line in result.stdout.split('\n'):
        if 'podcast_downloader.py' in line and 'grep' not in line:
            parts = line.split()
            if len(parts) > 1:
                pid = parts[1]
                # Extract feed name from command line
                if len(parts) > 11:
                    feed_name = ' '.join(parts[12:])  # Approximate
                    downloaders[pid] = feed_name

        elif 'podcast_transcriber.py' in line and 'grep' not in line:
            parts = line.split()
            if len(parts) > 1:
                pid = parts[1]
                transcribers[pid] = True

    return downloaders, transcribers

def prioritize_downloads(feeds):
    """Get priority list for downloads"""
    incomplete = [f for f in feeds if f['remaining'] > 0]
    incomplete.sort(key=lambda x: (x['remaining'], -x['book_score']))
    return incomplete

def prioritize_transcriptions(feeds):
    """Get priority list for transcriptions"""
    needs_transcription = [f for f in feeds
                          if f['downloaded'] > 0 and f['transcribed'] < f['downloaded']]

    for f in needs_transcription:
        f['trans_remaining'] = f['downloaded'] - f['transcribed']

    needs_transcription.sort(key=lambda x: (
        not x['is_dl_complete'],
        x['trans_remaining'],
        -x['book_score']
    ))

    return needs_transcription

def launch_downloader(feed):
    """Launch a download worker for a feed"""
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)

    name = feed['name']

    log_file = log_dir / f'download_{name.replace("/", "_")}.log'
    cmd = ['python3', 'podcast_downloader.py', name]

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
        print(f'✗ Failed to launch downloader for {name}: {e}')
        return None

def launch_transcriber(feed):
    """Launch a transcription worker for a feed"""
    if not feed['podcast_dir']:
        return None

    log_dir = Path('logs')
    name = feed['name']
    podcast_dir = feed['podcast_dir']

    log_file = log_dir / f'transcribe_{name.replace("/", "_")}.log'
    cmd = ['python3', 'podcast_transcriber.py', str(podcast_dir), 'base']

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
        print(f'✗ Failed to launch transcriber for {name}: {e}')
        return None

def clear_screen():
    os.system('clear' if os.name != 'nt' else 'cls')

def main():
    print("=" * 100)
    print("SMART ORCHESTRATOR - Dynamic Worker Allocation")
    print("=" * 100)
    print()
    print("Initializing...")

    # Track which feeds have active workers
    active_dl_feeds = set()
    active_tr_feeds = set()

    check_interval = 10  # Check every 10 seconds

    try:
        while True:
            clear_screen()

            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print("=" * 100)
            print(f"SMART ORCHESTRATOR - {now}")
            print("=" * 100)
            print()

            # Get current state
            feeds = get_feed_data()
            dl_workers, tr_workers = get_active_workers()

            dl_priority = prioritize_downloads(feeds)
            tr_priority = prioritize_transcriptions(feeds)

            # Show status
            print(f"Active Workers: {len(dl_workers)} downloaders (target: {TARGET_DOWNLOADERS}), "
                  f"{len(tr_workers)} transcribers (target: {TARGET_TRANSCRIBERS})")
            print()

            # Manage downloaders
            if len(dl_workers) < TARGET_DOWNLOADERS:
                needed = TARGET_DOWNLOADERS - len(dl_workers)
                print(f"📥 Need {needed} more downloaders")

                for feed in dl_priority[:needed]:
                    if feed['name'] not in active_dl_feeds and not feed['is_dl_complete']:
                        pid = launch_downloader(feed)
                        if pid:
                            active_dl_feeds.add(feed['name'])
                            print(f"  ✓ Launched DL: {feed['name'][:50]} ({feed['remaining']} left, book={feed['book_score']})")

            # Manage transcribers
            if len(tr_workers) < TARGET_TRANSCRIBERS:
                needed = TARGET_TRANSCRIBERS - len(tr_workers)
                print(f"📝 Need {needed} more transcribers")

                for feed in tr_priority[:needed]:
                    if feed['name'] not in active_tr_feeds and not feed['is_tr_complete']:
                        pid = launch_transcriber(feed)
                        if pid:
                            active_tr_feeds.add(feed['name'])
                            status = "✓ COMPLETE" if feed['is_dl_complete'] else "  partial"
                            print(f"  ✓ Launched TR: {feed['name'][:50]} ({feed['trans_remaining']} left, book={feed['book_score']}) {status}")

            # Remove completed feeds from active tracking
            for feed in feeds:
                if feed['is_dl_complete'] and feed['name'] in active_dl_feeds:
                    active_dl_feeds.remove(feed['name'])
                if feed['is_tr_complete'] and feed['name'] in active_tr_feeds:
                    active_tr_feeds.remove(feed['name'])

            # Show top priorities
            print()
            print("=" * 100)
            print("TOP DOWNLOAD PRIORITIES")
            print("-" * 100)
            for i, feed in enumerate(dl_priority[:10], 1):
                status = "🔄" if feed['name'] in active_dl_feeds else "  "
                print(f"{i:>2}. {status} {feed['name'][:50]:<50} {feed['remaining']:>4} left, book={feed['book_score']}")

            print()
            print("TOP TRANSCRIPTION PRIORITIES")
            print("-" * 100)
            for i, feed in enumerate(tr_priority[:10], 1):
                status = "🔄" if feed['name'] in active_tr_feeds else "  "
                complete = "✓" if feed['is_dl_complete'] else " "
                print(f"{i:>2}. {status} {feed['name'][:50]:<50} {feed['trans_remaining']:>4} left, book={feed['book_score']} {complete}")

            print()
            print("=" * 100)
            print(f"Next check in {check_interval}s... Ctrl+C to stop")

            time.sleep(check_interval)

    except KeyboardInterrupt:
        print("\n\nOrchestrator stopped.")
        sys.exit(0)

if __name__ == "__main__":
    main()
