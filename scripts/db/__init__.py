"""
Database module for progress persistence.

Provides SQLite-based tracking of episode download, transcription,
and enrichment progress with crash recovery support.
"""

from .progress import (
    EpisodeStatus,
    ProgressDB,
    get_db,
    init_db,
)

__all__ = [
    'EpisodeStatus',
    'ProgressDB',
    'get_db',
    'init_db',
]
