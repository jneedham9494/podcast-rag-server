"""
Display utilities for the monitor dashboard.
"""

import os
from datetime import datetime
from typing import Tuple


def clear_screen():
    """Clear the terminal screen."""
    os.system('clear' if os.name != 'nt' else 'cls')


def make_progress_bar(numerator: int, denominator: int, width: int = 20) -> str:
    """
    Create a progress bar string.

    Args:
        numerator: Current progress value
        denominator: Total value
        width: Width of the bar in characters

    Returns:
        Formatted progress bar string like "[████░░░░] 10/20 50.0%"
    """
    if denominator == 0:
        progress = 0
    else:
        progress = numerator / denominator

    filled = int(width * progress)
    bar = '█' * filled + '░' * (width - filled)
    pct = (progress * 100) if denominator > 0 else 0

    return f"[{bar}] {numerator:>4}/{denominator:<4} {pct:>5.1f}%"


def print_header():
    """Print the monitor dashboard header."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("=" * 130)
    print("PODCAST DOWNLOAD & TRANSCRIPTION MONITOR (Auto-Orchestrator Mode)".center(130))
    print(f"{now}".center(130))
    print("=" * 130)
    print()


def print_worker_status(
    dl_workers: int,
    tr_workers: int,
    en_workers: int,
    target_dl: int,
    target_tr: int,
    target_en: int
):
    """
    Print the current worker status line.

    Args:
        dl_workers: Number of active download workers
        tr_workers: Number of active transcription workers
        en_workers: Number of active enrichment workers
        target_dl: Target number of download workers
        target_tr: Target number of transcription workers
        target_en: Target number of enrichment workers
    """
    print(
        f"⚙️  Active Workers: "
        f"{dl_workers} downloaders (target: {target_dl}), "
        f"{tr_workers} transcribers (target: {target_tr}), "
        f"{en_workers} enrichers (target: {target_en})"
    )
    print()


def format_feed_row(
    name: str,
    book_score: int,
    dl_bar: str,
    tr_bar: str,
    en_bar: str,
    has_dl_worker: bool = False,
    has_tr_worker: bool = False,
    has_en_worker: bool = False,
    is_stalled: bool = False
) -> str:
    """
    Format a single feed row for display.

    Args:
        name: Feed name
        book_score: Book recommendation score
        dl_bar: Download progress bar
        tr_bar: Transcription progress bar
        en_bar: Enrichment progress bar
        has_dl_worker: Whether feed has active download worker
        has_tr_worker: Whether feed has active transcription worker
        has_en_worker: Whether feed has active enrichment worker
        is_stalled: Whether feed is stalled

    Returns:
        Formatted row string
    """
    # Worker indicators
    dl_indicator = "📥" if has_dl_worker else "  "
    tr_indicator = "📝" if has_tr_worker else "  "
    en_indicator = "✨" if has_en_worker else "  "

    # Stall indicator
    stall_indicator = " ⚠️" if is_stalled else ""

    # Truncate name if too long
    display_name = name[:30] if len(name) > 30 else name

    return (
        f"{display_name:<30} "
        f"[{book_score}] "
        f"{dl_indicator} {dl_bar} "
        f"{tr_indicator} {tr_bar} "
        f"{en_indicator} {en_bar}"
        f"{stall_indicator}"
    )
