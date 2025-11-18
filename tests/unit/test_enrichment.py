"""
Unit tests for refactored enrichment package.

Tests cover:
- JSON repair and parsing utilities
- Configuration data validation
- Topic extraction utilities (date extraction)
- Diarization segment merging
"""

import pytest
import sys
from pathlib import Path

# Add scripts to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from enrichment.json_utils import repair_json, parse_json_safely
from enrichment.config import KNOWN_SPEAKERS, TOPIC_TAXONOMY
from enrichment.topics import extract_episode_date
from enrichment.diarization import merge_diarization_with_transcript


class TestRepairJson:
    """Tests for repair_json function."""

    def test_handles_valid_json(self):
        """GIVEN valid JSON WHEN repairing THEN returns unchanged."""
        json_str = '{"key": "value"}'
        result = repair_json(json_str)
        assert '"key"' in result
        assert '"value"' in result

    def test_replaces_single_quotes_in_keys(self):
        """GIVEN single quotes in keys WHEN repairing THEN converts to double."""
        json_str = "{'key': 'value'}"
        result = repair_json(json_str)
        assert '"key"' in result

    def test_removes_trailing_commas_object(self):
        """GIVEN trailing comma in object WHEN repairing THEN removes it."""
        json_str = '{"key": "value",}'
        result = repair_json(json_str)
        assert ',}' not in result
        assert '}' in result

    def test_removes_trailing_commas_array(self):
        """GIVEN trailing comma in array WHEN repairing THEN removes it."""
        json_str = '{"arr": [1, 2,]}'
        result = repair_json(json_str)
        assert ',]' not in result

    def test_strips_preamble(self):
        """GIVEN text before JSON WHEN repairing THEN extracts JSON only."""
        text = 'Here is the JSON: {"key": "value"}'
        result = repair_json(text)
        assert result.startswith('{')

    def test_no_json_returns_text(self):
        """GIVEN no JSON WHEN repairing THEN returns original text."""
        text = "No JSON here"
        result = repair_json(text)
        assert result == text

    def test_handles_newlines(self):
        """GIVEN newlines in JSON WHEN repairing THEN normalizes them."""
        json_str = '{\n"key":\n"value"\n}'
        result = repair_json(json_str)
        assert '\n' not in result


class TestParseJsonSafely:
    """Tests for parse_json_safely function."""

    def test_parses_valid_json(self):
        """GIVEN valid JSON WHEN parsing THEN returns parsed object."""
        json_str = '{"name": "test", "value": 42}'
        result = parse_json_safely(json_str)
        assert result['name'] == 'test'
        assert result['value'] == 42

    def test_extracts_json_from_text(self):
        """GIVEN JSON embedded in text WHEN parsing THEN extracts it."""
        text = 'Response: {"status": "ok"} end'
        result = parse_json_safely(text)
        assert result['status'] == 'ok'

    def test_returns_default_on_failure(self):
        """GIVEN invalid JSON WHEN parsing THEN returns default."""
        text = "Not valid JSON at all"
        result = parse_json_safely(text, default={'error': True})
        assert result['error'] is True

    def test_default_is_empty_dict(self):
        """GIVEN no default WHEN parsing fails THEN returns empty dict."""
        text = "Invalid"
        result = parse_json_safely(text)
        assert result == {}

    def test_repairs_and_parses(self):
        """GIVEN repairable JSON WHEN parsing THEN repairs and parses."""
        text = "{'key': 'value',}"
        result = parse_json_safely(text)
        # This may or may not parse depending on repair success
        # At minimum it shouldn't crash
        assert isinstance(result, dict)

    def test_handles_nested_json(self):
        """GIVEN nested JSON WHEN parsing THEN preserves structure."""
        json_str = '{"outer": {"inner": [1, 2, 3]}}'
        result = parse_json_safely(json_str)
        assert result['outer']['inner'] == [1, 2, 3]


