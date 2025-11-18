"""
Unit tests for SQLite progress tracking.

Tests cover:
- Episode CRUD operations
- Status transitions
- Statistics queries
- Locking for concurrent workers
- Crash recovery
"""

import pytest
import sys
import tempfile
from pathlib import Path

# Add scripts to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from db.progress import (
    ProgressDB,
    EpisodeStatus,
    get_db,
    init_db,
)


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_progress.db"
        db = ProgressDB(db_path)
        yield db


class TestProgressDBInit:
    """Tests for database initialization."""

    def test_creates_database_file(self, temp_db):
        """GIVEN new database WHEN initialized THEN creates file."""
        assert temp_db.db_path.exists()

    def test_creates_episodes_table(self, temp_db):
        """GIVEN new database WHEN initialized THEN has episodes table."""
        with temp_db._get_connection() as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='episodes'"
            )
            assert cursor.fetchone() is not None

    def test_creates_locks_table(self, temp_db):
        """GIVEN new database WHEN initialized THEN has locks table."""
        with temp_db._get_connection() as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='processing_locks'"
            )
            assert cursor.fetchone() is not None


class TestEpisodeCRUD:
    """Tests for episode CRUD operations."""

    def test_add_episode_returns_id(self, temp_db):
        """GIVEN episode data WHEN adding THEN returns ID."""
        episode_id = temp_db.add_episode(
            podcast_name="Test Podcast",
            episode_title="Episode 1",
            episode_url="https://example.com/ep1.mp3"
        )
        assert episode_id > 0

    def test_add_episode_sets_pending_status(self, temp_db):
        """GIVEN new episode WHEN added THEN status is pending."""
        episode_id = temp_db.add_episode("Test", "Episode 1")
        episode = temp_db.get_episode_by_id(episode_id)
        assert episode['status'] == 'pending'

    def test_get_episode_returns_data(self, temp_db):
        """GIVEN existing episode WHEN getting THEN returns data."""
        temp_db.add_episode("Test", "Episode 1", "https://example.com/ep1.mp3")
        episode = temp_db.get_episode("Test", "Episode 1")

        assert episode is not None
        assert episode['podcast_name'] == "Test"
        assert episode['episode_title'] == "Episode 1"
        assert episode['episode_url'] == "https://example.com/ep1.mp3"

    def test_get_nonexistent_episode_returns_none(self, temp_db):
        """GIVEN no episode WHEN getting THEN returns None."""
        episode = temp_db.get_episode("Test", "Nonexistent")
        assert episode is None

    def test_add_duplicate_updates_existing(self, temp_db):
        """GIVEN duplicate episode WHEN adding THEN updates existing."""
        id1 = temp_db.add_episode("Test", "Episode 1", "url1")
        id2 = temp_db.add_episode("Test", "Episode 1", "url2")

        # Should return same ID
        assert id2 == id1

        # URL should be updated
        episode = temp_db.get_episode_by_id(id1)
        assert episode['episode_url'] == "url2"


class TestStatusUpdates:
    """Tests for status update methods."""

    def test_mark_downloading(self, temp_db):
        """GIVEN pending episode WHEN marking downloading THEN status updates."""
        episode_id = temp_db.add_episode("Test", "Episode 1")
        temp_db.mark_downloading(episode_id)

        episode = temp_db.get_episode_by_id(episode_id)
        assert episode['status'] == 'downloading'
        assert episode['download_started_at'] is not None

    def test_mark_downloaded(self, temp_db):
        """GIVEN downloading episode WHEN marking downloaded THEN saves path."""
        episode_id = temp_db.add_episode("Test", "Episode 1")
        temp_db.mark_downloaded(episode_id, "/path/to/audio.mp3")

        episode = temp_db.get_episode_by_id(episode_id)
        assert episode['status'] == 'downloaded'
        assert episode['audio_path'] == "/path/to/audio.mp3"
        assert episode['download_completed_at'] is not None

    def test_mark_transcribing(self, temp_db):
        """GIVEN downloaded episode WHEN marking transcribing THEN status updates."""
        episode_id = temp_db.add_episode("Test", "Episode 1")
        temp_db.mark_transcribing(episode_id)

        episode = temp_db.get_episode_by_id(episode_id)
        assert episode['status'] == 'transcribing'
        assert episode['transcribe_started_at'] is not None

    def test_mark_transcribed(self, temp_db):
        """GIVEN transcribing episode WHEN marking transcribed THEN saves path."""
        episode_id = temp_db.add_episode("Test", "Episode 1")
        temp_db.mark_transcribed(episode_id, "/path/to/transcript.txt")

        episode = temp_db.get_episode_by_id(episode_id)
        assert episode['status'] == 'transcribed'
        assert episode['transcript_path'] == "/path/to/transcript.txt"

    def test_mark_enriched(self, temp_db):
        """GIVEN transcribed episode WHEN marking enriched THEN saves path."""
        episode_id = temp_db.add_episode("Test", "Episode 1")
        temp_db.mark_enriched(episode_id, "/path/to/enrichment.json")

        episode = temp_db.get_episode_by_id(episode_id)
        assert episode['status'] == 'enriched'
        assert episode['enrichment_path'] == "/path/to/enrichment.json"

    def test_mark_failed(self, temp_db):
        """GIVEN episode WHEN marking failed THEN saves error message."""
        episode_id = temp_db.add_episode("Test", "Episode 1")
        temp_db.mark_failed(episode_id, "Connection timeout")

        episode = temp_db.get_episode_by_id(episode_id)
        assert episode['status'] == 'failed'
        assert episode['error_message'] == "Connection timeout"

    def test_mark_skipped(self, temp_db):
        """GIVEN episode WHEN marking skipped THEN saves reason."""
        episode_id = temp_db.add_episode("Test", "Episode 1")
        temp_db.mark_skipped(episode_id, "Already exists")

        episode = temp_db.get_episode_by_id(episode_id)
        assert episode['status'] == 'skipped'
        assert episode['error_message'] == "Already exists"


