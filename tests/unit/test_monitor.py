"""
Unit tests for refactored monitor package.

Tests cover:
- Display utilities
- Configuration values
- Feed analysis utilities (non-IO)
"""

import pytest
import sys
from pathlib import Path

# Add scripts to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from monitor.config import (
    TARGET_DOWNLOADERS,
    TARGET_TRANSCRIBERS,
    TARGET_ENRICHERS,
    REFRESH_INTERVAL,
    STALL_THRESHOLD,
)
from monitor.display import (
    make_progress_bar,
)
from monitor.feed_analyzer import (
    get_book_scores,
    normalize_title,
)


class TestConfig:
    """Tests for configuration values."""

    def test_target_downloaders_positive(self):
        """GIVEN config WHEN checking target THEN positive integer."""
        assert TARGET_DOWNLOADERS > 0
        assert isinstance(TARGET_DOWNLOADERS, int)

    def test_target_transcribers_positive(self):
        """GIVEN config WHEN checking target THEN positive integer."""
        assert TARGET_TRANSCRIBERS > 0
        assert isinstance(TARGET_TRANSCRIBERS, int)

    def test_target_enrichers_positive(self):
        """GIVEN config WHEN checking target THEN positive integer."""
        assert TARGET_ENRICHERS > 0
        assert isinstance(TARGET_ENRICHERS, int)

    def test_refresh_interval_reasonable(self):
        """GIVEN config WHEN checking interval THEN reasonable value."""
        assert REFRESH_INTERVAL >= 1
        assert REFRESH_INTERVAL <= 300  # No more than 5 minutes

    def test_stall_threshold_positive(self):
        """GIVEN config WHEN checking threshold THEN positive integer."""
        assert STALL_THRESHOLD > 0
        assert isinstance(STALL_THRESHOLD, int)


class TestMakeProgressBar:
    """Tests for make_progress_bar function."""

    def test_zero_progress(self):
        """GIVEN 0/100 WHEN making bar THEN shows empty bar."""
        result = make_progress_bar(0, 100, 10)
        assert "░" * 10 in result
        assert "0.0%" in result

    def test_half_progress(self):
        """GIVEN 50/100 WHEN making bar THEN shows half filled."""
        result = make_progress_bar(50, 100, 10)
        assert "█" * 5 in result
        assert "░" * 5 in result
        assert "50.0%" in result

    def test_full_progress(self):
        """GIVEN 100/100 WHEN making bar THEN shows full bar."""
        result = make_progress_bar(100, 100, 10)
        assert "█" * 10 in result
        assert "100.0%" in result

    def test_zero_denominator(self):
        """GIVEN 0/0 WHEN making bar THEN shows empty bar without error."""
        result = make_progress_bar(0, 0, 10)
        assert "░" * 10 in result
        assert "0.0%" in result

    def test_custom_width(self):
        """GIVEN custom width WHEN making bar THEN uses that width."""
        result = make_progress_bar(50, 100, 20)
        # Should have 10 filled + 10 empty = 20 total
        assert "█" * 10 in result
        assert "░" * 10 in result

    def test_format_includes_counts(self):
        """GIVEN counts WHEN making bar THEN includes both in output."""
        result = make_progress_bar(42, 100, 10)
        assert "42" in result
        assert "100" in result

    def test_over_100_percent(self):
        """GIVEN numerator > denominator WHEN making bar THEN caps at 100%."""
        result = make_progress_bar(150, 100, 10)
        # Bar should be full
        assert "█" * 10 in result

    def test_fractional_progress(self):
        """GIVEN fractional progress WHEN making bar THEN rounds correctly."""
        result = make_progress_bar(33, 100, 10)
        # 33% = 3.3 filled, rounds to 3
        assert "█" * 3 in result
        assert "33.0%" in result


class TestGetBookScores:
    """Tests for get_book_scores function."""

    def test_returns_dict(self):
        """GIVEN function WHEN called THEN returns dictionary."""
        scores = get_book_scores()
        assert isinstance(scores, dict)

    def test_scores_are_integers(self):
        """GIVEN scores WHEN checking values THEN all are integers."""
        scores = get_book_scores()
        for name, score in scores.items():
            assert isinstance(score, int), f"{name} has non-int score: {score}"

    def test_scores_in_valid_range(self):
        """GIVEN scores WHEN checking values THEN all between 1-10."""
        scores = get_book_scores()
        for name, score in scores.items():
            assert 1 <= score <= 10, f"{name} has invalid score: {score}"

    def test_contains_known_podcasts(self):
        """GIVEN scores WHEN checking THEN contains expected podcasts."""
        scores = get_book_scores()
        assert 'THE ADAM BUXTON PODCAST' in scores
        assert 'Odd Lots' in scores
        assert 'Blowback' in scores

    def test_adam_buxton_high_score(self):
        """GIVEN Adam Buxton WHEN checking score THEN high score (known for book recs)."""
        scores = get_book_scores()
        assert scores.get('THE ADAM BUXTON PODCAST', 0) >= 8


class TestNormalizeTitle:
    """Tests for normalize_title function."""

    def test_lowercase(self):
        """GIVEN mixed case WHEN normalized THEN lowercase."""
        result = normalize_title("Episode ONE")
        assert result == "episodeone"

    def test_removes_special_chars(self):
        """GIVEN special chars WHEN normalized THEN removes them."""
        result = normalize_title("Episode #1: The Beginning!")
        assert result == "episode1thebeginning"
        assert "#" not in result
        assert ":" not in result
        assert "!" not in result

    def test_removes_spaces(self):
        """GIVEN spaces WHEN normalized THEN removes them."""
        result = normalize_title("Episode One Two Three")
        assert result == "episodeonetwothree"
        assert " " not in result

    def test_preserves_numbers(self):
        """GIVEN numbers WHEN normalized THEN preserves them."""
        result = normalize_title("Episode 123")
        assert "123" in result

    def test_empty_string(self):
        """GIVEN empty string WHEN normalized THEN returns empty."""
        result = normalize_title("")
        assert result == ""

    def test_only_special_chars(self):
        """GIVEN only special chars WHEN normalized THEN returns empty."""
        result = normalize_title("!@#$%^&*()")
        assert result == ""


class TestModuleImports:
    """Tests to verify all module imports work correctly."""

    def test_can_import_config(self):
        """GIVEN monitor.config WHEN importing THEN succeeds."""
        from monitor import config
        assert hasattr(config, 'TARGET_DOWNLOADERS')

    def test_can_import_display(self):
        """GIVEN monitor.display WHEN importing THEN succeeds."""
        from monitor import display
        assert hasattr(display, 'make_progress_bar')
        assert hasattr(display, 'clear_screen')

    def test_can_import_workers(self):
        """GIVEN monitor.workers WHEN importing THEN succeeds."""
        from monitor import workers
        assert hasattr(workers, 'get_worker_counts')
        assert hasattr(workers, 'launch_worker')

    def test_can_import_feed_analyzer(self):
        """GIVEN monitor.feed_analyzer WHEN importing THEN succeeds."""
        from monitor import feed_analyzer
        assert hasattr(feed_analyzer, 'get_book_scores')
        assert hasattr(feed_analyzer, 'fetch_rss_totals')
        assert hasattr(feed_analyzer, 'get_feed_progress')

    def test_package_exports_all(self):
        """GIVEN monitor package WHEN checking __all__ THEN exports key items."""
        from monitor import __all__
        assert 'TARGET_DOWNLOADERS' in __all__
        assert 'make_progress_bar' in __all__
        assert 'get_worker_counts' in __all__
        assert 'get_book_scores' in __all__