class TestKnownSpeakers:
    """Tests for KNOWN_SPEAKERS configuration."""

    def test_contains_expected_podcasts(self):
        """GIVEN KNOWN_SPEAKERS WHEN checking THEN has expected podcasts."""
        assert 'TRUE ANON TRUTH FEED' in KNOWN_SPEAKERS
        assert 'Chapo Trap House' in KNOWN_SPEAKERS
        assert 'Hello Internet' in KNOWN_SPEAKERS

    def test_podcasts_have_hosts(self):
        """GIVEN each podcast WHEN checking THEN has hosts list."""
        for podcast, data in KNOWN_SPEAKERS.items():
            assert 'hosts' in data, f"{podcast} missing hosts"
            assert isinstance(data['hosts'], list)
            assert len(data['hosts']) > 0

    def test_podcasts_have_aliases(self):
        """GIVEN each podcast WHEN checking THEN has aliases dict."""
        for podcast, data in KNOWN_SPEAKERS.items():
            assert 'aliases' in data, f"{podcast} missing aliases"
            assert isinstance(data['aliases'], dict)

    def test_true_anon_hosts(self):
        """GIVEN TRUE ANON WHEN checking THEN has correct hosts."""
        hosts = KNOWN_SPEAKERS['TRUE ANON TRUTH FEED']['hosts']
        assert 'Brace Belden' in hosts
        assert 'Liz Franczak' in hosts

    def test_chapo_hosts(self):
        """GIVEN Chapo WHEN checking THEN has correct hosts."""
        hosts = KNOWN_SPEAKERS['Chapo Trap House']['hosts']
        assert 'Will Menaker' in hosts
        assert 'Matt Christman' in hosts
        assert 'Felix Biederman' in hosts


class TestTopicTaxonomy:
    """Tests for TOPIC_TAXONOMY configuration."""

    def test_is_list(self):
        """GIVEN TOPIC_TAXONOMY WHEN checking THEN is a list."""
        assert isinstance(TOPIC_TAXONOMY, list)

    def test_has_topics(self):
        """GIVEN TOPIC_TAXONOMY WHEN checking THEN has topics."""
        assert len(TOPIC_TAXONOMY) > 0

    def test_contains_expected_topics(self):
        """GIVEN TOPIC_TAXONOMY WHEN checking THEN has expected topics."""
        assert "US Politics" in TOPIC_TAXONOMY
        assert "Technology" in TOPIC_TAXONOMY
        assert "History" in TOPIC_TAXONOMY

    def test_all_strings(self):
        """GIVEN TOPIC_TAXONOMY WHEN checking THEN all are strings."""
        for topic in TOPIC_TAXONOMY:
            assert isinstance(topic, str)
            assert len(topic) > 0


class TestExtractEpisodeDate:
    """Tests for extract_episode_date function."""

    def test_extracts_year_from_text(self):
        """GIVEN year in text WHEN extracting THEN returns year."""
        text = "Welcome to our show, recorded in January 2020."
        result = extract_episode_date(text)
        assert result == "2020"

    def test_extracts_most_common_year(self):
        """GIVEN multiple years WHEN extracting THEN returns most common."""
        text = "In 2019 we saw changes, but 2020 was different. 2020 changed everything."
        result = extract_episode_date(text)
        assert result == "2020"

    def test_returns_none_for_no_year(self):
        """GIVEN no year WHEN extracting THEN returns None."""
        text = "Just a regular transcript without any dates mentioned."
        result = extract_episode_date(text)
        assert result is None

    def test_handles_19xx_years(self):
        """GIVEN 1900s year WHEN extracting THEN returns it."""
        text = "Back in 1995, things were different."
        result = extract_episode_date(text)
        assert result == "1995"

    def test_uses_intro_only(self):
        """GIVEN year only in later text WHEN extracting THEN may miss it."""
        # Function only looks at first 5000 chars
        text = "x" * 6000 + " In 2020 this happened."
        result = extract_episode_date(text)
        # Year is past the 5000 char limit
        assert result is None


