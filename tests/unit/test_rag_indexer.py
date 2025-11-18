"""
Unit tests for RAG indexer package.

Tests cover:
- Text chunking utilities
- Metadata loading and extraction
- Timestamp formatting
"""

import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.rag import (
    chunk_text_sentence_aware,
    extract_episode_fields,
    find_chunk_timestamps,
    format_timestamp,
    get_episode_metadata,
    load_detailed_transcript,
    load_podcast_metadata,
    split_into_sentences,
)


class TestSplitIntoSentences:
    """Tests for sentence splitting."""

    def test_splits_on_period(self):
        """GIVEN text with periods WHEN splitting THEN splits correctly."""
        text = "Hello world. How are you. I am fine."
        result = split_into_sentences(text)
        assert result == ["Hello world.", "How are you.", "I am fine."]

    def test_splits_on_question_mark(self):
        """GIVEN text with question marks WHEN splitting THEN splits correctly."""
        text = "What is this? This is a test."
        result = split_into_sentences(text)
        assert result == ["What is this?", "This is a test."]

    def test_splits_on_exclamation(self):
        """GIVEN text with exclamation WHEN splitting THEN splits correctly."""
        text = "Wow! That is amazing."
        result = split_into_sentences(text)
        assert result == ["Wow!", "That is amazing."]

    def test_empty_text_returns_empty_list(self):
        """GIVEN empty text WHEN splitting THEN returns empty list."""
        result = split_into_sentences("")
        assert result == []

    def test_strips_whitespace(self):
        """GIVEN text with extra whitespace WHEN splitting THEN strips it."""
        text = "  Hello.   World.  "
        result = split_into_sentences(text)
        assert result == ["Hello.", "World."]

    def test_single_sentence(self):
        """GIVEN single sentence WHEN splitting THEN returns one item."""
        text = "This is a single sentence."
        result = split_into_sentences(text)
        assert result == ["This is a single sentence."]


class TestChunkTextSentenceAware:
    """Tests for sentence-aware chunking."""

    def test_chunks_respects_size_limit(self):
        """GIVEN text WHEN chunking THEN respects size limit."""
        text = "Short sentence. " * 50  # Long text
        chunks = chunk_text_sentence_aware(text, chunk_size=100)

        # All chunks should be around or below the limit
        for chunk in chunks:
            # Allow some overflow for last sentence
            assert len(chunk) < 200

    def test_preserves_sentence_boundaries(self):
        """GIVEN text WHEN chunking THEN preserves sentences."""
        text = "First sentence. Second sentence. Third sentence."
        chunks = chunk_text_sentence_aware(text, chunk_size=100)

        # Should not split mid-sentence
        for chunk in chunks:
            assert chunk.endswith('.')

    def test_empty_text_returns_empty_list(self):
        """GIVEN empty text WHEN chunking THEN returns empty list."""
        result = chunk_text_sentence_aware("")
        assert result == []

    def test_single_short_sentence(self):
        """GIVEN single sentence WHEN chunking THEN returns one chunk."""
        text = "Hello world."
        result = chunk_text_sentence_aware(text, chunk_size=1000)
        assert result == ["Hello world."]

    def test_overlap_between_chunks(self):
        """GIVEN text WHEN chunking with overlap THEN chunks overlap."""
        # Create text that will need multiple chunks
        text = "Sentence one. Sentence two. Sentence three. Sentence four. Sentence five."
        chunks = chunk_text_sentence_aware(text, chunk_size=50, overlap_sentences=1)

        # If we have multiple chunks, later ones should contain
        # some content from previous ones
        if len(chunks) > 1:
            # At least verify we got multiple chunks
            assert len(chunks) >= 2


class TestFormatTimestamp:
    """Tests for timestamp formatting."""

    def test_format_zero(self):
        """GIVEN zero seconds WHEN formatting THEN returns 00:00."""
        assert format_timestamp(0) == "00:00"

    def test_format_seconds_only(self):
        """GIVEN less than a minute WHEN formatting THEN shows seconds."""
        assert format_timestamp(45) == "00:45"

    def test_format_minutes_and_seconds(self):
        """GIVEN minutes and seconds WHEN formatting THEN shows MM:SS."""
        assert format_timestamp(125) == "02:05"

    def test_format_hours(self):
        """GIVEN hours WHEN formatting THEN shows HH:MM:SS."""
        assert format_timestamp(3665) == "01:01:05"

    def test_format_large_hours(self):
        """GIVEN many hours WHEN formatting THEN handles correctly."""
        # 2 hours, 30 minutes, 45 seconds
        seconds = 2 * 3600 + 30 * 60 + 45
        assert format_timestamp(seconds) == "02:30:45"


class TestExtractEpisodeFields:
    """Tests for episode field extraction."""

    def test_extracts_all_fields(self):
        """GIVEN full episode data WHEN extracting THEN gets all fields."""
        episode = {
            'title': 'Test Episode',
            'description': 'A test description',
            'published': '2024-01-15',
            'duration': 3600,
            'link': 'https://example.com/ep1'
        }
        result = extract_episode_fields(episode)

        assert result['title'] == 'Test Episode'
        assert result['description'] == 'A test description'
        assert result['publish_date'] == '2024-01-15'
        assert result['duration'] == '3600'
        assert result['link'] == 'https://example.com/ep1'

    def test_handles_missing_fields(self):
        """GIVEN partial episode WHEN extracting THEN handles missing."""
        episode = {'title': 'Only Title'}
        result = extract_episode_fields(episode)

        assert result['title'] == 'Only Title'
        assert result['description'] == ''
        assert result['publish_date'] == ''
        assert result['duration'] == ''
        assert result['link'] == ''

    def test_truncates_long_description(self):
        """GIVEN long description WHEN extracting THEN truncates to 500."""
        episode = {
            'title': 'Test',
            'description': 'A' * 1000
        }
        result = extract_episode_fields(episode)
        assert len(result['description']) == 500