class TestQueries:
    """Tests for query methods."""

    def test_get_episodes_by_status(self, temp_db):
        """GIVEN multiple episodes WHEN filtering by status THEN returns matches."""
        temp_db.add_episode("Test", "Episode 1")
        temp_db.add_episode("Test", "Episode 2")
        ep3_id = temp_db.add_episode("Test", "Episode 3")
        temp_db.mark_downloaded(ep3_id, "/path/to/ep3.mp3")

        pending = temp_db.get_episodes_by_status(EpisodeStatus.PENDING)
        downloaded = temp_db.get_episodes_by_status(EpisodeStatus.DOWNLOADED)

        assert len(pending) == 2
        assert len(downloaded) == 1
        assert downloaded[0]['episode_title'] == "Episode 3"

    def test_get_pending_downloads(self, temp_db):
        """GIVEN episodes WHEN getting pending downloads THEN returns pending."""
        temp_db.add_episode("Test", "Episode 1")
        temp_db.add_episode("Test", "Episode 2")

        pending = temp_db.get_pending_downloads()
        assert len(pending) == 2

    def test_get_pending_transcriptions(self, temp_db):
        """GIVEN downloaded episodes WHEN getting pending transcriptions THEN returns them."""
        ep1_id = temp_db.add_episode("Test", "Episode 1")
        ep2_id = temp_db.add_episode("Test", "Episode 2")
        temp_db.mark_downloaded(ep1_id, "/path/ep1.mp3")
        temp_db.mark_downloaded(ep2_id, "/path/ep2.mp3")

        pending = temp_db.get_pending_transcriptions()
        assert len(pending) == 2

    def test_filter_by_podcast(self, temp_db):
        """GIVEN episodes from multiple podcasts WHEN filtering THEN returns matches."""
        temp_db.add_episode("Podcast A", "Episode 1")
        temp_db.add_episode("Podcast A", "Episode 2")
        temp_db.add_episode("Podcast B", "Episode 1")

        podcast_a = temp_db.get_pending_downloads(podcast_name="Podcast A")
        podcast_b = temp_db.get_pending_downloads(podcast_name="Podcast B")

        assert len(podcast_a) == 2
        assert len(podcast_b) == 1

    def test_get_stats(self, temp_db):
        """GIVEN episodes in various states WHEN getting stats THEN returns counts."""
        # Add episodes in different states
        ep1_id = temp_db.add_episode("Test", "Episode 1")
        ep2_id = temp_db.add_episode("Test", "Episode 2")
        ep3_id = temp_db.add_episode("Test", "Episode 3")

        temp_db.mark_downloaded(ep1_id, "/path/ep1.mp3")
        temp_db.mark_transcribed(ep2_id, "/path/ep2.txt")
        temp_db.mark_failed(ep3_id, "Error")

        stats = temp_db.get_stats()

        assert stats['downloaded'] == 1
        assert stats['transcribed'] == 1
        assert stats['failed'] == 1
        assert stats['total'] == 3

    def test_get_podcast_stats(self, temp_db):
        """GIVEN episodes from multiple podcasts WHEN getting stats THEN breaks down by podcast."""
        temp_db.add_episode("Podcast A", "Episode 1")
        temp_db.add_episode("Podcast A", "Episode 2")
        temp_db.add_episode("Podcast B", "Episode 1")

        stats = temp_db.get_podcast_stats()

        assert len(stats) == 2
        podcast_a = next(s for s in stats if s['podcast_name'] == 'Podcast A')
        assert podcast_a['total'] == 2


