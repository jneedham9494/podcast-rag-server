"""
SQLite-based progress tracking for podcast episodes.

Tracks episode status through the pipeline:
pending → downloading → downloaded → transcribing → transcribed → enriching → enriched

Supports crash recovery by persisting state to disk.
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple
from loguru import logger


class EpisodeStatus(str, Enum):
    """Status of an episode in the processing pipeline."""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    DOWNLOADED = "downloaded"
    TRANSCRIBING = "transcribing"
    TRANSCRIBED = "transcribed"
    ENRICHING = "enriching"
    ENRICHED = "enriched"
    FAILED = "failed"
    SKIPPED = "skipped"


# Default database path
DEFAULT_DB_PATH = Path("data/progress.db")


class ProgressDB:
    """
    SQLite database for tracking episode progress.

    Thread-safe with connection pooling for concurrent workers.
    """

    def __init__(self, db_path: Path = DEFAULT_DB_PATH):
        """
        Initialize progress database.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Get a database connection with row factory."""
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")  # Better concurrent access
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_schema(self) -> None:
        """Initialize database schema."""
        with self._get_connection() as conn:
            conn.executescript("""
                -- Episodes table
                CREATE TABLE IF NOT EXISTS episodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    podcast_name TEXT NOT NULL,
                    episode_title TEXT NOT NULL,
                    episode_url TEXT,
                    guid TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    error_message TEXT,
                    audio_path TEXT,
                    transcript_path TEXT,
                    enrichment_path TEXT,
                    download_started_at TEXT,
                    download_completed_at TEXT,
                    transcribe_started_at TEXT,
                    transcribe_completed_at TEXT,
                    enrich_started_at TEXT,
                    enrich_completed_at TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(podcast_name, episode_title)
                );

                -- Indexes for common queries
                CREATE INDEX IF NOT EXISTS idx_episodes_status
                    ON episodes(status);
                CREATE INDEX IF NOT EXISTS idx_episodes_podcast
                    ON episodes(podcast_name);
                CREATE INDEX IF NOT EXISTS idx_episodes_podcast_status
                    ON episodes(podcast_name, status);

                -- Processing locks table (for distributed workers)
                CREATE TABLE IF NOT EXISTS processing_locks (
                    episode_id INTEGER PRIMARY KEY,
                    worker_id TEXT NOT NULL,
                    locked_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (episode_id) REFERENCES episodes(id)
                );

                -- Migration tracking
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                -- Insert initial version if not exists
                INSERT OR IGNORE INTO schema_version (version) VALUES (1);
            """)

    # === Episode CRUD Operations ===

    def add_episode(
        self,
        podcast_name: str,
        episode_title: str,
        episode_url: Optional[str] = None,
        guid: Optional[str] = None,
    ) -> int:
        """
        Add a new episode to track.

        Args:
            podcast_name: Name of the podcast
            episode_title: Title of the episode
            episode_url: URL to download from
            guid: RSS feed GUID

        Returns:
            Episode ID
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO episodes (podcast_name, episode_title, episode_url, guid)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(podcast_name, episode_title) DO UPDATE SET
                    episode_url = COALESCE(excluded.episode_url, episode_url),
                    guid = COALESCE(excluded.guid, guid),
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
                """,
                (podcast_name, episode_title, episode_url, guid)
            )
            result = cursor.fetchone()
            return result[0] if result else 0

    def get_episode(
        self,
        podcast_name: str,
        episode_title: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get episode by podcast and title.

        Returns:
            Episode data as dict, or None if not found
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM episodes
                WHERE podcast_name = ? AND episode_title = ?
                """,
                (podcast_name, episode_title)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_episode_by_id(self, episode_id: int) -> Optional[Dict[str, Any]]:
        """Get episode by ID."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM episodes WHERE id = ?",
                (episode_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    # === Status Updates ===

    def update_status(
        self,
        episode_id: int,
        status: EpisodeStatus,
        error_message: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        """
        Update episode status with optional additional fields.

        Args:
            episode_id: Episode ID
            status: New status
            error_message: Error message if failed
            **kwargs: Additional fields to update (audio_path, transcript_path, etc.)
        """
        # Build dynamic update query
        updates = ["status = ?", "updated_at = CURRENT_TIMESTAMP"]
        params: List[Any] = [status.value]

        if error_message:
            updates.append("error_message = ?")
            params.append(error_message)

        # Handle timestamp fields based on status
        timestamp_map = {
            EpisodeStatus.DOWNLOADING: ("download_started_at", datetime.now().isoformat()),
            EpisodeStatus.DOWNLOADED: ("download_completed_at", datetime.now().isoformat()),
            EpisodeStatus.TRANSCRIBING: ("transcribe_started_at", datetime.now().isoformat()),
            EpisodeStatus.TRANSCRIBED: ("transcribe_completed_at", datetime.now().isoformat()),
            EpisodeStatus.ENRICHING: ("enrich_started_at", datetime.now().isoformat()),
            EpisodeStatus.ENRICHED: ("enrich_completed_at", datetime.now().isoformat()),
        }

        if status in timestamp_map:
            field, value = timestamp_map[status]
            updates.append(f"{field} = ?")
            params.append(value)

        # Handle additional kwargs
        for key, value in kwargs.items():
            if key in ('audio_path', 'transcript_path', 'enrichment_path'):
                updates.append(f"{key} = ?")
                params.append(value)

        params.append(episode_id)

        with self._get_connection() as conn:
            conn.execute(
                f"UPDATE episodes SET {', '.join(updates)} WHERE id = ?",
                params
            )

        logger.debug(f"Episode {episode_id} status updated to {status.value}")

    def mark_downloading(self, episode_id: int) -> None:
        """Mark episode as downloading."""
        self.update_status(episode_id, EpisodeStatus.DOWNLOADING)

    def mark_downloaded(self, episode_id: int, audio_path: str) -> None:
        """Mark episode as downloaded with audio path."""
        self.update_status(
            episode_id,
            EpisodeStatus.DOWNLOADED,
            audio_path=audio_path
        )

    def mark_transcribing(self, episode_id: int) -> None:
        """Mark episode as transcribing."""
        self.update_status(episode_id, EpisodeStatus.TRANSCRIBING)

    def mark_transcribed(self, episode_id: int, transcript_path: str) -> None:
        """Mark episode as transcribed with transcript path."""
        self.update_status(
            episode_id,
            EpisodeStatus.TRANSCRIBED,
            transcript_path=transcript_path
        )

    def mark_enriching(self, episode_id: int) -> None:
        """Mark episode as enriching."""
        self.update_status(episode_id, EpisodeStatus.ENRICHING)

    def mark_enriched(self, episode_id: int, enrichment_path: str) -> None:
        """Mark episode as enriched with enrichment path."""
        self.update_status(
            episode_id,
            EpisodeStatus.ENRICHED,
            enrichment_path=enrichment_path
        )

    def mark_failed(self, episode_id: int, error_message: str) -> None:
        """Mark episode as failed with error message."""
        self.update_status(
            episode_id,
            EpisodeStatus.FAILED,
            error_message=error_message
        )

    def mark_skipped(self, episode_id: int, reason: str) -> None:
        """Mark episode as skipped with reason."""
        self.update_status(
            episode_id,
            EpisodeStatus.SKIPPED,
            error_message=reason
        )

    # === Queries ===

    def get_episodes_by_status(
        self,
        status: EpisodeStatus,
        podcast_name: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get episodes with a specific status.

        Args:
            status: Status to filter by
            podcast_name: Optional podcast name filter
            limit: Maximum results to return

        Returns:
            List of episode dicts
        """
        with self._get_connection() as conn:
            if podcast_name:
                cursor = conn.execute(
                    """
                    SELECT * FROM episodes
                    WHERE status = ? AND podcast_name = ?
                    ORDER BY created_at ASC
                    LIMIT ?
                    """,
                    (status.value, podcast_name, limit)
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT * FROM episodes
                    WHERE status = ?
                    ORDER BY created_at ASC
                    LIMIT ?
                    """,
                    (status.value, limit)
                )
            return [dict(row) for row in cursor.fetchall()]

    def get_pending_downloads(
        self,
        podcast_name: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get episodes pending download."""
        return self.get_episodes_by_status(
            EpisodeStatus.PENDING, podcast_name, limit
        )

    def get_pending_transcriptions(
        self,
        podcast_name: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get episodes pending transcription (downloaded but not transcribed)."""
        return self.get_episodes_by_status(
            EpisodeStatus.DOWNLOADED, podcast_name, limit
        )

    def get_pending_enrichments(
        self,
        podcast_name: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get episodes pending enrichment (transcribed but not enriched)."""
        return self.get_episodes_by_status(
            EpisodeStatus.TRANSCRIBED, podcast_name, limit
        )

    def get_failed_episodes(
        self,
        podcast_name: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get failed episodes."""
        return self.get_episodes_by_status(
            EpisodeStatus.FAILED, podcast_name, limit
        )

    def get_stats(self, podcast_name: Optional[str] = None) -> Dict[str, int]:
        """
        Get statistics about episode processing.

        Returns:
            Dict with counts per status
        """
        with self._get_connection() as conn:
            if podcast_name:
                cursor = conn.execute(
                    """
                    SELECT status, COUNT(*) as count
                    FROM episodes
                    WHERE podcast_name = ?
                    GROUP BY status
                    """,
                    (podcast_name,)
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT status, COUNT(*) as count
                    FROM episodes
                    GROUP BY status
                    """
                )

            stats = {status.value: 0 for status in EpisodeStatus}
            for row in cursor.fetchall():
                stats[row['status']] = row['count']

            stats['total'] = sum(stats.values())
            return stats

    def get_podcast_stats(self) -> List[Dict[str, Any]]:
        """Get stats broken down by podcast."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT
                    podcast_name,
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'enriched' THEN 1 ELSE 0 END) as enriched,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending
                FROM episodes
                GROUP BY podcast_name
                ORDER BY podcast_name
                """
            )
            return [dict(row) for row in cursor.fetchall()]

    # === Locking for Concurrent Workers ===

    def acquire_lock(self, episode_id: int, worker_id: str) -> bool:
        """
        Acquire a processing lock for an episode.

        Args:
            episode_id: Episode to lock
            worker_id: Identifier for the worker

        Returns:
            True if lock acquired, False if already locked
        """
        try:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO processing_locks (episode_id, worker_id)
                    VALUES (?, ?)
                    """,
                    (episode_id, worker_id)
                )
                return True
        except sqlite3.IntegrityError:
            return False

    def release_lock(self, episode_id: int, worker_id: str) -> bool:
        """
        Release a processing lock.

        Args:
            episode_id: Episode to unlock
            worker_id: Worker that holds the lock

        Returns:
            True if lock released, False if not held
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                DELETE FROM processing_locks
                WHERE episode_id = ? AND worker_id = ?
                """,
                (episode_id, worker_id)
            )
            return cursor.rowcount > 0

    def cleanup_stale_locks(self, max_age_minutes: int = 60) -> int:
        """
        Remove locks older than max_age_minutes.

        Returns:
            Number of locks cleaned up
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                DELETE FROM processing_locks
                WHERE datetime(locked_at) < datetime('now', ?)
                """,
                (f'-{max_age_minutes} minutes',)
            )
            count = cursor.rowcount
            if count > 0:
                logger.info(f"Cleaned up {count} stale locks")
            return count

    # === Recovery ===

    def reset_stuck_episodes(self) -> int:
        """
        Reset episodes stuck in processing states after crash.

        Returns:
            Number of episodes reset
        """
        with self._get_connection() as conn:
            # Reset downloading → pending
            cursor = conn.execute(
                """
                UPDATE episodes
                SET status = 'pending', updated_at = CURRENT_TIMESTAMP
                WHERE status = 'downloading'
                """
            )
            downloading = cursor.rowcount

            # Reset transcribing → downloaded
            cursor = conn.execute(
                """
                UPDATE episodes
                SET status = 'downloaded', updated_at = CURRENT_TIMESTAMP
                WHERE status = 'transcribing'
                """
            )
            transcribing = cursor.rowcount

            # Reset enriching → transcribed
            cursor = conn.execute(
                """
                UPDATE episodes
                SET status = 'transcribed', updated_at = CURRENT_TIMESTAMP
                WHERE status = 'enriching'
                """
            )
            enriching = cursor.rowcount

            total = downloading + transcribing + enriching
            if total > 0:
                logger.info(
                    f"Reset {total} stuck episodes: "
                    f"{downloading} downloading, "
                    f"{transcribing} transcribing, "
                    f"{enriching} enriching"
                )

        # Cleanup stale locks after connection is closed
        self.cleanup_stale_locks()

        return total


# Global database instance
_db_instance: Optional[ProgressDB] = None


def get_db(db_path: Optional[Path] = None) -> ProgressDB:
    """
    Get or create the global database instance.

    Args:
        db_path: Optional path to database file

    Returns:
        ProgressDB instance
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = ProgressDB(db_path or DEFAULT_DB_PATH)
    return _db_instance


def init_db(db_path: Optional[Path] = None) -> ProgressDB:
    """
    Initialize database and return instance.

    Alias for get_db() for clarity at startup.
    """
    return get_db(db_path)
