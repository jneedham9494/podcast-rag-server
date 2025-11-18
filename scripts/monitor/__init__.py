"""
Monitor package for podcast download and transcription orchestration.

This is a refactored modular version of monitor_progress.py.
The original file is preserved for comparison and backup.
"""

from .config import (
    TARGET_DOWNLOADERS,
    TARGET_TRANSCRIBERS,
    TARGET_ENRICHERS,
    REFRESH_INTERVAL,
    STALL_THRESHOLD,
    MIN_EPISODES_FOR_MULTIPLE_WORKERS,
    MANUAL_FAILOVER_THRESHOLD,
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
    normalize_title,
    count_rss_duplicates,
    fetch_rss_totals,
    get_feed_progress,
    check_feed_failure,
)

__all__ = [
    # Config
    'TARGET_DOWNLOADERS',
    'TARGET_TRANSCRIBERS',
    'TARGET_ENRICHERS',
    'REFRESH_INTERVAL',
    'STALL_THRESHOLD',
    'MIN_EPISODES_FOR_MULTIPLE_WORKERS',
    'MANUAL_FAILOVER_THRESHOLD',
    # Display
    'clear_screen',
    'make_progress_bar',
    'print_header',
    'print_worker_status',
    # Workers
    'get_worker_counts',
    'launch_worker',
    # Feed analysis
    'get_book_scores',
    'normalize_title',
    'count_rss_duplicates',
    'fetch_rss_totals',
    'get_feed_progress',
    'check_feed_failure',
]
