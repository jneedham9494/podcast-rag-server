#!/usr/bin/env python3
"""
Main entry point for the refactored monitor.

Usage:
    python3 scripts/monitor/main.py

This is a modular version of monitor_progress.py.
The original file is preserved for comparison.
"""

import os
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime

# Import from our modules
from .config import (
    TARGET_DOWNLOADERS,
    TARGET_TRANSCRIBERS,
    TARGET_ENRICHERS,
    REFRESH_INTERVAL,
    STALL_THRESHOLD,
    MIN_EPISODES_FOR_MULTIPLE_WORKERS,
    MANUAL_FAILOVER_THRESHOLD,
    PATREON_BASE_DELAY,
    PATREON_MAX_DELAY,
)
from .display import (
    clear_screen,
    make_progress_bar,
    print_header,
    print_worker_status,
)
from .workers import (
    get_worker_counts,
    launch_worker,
)
from .feed_analyzer import (
    get_book_scores,
    fetch_rss_totals,
    get_feed_progress,
    check_feed_failure,
)


def main():
    """Main orchestration loop."""

    # Track which feeds have active workers
    active_dl_feeds = set()
    active_tr_feeds_count = {}  # {feed_name: worker_count}
    active_en_feeds = set()

    # Track progress history to detect stalled feeds
    progress_history = {}

    # Exponential backoff tracking for Patreon feeds
    backoff_state = {
        'TRUE ANON TRUTH FEED': {
            'failure_count': 0,
            'last_attempt': None,
            'base_delay': PATREON_BASE_DELAY,
            'max_delay': PATREON_MAX_DELAY,
            'manual_mode': False,
            'manual_pid': None,
        }
    }

    print("Starting live progress monitor with auto-worker management...")
    print(f"Refresh interval: {REFRESH_INTERVAL} seconds")
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
            print_header()

            # Worker counts
            dl_workers, tr_workers, en_workers, dl_feeds, tr_feeds, en_feeds = get_worker_counts()
            print_worker_status(
                dl_workers, tr_workers, en_workers,
                TARGET_DOWNLOADERS, TARGET_TRANSCRIBERS, TARGET_ENRICHERS
            )

            # Get feed progress
            feeds = get_feed_progress(rss_totals, book_scores)

            # Update progress history to detect stalled feeds
            stalled_feeds = []
            for feed in feeds:
                name = feed['name']
                downloaded = feed['downloaded']
                total = feed.get('total', downloaded)

                if name not in progress_history:
                    progress_history[name] = []

                progress_history[name].append(downloaded)

                if len(progress_history[name]) > STALL_THRESHOLD:
                    progress_history[name].pop(0)

                completion_pct = (downloaded / total * 100) if total > 0 else 100
                if (len(progress_history[name]) >= STALL_THRESHOLD and
                    len(set(progress_history[name])) == 1 and
                    not feed['is_dl_complete'] and
                    feed['remaining'] > 0 and
                    feed['remaining'] > 5 and
                    completion_pct < 99.0 and
                    downloaded < total):
                    stalled_feeds.append(name)

            # Update backoff state for TRUE ANON TRUTH FEED
            if 'TRUE ANON TRUTH FEED' in backoff_state:
                feed_name = 'TRUE ANON TRUTH FEED'
                state = backoff_state[feed_name]

                if state['last_attempt'] and feed_name in active_dl_feeds and feed_name not in dl_feeds:
                    if check_feed_failure(feed_name):
                        state['failure_count'] += 1
                        print(f"  ⚠️  {feed_name}: Download failed (failure #{state['failure_count']})")

                        if state['failure_count'] >= MANUAL_FAILOVER_THRESHOLD and not state['manual_mode']:
                            print(f"  🔄 {feed_name}: Switching to manual download assistant")
                            state['manual_mode'] = True

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
                            except Exception as e:
                                print(f"  ✗ Failed to launch manual download assistant: {e}")
                    else:
                        if state['failure_count'] > 0:
                            print(f"  ✓ {feed_name}: Download succeeded, resetting backoff")
                        state['failure_count'] = 0
                        state['manual_mode'] = False

                    active_dl_feeds.discard(feed_name)

            # Launch download workers if needed
            if dl_workers < TARGET_DOWNLOADERS:
                needed = TARGET_DOWNLOADERS - dl_workers
                incomplete_feeds = [f for f in feeds if not f['is_dl_complete']]
                for feed in incomplete_feeds[:needed]:
                    if feed['name'] == 'TRUE ANON TRUTH FEED':
                        if feed['name'] in active_dl_feeds or feed['name'] in dl_feeds:
                            continue

                        state = backoff_state[feed['name']]
                        if state['manual_mode']:
                            if state['manual_pid']:
                                try:
                                    os.kill(state['manual_pid'], 0)
                                    continue
                                except OSError:
                                    state['manual_mode'] = False
                                    state['manual_pid'] = None
                                    state['failure_count'] = 0

                        if state['last_attempt'] and state['failure_count'] > 0:
                            delay = min(
                                state['base_delay'] * (2 ** (state['failure_count'] - 1)),
                                state['max_delay']
                            )
                            time_since_attempt = time.time() - state['last_attempt']
                            if time_since_attempt < delay:
                                continue

                    if feed['name'] not in active_dl_feeds and feed['name'] not in dl_feeds:
                        episodes_dir = Path('../episodes')
                        podcast_dir = episodes_dir / feed['name']
                        if (Path('episodes') / feed['name']).exists():
                            feed['podcast_dir'] = podcast_dir

                        pid = launch_worker(feed, 'download')
                        if pid:
                            active_dl_feeds.add(feed['name'])
                            if feed['name'] == 'TRUE ANON TRUTH FEED':
                                backoff_state[feed['name']]['last_attempt'] = time.time()
                            print(f"  📥 Launched downloader: {feed['name']} (PID {pid})")

            # Launch transcription workers if needed
            if tr_workers < TARGET_TRANSCRIBERS:
                slots_available = TARGET_TRANSCRIBERS - tr_workers
                transcribe_feeds = [f for f in feeds if f['trans_remaining'] > 0]
                transcribe_feeds.sort(key=lambda x: (-x['trans_remaining'], not x['is_dl_complete'], -x['book_score']))

                for feed in transcribe_feeds:
                    if slots_available <= 0:
                        break

                    feed_name = feed['name']
                    current_workers = active_tr_feeds_count.get(feed_name, 0)
                    trans_remaining = feed['trans_remaining']

                    if trans_remaining >= MIN_EPISODES_FOR_MULTIPLE_WORKERS:
                        max_workers_for_feed = min(slots_available, max(1, trans_remaining // 50))
                    else:
                        max_workers_for_feed = 1

                    workers_to_launch = max_workers_for_feed - current_workers

                    if workers_to_launch > 0:
                        episodes_dir = Path('../episodes')
                        podcast_dir = episodes_dir / feed_name
                        if (Path('episodes') / feed_name).exists():
                            feed['podcast_dir'] = podcast_dir

                        for _ in range(workers_to_launch):
                            if slots_available <= 0:
                                break

                            pid = launch_worker(feed, 'transcribe')
                            if pid:
                                active_tr_feeds_count[feed_name] = active_tr_feeds_count.get(feed_name, 0) + 1
                                slots_available -= 1
                                print(f"  📝 Launched transcriber: {feed_name} (PID {pid})")

            # Launch enrichment workers if needed
            if en_workers < TARGET_ENRICHERS:
                slots_available = TARGET_ENRICHERS - en_workers
                enrich_feeds = [f for f in feeds if f['enrich_remaining'] > 0]
                enrich_feeds.sort(key=lambda x: (-x['enrich_remaining'], -x['book_score']))

                for feed in enrich_feeds:
                    if slots_available <= 0:
                        break

                    feed_name = feed['name']
                    if feed_name in active_en_feeds or feed_name in en_feeds:
                        continue

                    project_root = Path(__file__).parent.parent.parent
                    trans_dir = project_root / 'transcripts' / feed_name
                    if trans_dir.exists():
                        txt_files = list(trans_dir.glob('*.txt'))
                        for txt_file in txt_files:
                            enriched_file = txt_file.with_name(txt_file.stem + '_enriched.json')
                            if not enriched_file.exists():
                                log_dir = project_root / 'logs'
                                log_dir.mkdir(exist_ok=True)
                                log_file = log_dir / f'enrich_{feed_name.replace("/", "_")}.log'

                                try:
                                    with open(log_file, 'w') as f:
                                        process = subprocess.Popen(
                                            ['python3', '-m', 'scripts.enrichment.main', str(txt_file.absolute())],
                                            cwd=project_root,
                                            stdout=f,
                                            stderr=subprocess.STDOUT,
                                            stdin=subprocess.DEVNULL
                                        )
                                    active_en_feeds.add(feed_name)
                                    slots_available -= 1
                                    print(f"  🔍 Launched enricher: {feed_name} (PID {process.pid})")
                                except Exception as e:
                                    print(f"  ✗ Failed to launch enricher: {e}")
                                break

            # Remove completed feeds from active tracking
            for feed in feeds:
                if feed['is_dl_complete'] and feed['name'] in active_dl_feeds:
                    active_dl_feeds.discard(feed['name'])
                if feed['is_tr_complete'] and feed['name'] in active_tr_feeds_count:
                    del active_tr_feeds_count[feed['name']]
                if feed['is_en_complete'] and feed['name'] in active_en_feeds:
                    active_en_feeds.discard(feed['name'])
                if feed['name'] in active_en_feeds and feed['name'] not in en_feeds:
                    active_en_feeds.discard(feed['name'])

            print()

            # Calculate and display totals
            total_available = sum(f['total'] for f in feeds)
            total_downloaded = sum(f['downloaded'] for f in feeds)
            total_transcribed = sum(f['transcribed'] for f in feeds)
            total_enriched = sum(f['enriched'] for f in feeds)

            dl_pct = total_downloaded / total_available * 100 if total_available > 0 else 0
            tr_pct = total_transcribed / total_downloaded * 100 if total_downloaded > 0 else 0
            en_pct = total_enriched / total_transcribed * 100 if total_transcribed > 0 else 0

            print(f"📊 Overall: ⬇ {total_downloaded}/{total_available} ({dl_pct:.1f}%), "
                  f"📝 {total_transcribed} ({tr_pct:.1f}%), "
                  f"🔍 {total_enriched} ({en_pct:.1f}%)")
            print()
            print("=" * 130)

            # Display feed table
            print(f"{'PODCAST FEED':<28} {'BK':<3} {'REM':>4}  {'DOWNLOAD':<28} {'TRANSCRIBE':<28} {'ENRICH':<20}")
            print("-" * 130)

            for feed in feeds:
                name = feed['name'][:27]
                book_score = feed['book_score']
                remaining = feed['remaining']

                dl_bar = make_progress_bar(feed['downloaded'], feed['total'], 10)
                tr_bar = make_progress_bar(feed['transcribed'], feed['downloaded'], 10)
                en_bar = make_progress_bar(feed['enriched'], feed['transcribed'], 8)

                # Status indicators
                if feed['is_dl_complete']:
                    dl_indicator = "✓ "
                elif feed['name'] in dl_feeds:
                    dl_indicator = "⬇ "
                elif feed['name'] in stalled_feeds:
                    dl_indicator = "⚠️"
                else:
                    dl_indicator = "  "

                if feed['is_tr_complete']:
                    tr_indicator = "✓ "
                elif feed['name'] in tr_feeds:
                    tr_indicator = "📝 "
                else:
                    tr_indicator = "  "

                if feed['is_en_complete']:
                    en_indicator = "✓ "
                elif feed['name'] in en_feeds:
                    en_indicator = "🔍 "
                else:
                    en_indicator = "  "

                print(f"{name:<28} {book_score:>2} {remaining:>4}  {dl_bar} {dl_indicator} {tr_bar} {tr_indicator} {en_bar} {en_indicator}")

            print("=" * 130)

            if stalled_feeds:
                print(f"\n⚠️  STALLED FEEDS ({len(stalled_feeds)}): No progress for {STALL_THRESHOLD * REFRESH_INTERVAL}s")
                for stalled in stalled_feeds[:3]:
                    print(f"   - {stalled}")

            print(f"\nRefreshing every {REFRESH_INTERVAL}s... Ctrl+C to exit.")

            time.sleep(REFRESH_INTERVAL)

    except KeyboardInterrupt:
        print("\n\nMonitor stopped.")
        sys.exit(0)


if __name__ == "__main__":
    main()