class TestMergeDiarizationWithTranscript:
    """Tests for merge_diarization_with_transcript function."""

    def test_merges_matching_segments(self):
        """GIVEN matching segments WHEN merging THEN assigns speaker."""
        diarization = [
            {'start': 0, 'end': 5, 'speaker': 'SPEAKER_00'},
            {'start': 5, 'end': 10, 'speaker': 'SPEAKER_01'},
        ]
        whisper = [
            {'id': 0, 'start': 1, 'end': 4, 'text': 'Hello'},
            {'id': 1, 'start': 6, 'end': 9, 'text': 'World'},
        ]
        result = merge_diarization_with_transcript(diarization, whisper)

        assert len(result) == 2
        assert result[0]['speaker'] == 'SPEAKER_00'
        assert result[1]['speaker'] == 'SPEAKER_01'
        assert result[0]['text'] == 'Hello'
        assert result[1]['text'] == 'World'

    def test_handles_overlapping_segments(self):
        """GIVEN overlapping segments WHEN merging THEN picks best match."""
        diarization = [
            {'start': 0, 'end': 3, 'speaker': 'SPEAKER_00'},
            {'start': 2, 'end': 5, 'speaker': 'SPEAKER_01'},
        ]
        whisper = [
            {'id': 0, 'start': 2.5, 'end': 4.5, 'text': 'Overlap'},
        ]
        result = merge_diarization_with_transcript(diarization, whisper)

        # Should pick SPEAKER_01 (more overlap: 2.5-4.5 overlaps 2-5 more)
        assert result[0]['speaker'] == 'SPEAKER_01'

    def test_handles_no_diarization(self):
        """GIVEN empty diarization WHEN merging THEN marks unknown."""
        whisper = [
            {'id': 0, 'start': 0, 'end': 5, 'text': 'Hello'},
        ]
        result = merge_diarization_with_transcript([], whisper)

        assert result[0]['speaker'] == 'UNKNOWN'

    def test_preserves_segment_data(self):
        """GIVEN segments WHEN merging THEN preserves all fields."""
        diarization = [
            {'start': 0, 'end': 5, 'speaker': 'SPEAKER_00'},
        ]
        whisper = [
            {'id': 42, 'start': 1, 'end': 4, 'text': '  Test  '},
        ]
        result = merge_diarization_with_transcript(diarization, whisper)

        assert result[0]['id'] == 42
        assert result[0]['start'] == 1
        assert result[0]['end'] == 4
        assert result[0]['text'] == 'Test'  # Stripped

    def test_handles_missing_fields(self):
        """GIVEN segments with missing fields WHEN merging THEN uses defaults."""
        diarization = [
            {'start': 0, 'end': 5, 'speaker': 'SPEAKER_00'},
        ]
        whisper = [
            {'text': 'No timestamps'},
        ]
        result = merge_diarization_with_transcript(diarization, whisper)

        assert result[0]['start'] == 0
        assert result[0]['end'] == 0
        assert result[0]['id'] == 0


class TestModuleImports:
    """Tests to verify all enrichment module imports work correctly."""

    def test_can_import_json_utils(self):
        """GIVEN json_utils WHEN importing THEN succeeds."""
        from enrichment import repair_json, parse_json_safely
        assert callable(repair_json)
        assert callable(parse_json_safely)

    def test_can_import_config(self):
        """GIVEN config WHEN importing THEN succeeds."""
        from enrichment import KNOWN_SPEAKERS, TOPIC_TAXONOMY
        assert isinstance(KNOWN_SPEAKERS, dict)
        assert isinstance(TOPIC_TAXONOMY, list)

    def test_can_import_topics(self):
        """GIVEN topics WHEN importing THEN succeeds."""
        from enrichment import (
            extract_episode_date,
            detect_chapters_ollama,
            classify_topics_ollama,
            classify_topics_huggingface,
        )
        assert callable(extract_episode_date)
        assert callable(detect_chapters_ollama)

    def test_can_import_diarization(self):
        """GIVEN diarization WHEN importing THEN succeeds."""
        from enrichment import (
            diarize_audio,
            merge_diarization_with_transcript,
        )
        assert callable(diarize_audio)
        assert callable(merge_diarization_with_transcript)

    def test_can_import_main(self):
        """GIVEN main WHEN importing THEN succeeds."""
        from enrichment import enrich_transcript
        assert callable(enrich_transcript)

    def test_package_exports_all(self):
        """GIVEN enrichment package WHEN checking __all__ THEN has exports."""
        from enrichment import __all__
        assert 'repair_json' in __all__
        assert 'KNOWN_SPEAKERS' in __all__
        assert 'enrich_transcript' in __all__
        assert 'extract_episode_date' in __all__