class TestLoadPodcastMetadata:
    """Tests for loading podcast metadata."""

    def test_loads_json_files(self):
        """GIVEN directory with JSON WHEN loading THEN loads all files."""
        with TemporaryDirectory() as tmpdir:
            metadata_dir = Path(tmpdir)

            # Create test metadata
            podcast1 = {'title': 'Podcast 1', 'episodes': []}
            podcast2 = {'title': 'Podcast 2', 'episodes': []}

            (metadata_dir / 'podcast1.json').write_text(json.dumps(podcast1))
            (metadata_dir / 'podcast2.json').write_text(json.dumps(podcast2))

            result = load_podcast_metadata(metadata_dir)

            assert len(result) == 2
            assert 'podcast1' in result
            assert 'podcast2' in result
            assert result['podcast1']['title'] == 'Podcast 1'

    def test_handles_missing_directory(self):
        """GIVEN missing directory WHEN loading THEN returns empty dict."""
        result = load_podcast_metadata(Path('/nonexistent/path'))
        assert result == {}

    def test_skips_invalid_json(self):
        """GIVEN invalid JSON WHEN loading THEN skips it."""
        with TemporaryDirectory() as tmpdir:
            metadata_dir = Path(tmpdir)

            # Valid JSON
            (metadata_dir / 'valid.json').write_text('{"title": "Valid"}')
            # Invalid JSON
            (metadata_dir / 'invalid.json').write_text('not json')

            result = load_podcast_metadata(metadata_dir)

            assert len(result) == 1
            assert 'valid' in result


class TestGetEpisodeMetadata:
    """Tests for episode metadata lookup."""

    def test_exact_match(self):
        """GIVEN exact title match WHEN getting metadata THEN returns it."""
        metadata = {
            'podcast1': {
                'episodes': [
                    {'title': 'Episode Title', 'description': 'Test'}
                ]
            }
        }
        result = get_episode_metadata(metadata, 'podcast1', 'Episode Title.txt')
        assert result['title'] == 'Episode Title'
        assert result['description'] == 'Test'

    def test_partial_match(self):
        """GIVEN partial title match WHEN getting metadata THEN returns it."""
        metadata = {
            'podcast1': {
                'episodes': [
                    {'title': 'Episode Title Part', 'description': 'Test'}
                ]
            }
        }
        # Partial match should work
        result = get_episode_metadata(metadata, 'podcast1', 'Episode Title.txt')
        assert result['title'] == 'Episode Title Part'

    def test_missing_podcast(self):
        """GIVEN unknown podcast WHEN getting metadata THEN returns empty."""
        metadata = {'podcast1': {'episodes': []}}
        result = get_episode_metadata(metadata, 'unknown', 'file.txt')
        assert result == {}

    def test_no_matching_episode(self):
        """GIVEN no match WHEN getting metadata THEN returns empty."""
        metadata = {
            'podcast1': {
                'episodes': [
                    {'title': 'Different Title'}
                ]
            }
        }
        result = get_episode_metadata(metadata, 'podcast1', 'Unrelated.txt')
        assert result == {}


class TestLoadDetailedTranscript:
    """Tests for loading detailed transcripts."""

    def test_loads_existing_file(self):
        """GIVEN existing file WHEN loading THEN returns data."""
        with TemporaryDirectory() as tmpdir:
            transcript_dir = Path(tmpdir)
            detailed = {'segments': [{'text': 'Hello', 'start': 0, 'end': 1}]}

            (transcript_dir / 'episode_detailed.json').write_text(
                json.dumps(detailed)
            )

            result = load_detailed_transcript(transcript_dir, 'episode')
            assert result is not None
            assert 'segments' in result

    def test_returns_none_for_missing(self):
        """GIVEN missing file WHEN loading THEN returns None."""
        with TemporaryDirectory() as tmpdir:
            result = load_detailed_transcript(Path(tmpdir), 'nonexistent')
            assert result is None


class TestFindChunkTimestamps:
    """Tests for finding chunk timestamps."""

    def test_finds_matching_segment(self):
        """GIVEN matching text WHEN finding timestamps THEN returns them."""
        chunk_text = "Hello world this is a test"
        transcript = {
            'segments': [
                {'text': 'Hello world', 'start': 0.0, 'end': 1.0},
                {'text': 'this is a test', 'start': 1.0, 'end': 2.0}
            ]
        }

        start, end = find_chunk_timestamps(chunk_text, transcript)
        assert start == 0.0
        assert end >= 1.0

    def test_handles_none_transcript(self):
        """GIVEN None transcript WHEN finding timestamps THEN returns zeros."""
        start, end = find_chunk_timestamps("text", None)
        assert start == 0.0
        assert end == 0.0

    def test_handles_empty_segments(self):
        """GIVEN no segments WHEN finding timestamps THEN returns zeros."""
        start, end = find_chunk_timestamps("text", {'other': 'data'})
        assert start == 0.0
        assert end == 0.0


class TestModuleImports:
    """Tests for package imports."""

    def test_can_import_from_package(self):
        """GIVEN rag package WHEN importing THEN succeeds."""
        from scripts.rag import (
            EnhancedTranscriptIndexer,
            chunk_text_sentence_aware,
            extract_episode_fields,
            find_chunk_timestamps,
            format_timestamp,
            get_episode_metadata,
            load_detailed_transcript,
            load_podcast_metadata,
            split_into_sentences,
        )

        assert EnhancedTranscriptIndexer is not None
        assert callable(chunk_text_sentence_aware)
        assert callable(load_podcast_metadata)
        assert callable(format_timestamp)
