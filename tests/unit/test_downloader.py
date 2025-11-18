"""
Unit tests for podcast_downloader.py utility functions.

Tests cover:
- sanitize_filename: Filename sanitization for various edge cases
- parse_opml: OPML file parsing
- get_feed_by_name: Feed lookup by name
"""

import pytest
import sys
from pathlib import Path

# Add scripts to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from podcast_downloader import sanitize_filename, parse_opml, get_feed_by_name


class TestSanitizeFilename:
    """Tests for sanitize_filename function."""

    def test_sanitize_filename_normal_text(self):
        """GIVEN normal text WHEN sanitized THEN returns unchanged."""
        result = sanitize_filename("Episode 1 Introduction")
        assert result == "Episode 1 Introduction"

    def test_sanitize_filename_removes_invalid_chars(self):
        """GIVEN text with invalid chars WHEN sanitized THEN removes them."""
        result = sanitize_filename('Episode: "Test" <Part> 1/2')
        assert result == "Episode Test Part 12"
        assert ':' not in result
        assert '"' not in result
        assert '<' not in result
        assert '>' not in result
        assert '/' not in result

    def test_sanitize_filename_collapses_spaces(self):
        """GIVEN text with multiple spaces WHEN sanitized THEN collapses to single."""
        result = sanitize_filename("Episode    with   many    spaces")
        assert result == "Episode with many spaces"
        assert "  " not in result

    def test_sanitize_filename_truncates_long_names(self):
        """GIVEN very long text WHEN sanitized THEN truncates to 150 chars."""
        long_text = "A" * 200
        result = sanitize_filename(long_text)
        assert len(result) == 150

    def test_sanitize_filename_strips_whitespace(self):
        """GIVEN text with leading/trailing spaces WHEN sanitized THEN strips them."""
        result = sanitize_filename("  Episode Title  ")
        assert result == "Episode Title"

    def test_sanitize_filename_empty_string(self):
        """GIVEN empty string WHEN sanitized THEN returns empty string."""
        result = sanitize_filename("")
        assert result == ""

    def test_sanitize_filename_only_invalid_chars(self):
        """GIVEN only invalid chars WHEN sanitized THEN returns empty string."""
        result = sanitize_filename(':<>"/\\|?*')
        assert result == ""

    def test_sanitize_filename_preserves_numbers(self):
        """GIVEN text with numbers WHEN sanitized THEN preserves them."""
        result = sanitize_filename("Episode 123 - Part 45")
        assert "123" in result
        assert "45" in result

    def test_sanitize_filename_preserves_hyphens(self):
        """GIVEN text with hyphens WHEN sanitized THEN preserves them."""
        result = sanitize_filename("Episode 1 - Introduction - Part A")
        assert "-" in result

    def test_sanitize_filename_unicode_characters(self):
        """GIVEN text with unicode WHEN sanitized THEN preserves unicode."""
        result = sanitize_filename("Episode café résumé")
        assert "café" in result
        assert "résumé" in result

    def test_sanitize_filename_question_marks_removed(self):
        """GIVEN text with question marks WHEN sanitized THEN removes them."""
        result = sanitize_filename("What is Truth?")
        assert "?" not in result
        assert result == "What is Truth"

    def test_sanitize_filename_backslash_removed(self):
        """GIVEN text with backslash WHEN sanitized THEN removes it."""
        result = sanitize_filename("Episode\\Test")
        assert "\\" not in result

    def test_sanitize_filename_pipe_removed(self):
        """GIVEN text with pipe WHEN sanitized THEN removes it."""
        result = sanitize_filename("Episode | Test")
        assert "|" not in result


class TestParseOpml:
    """Tests for parse_opml function."""

    def test_parse_opml_extracts_feeds(self, sample_opml_file):
        """GIVEN valid OPML file WHEN parsed THEN returns list of feeds."""
        feeds = parse_opml(sample_opml_file)
        assert len(feeds) == 3

    def test_parse_opml_extracts_titles(self, sample_opml_file):
        """GIVEN valid OPML file WHEN parsed THEN extracts feed titles."""
        feeds = parse_opml(sample_opml_file)
        titles = [f['title'] for f in feeds]
        assert "Test Podcast 1" in titles
        assert "Test Podcast 2" in titles
        assert "Another Show" in titles

    def test_parse_opml_extracts_urls(self, sample_opml_file):
        """GIVEN valid OPML file WHEN parsed THEN extracts feed URLs."""
        feeds = parse_opml(sample_opml_file)
        urls = [f['url'] for f in feeds]
        assert "https://example.com/feed1.xml" in urls
        assert "https://example.com/feed2.xml" in urls

    def test_parse_opml_returns_dicts(self, sample_opml_file):
        """GIVEN valid OPML file WHEN parsed THEN returns list of dicts."""
        feeds = parse_opml(sample_opml_file)
        for feed in feeds:
            assert isinstance(feed, dict)
            assert 'title' in feed
            assert 'url' in feed

    def test_parse_opml_empty_file(self, temp_dir):
        """GIVEN empty OPML file WHEN parsed THEN returns empty list."""
        empty_opml = temp_dir / "empty.opml"
        empty_opml.write_text('''<?xml version="1.0"?>
<opml version="2.0">
  <head><title>Empty</title></head>
  <body></body>
</opml>''')
        feeds = parse_opml(empty_opml)
        assert feeds == []


class TestGetFeedByName:
    """Tests for get_feed_by_name function."""

    def test_get_feed_by_name_exact_match(self, sample_opml_file):
        """GIVEN exact podcast name WHEN searched THEN returns feed."""
        feed = get_feed_by_name(sample_opml_file, "Test Podcast 1")
        assert feed is not None
        assert feed['title'] == "Test Podcast 1"

    def test_get_feed_by_name_case_insensitive(self, sample_opml_file):
        """GIVEN lowercase name WHEN searched THEN returns feed (case insensitive)."""
        feed = get_feed_by_name(sample_opml_file, "test podcast 1")
        assert feed is not None
        assert feed['title'] == "Test Podcast 1"

    def test_get_feed_by_name_partial_match(self, sample_opml_file):
        """GIVEN partial name WHEN searched THEN returns matching feed."""
        feed = get_feed_by_name(sample_opml_file, "Another")
        assert feed is not None
        assert feed['title'] == "Another Show"

    def test_get_feed_by_name_not_found(self, sample_opml_file):
        """GIVEN non-existent name WHEN searched THEN returns None."""
        feed = get_feed_by_name(sample_opml_file, "Nonexistent Podcast")
        assert feed is None

    def test_get_feed_by_name_returns_url(self, sample_opml_file):
        """GIVEN valid name WHEN searched THEN returns feed with URL."""
        feed = get_feed_by_name(sample_opml_file, "Test Podcast 1")
        assert feed['url'] == "https://example.com/feed1.xml"