class TestLocking:
    """Tests for concurrent worker locking."""

    def test_acquire_lock_succeeds(self, temp_db):
        """GIVEN unlocked episode WHEN acquiring lock THEN succeeds."""
        episode_id = temp_db.add_episode("Test", "Episode 1")
        result = temp_db.acquire_lock(episode_id, "worker-1")
        assert result is True

    def test_acquire_lock_fails_if_already_locked(self, temp_db):
        """GIVEN locked episode WHEN acquiring lock THEN fails."""
        episode_id = temp_db.add_episode("Test", "Episode 1")
        temp_db.acquire_lock(episode_id, "worker-1")

        result = temp_db.acquire_lock(episode_id, "worker-2")
        assert result is False

    def test_release_lock_succeeds(self, temp_db):
        """GIVEN locked episode WHEN releasing by owner THEN succeeds."""
        episode_id = temp_db.add_episode("Test", "Episode 1")
        temp_db.acquire_lock(episode_id, "worker-1")

        result = temp_db.release_lock(episode_id, "worker-1")
        assert result is True

    def test_release_lock_fails_if_not_owner(self, temp_db):
        """GIVEN locked episode WHEN releasing by non-owner THEN fails."""
        episode_id = temp_db.add_episode("Test", "Episode 1")
        temp_db.acquire_lock(episode_id, "worker-1")

        result = temp_db.release_lock(episode_id, "worker-2")
        assert result is False

    def test_can_reacquire_after_release(self, temp_db):
        """GIVEN released lock WHEN acquiring again THEN succeeds."""
        episode_id = temp_db.add_episode("Test", "Episode 1")
        temp_db.acquire_lock(episode_id, "worker-1")
        temp_db.release_lock(episode_id, "worker-1")

        result = temp_db.acquire_lock(episode_id, "worker-2")
        assert result is True


class TestRecovery:
    """Tests for crash recovery."""

    def test_reset_stuck_downloading(self, temp_db):
        """GIVEN stuck downloading episode WHEN resetting THEN returns to pending."""
        episode_id = temp_db.add_episode("Test", "Episode 1")
        temp_db.mark_downloading(episode_id)

        reset_count = temp_db.reset_stuck_episodes()

        assert reset_count == 1
        episode = temp_db.get_episode_by_id(episode_id)
        assert episode['status'] == 'pending'

    def test_reset_stuck_transcribing(self, temp_db):
        """GIVEN stuck transcribing episode WHEN resetting THEN returns to downloaded."""
        episode_id = temp_db.add_episode("Test", "Episode 1")
        temp_db.update_status(episode_id, EpisodeStatus.TRANSCRIBING)

        temp_db.reset_stuck_episodes()

        episode = temp_db.get_episode_by_id(episode_id)
        assert episode['status'] == 'downloaded'

    def test_reset_stuck_enriching(self, temp_db):
        """GIVEN stuck enriching episode WHEN resetting THEN returns to transcribed."""
        episode_id = temp_db.add_episode("Test", "Episode 1")
        temp_db.update_status(episode_id, EpisodeStatus.ENRICHING)

        temp_db.reset_stuck_episodes()

        episode = temp_db.get_episode_by_id(episode_id)
        assert episode['status'] == 'transcribed'

    def test_reset_does_not_affect_completed(self, temp_db):
        """GIVEN completed episodes WHEN resetting THEN not affected."""
        ep1_id = temp_db.add_episode("Test", "Episode 1")
        ep2_id = temp_db.add_episode("Test", "Episode 2")

        temp_db.mark_enriched(ep1_id, "/path/enriched.json")
        temp_db.mark_failed(ep2_id, "Error")

        temp_db.reset_stuck_episodes()

        ep1 = temp_db.get_episode_by_id(ep1_id)
        ep2 = temp_db.get_episode_by_id(ep2_id)

        assert ep1['status'] == 'enriched'
        assert ep2['status'] == 'failed'


class TestModuleImports:
    """Tests for module imports."""

    def test_can_import_from_db(self):
        """GIVEN db module WHEN importing THEN succeeds."""
        from scripts.db import ProgressDB, EpisodeStatus, get_db, init_db

        assert ProgressDB is not None
        assert EpisodeStatus is not None
        assert callable(get_db)
        assert callable(init_db)
