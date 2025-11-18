"""
Unit tests for input validation utilities.

Tests cover:
- Podcast name validation
- Episode range validation
- File path validation (including path traversal prevention)
- URL validation
- Whisper model validation
"""

import pytest
import sys
from pathlib import Path

# Add scripts to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from utils.validators import (
    validate_podcast_name,
    validate_episode_range,
    validate_file_path,
    validate_url,
    validate_positive_integer,
    validate_whisper_model,
    ValidationError,
)


class TestValidatePodcastName:
    """Tests for validate_podcast_name function."""

    def test_valid_podcast_name(self):
        """GIVEN valid name WHEN validated THEN returns name."""
        result = validate_podcast_name("My Podcast")
        assert result == "My Podcast"

    def test_strips_whitespace(self):
        """GIVEN name with whitespace WHEN validated THEN strips it."""
        result = validate_podcast_name("  My Podcast  ")
        assert result == "My Podcast"

    def test_empty_name_raises(self):
        """GIVEN empty name WHEN validated THEN raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_podcast_name("")
        assert "cannot be empty" in str(exc_info.value)

    def test_path_traversal_rejected(self):
        """GIVEN name with .. WHEN validated THEN raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_podcast_name("../malicious")
        assert "path traversal" in str(exc_info.value).lower()

    def test_forward_slash_rejected(self):
        """GIVEN name with / WHEN validated THEN raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_podcast_name("my/podcast")
        assert "path separators" in str(exc_info.value)

    def test_backslash_rejected(self):
        """GIVEN name with backslash WHEN validated THEN raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_podcast_name("my\\podcast")
        assert "path separators" in str(exc_info.value)

    def test_too_long_name_rejected(self):
        """GIVEN name >200 chars WHEN validated THEN raises ValidationError."""
        long_name = "A" * 201
        with pytest.raises(ValidationError) as exc_info:
            validate_podcast_name(long_name)
        assert "too long" in str(exc_info.value)

    def test_null_byte_rejected(self):
        """GIVEN name with null byte WHEN validated THEN raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_podcast_name("my\x00podcast")
        assert "null bytes" in str(exc_info.value)

    def test_unicode_allowed(self):
        """GIVEN name with unicode WHEN validated THEN returns name."""
        result = validate_podcast_name("Café Podcast")
        assert result == "Café Podcast"


class TestValidateEpisodeRange:
    """Tests for validate_episode_range function."""

    def test_valid_range(self):
        """GIVEN valid range WHEN validated THEN returns tuple."""
        start, end = validate_episode_range("0:100")
        assert start == 0
        assert end == 100

    def test_valid_mid_range(self):
        """GIVEN mid-range values WHEN validated THEN returns tuple."""
        start, end = validate_episode_range("50:150")
        assert start == 50
        assert end == 150

    def test_empty_range_raises(self):
        """GIVEN empty string WHEN validated THEN raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_episode_range("")
        assert "cannot be empty" in str(exc_info.value)

    def test_missing_colon_raises(self):
        """GIVEN range without colon WHEN validated THEN raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_episode_range("100")
        assert "start:end" in str(exc_info.value)

    def test_non_integer_raises(self):
        """GIVEN non-integer values WHEN validated THEN raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_episode_range("abc:def")
        assert "integers" in str(exc_info.value)

    def test_negative_start_raises(self):
        """GIVEN negative start WHEN validated THEN raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_episode_range("-10:100")
        assert "negative" in str(exc_info.value)

    def test_start_equals_end_raises(self):
        """GIVEN start == end WHEN validated THEN raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_episode_range("50:50")
        assert "less than" in str(exc_info.value)

    def test_start_greater_than_end_raises(self):
        """GIVEN start > end WHEN validated THEN raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_episode_range("100:50")
        assert "less than" in str(exc_info.value)

    def test_too_large_range_raises(self):
        """GIVEN range >10000 WHEN validated THEN raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_episode_range("0:20000")
        assert "too large" in str(exc_info.value)


class TestValidateFilePath:
    """Tests for validate_file_path function."""

    def test_valid_relative_path(self, temp_dir):
        """GIVEN valid relative path WHEN validated THEN returns Path."""
        result = validate_file_path("test.txt", base_dir=temp_dir)
        assert isinstance(result, Path)

    def test_path_traversal_rejected(self, temp_dir):
        """GIVEN path with .. WHEN validated with base_dir THEN raises."""
        with pytest.raises(ValidationError) as exc_info:
            validate_file_path("../outside.txt", base_dir=temp_dir)
        assert "path traversal" in str(exc_info.value).lower()

    def test_absolute_path_rejected_by_default(self):
        """GIVEN absolute path WHEN validated THEN raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_file_path("/etc/passwd")
        assert "Absolute paths" in str(exc_info.value)

    def test_absolute_path_allowed_when_enabled(self):
        """GIVEN absolute path WHEN allow_absolute=True THEN returns Path."""
        result = validate_file_path("/tmp/test.txt", allow_absolute=True)
        assert isinstance(result, Path)

    def test_null_byte_rejected(self, temp_dir):
        """GIVEN path with null byte WHEN validated THEN raises."""
        with pytest.raises(ValidationError) as exc_info:
            validate_file_path("test\x00.txt", base_dir=temp_dir)
        assert "null bytes" in str(exc_info.value)

    def test_empty_path_raises(self):
        """GIVEN empty path WHEN validated THEN raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_file_path("")
        assert "cannot be empty" in str(exc_info.value)

    def test_must_exist_fails_for_missing(self, temp_dir):
        """GIVEN nonexistent path WHEN must_exist=True THEN raises."""
        with pytest.raises(ValidationError) as exc_info:
            validate_file_path("nonexistent.txt", base_dir=temp_dir, must_exist=True)
        assert "does not exist" in str(exc_info.value)

    def test_must_exist_succeeds_for_existing(self, temp_dir):
        """GIVEN existing path WHEN must_exist=True THEN returns Path."""
        # Create a file
        test_file = temp_dir / "exists.txt"
        test_file.write_text("test")

        result = validate_file_path("exists.txt", base_dir=temp_dir, must_exist=True)
        assert result.exists()


class TestValidateUrl:
    """Tests for validate_url function."""

    def test_valid_https_url(self):
        """GIVEN valid HTTPS URL WHEN validated THEN returns URL."""
        result = validate_url("https://example.com/feed.xml")
        assert result == "https://example.com/feed.xml"

    def test_valid_http_url(self):
        """GIVEN valid HTTP URL WHEN validated THEN returns URL."""
        result = validate_url("http://example.com/feed.xml")
        assert result == "http://example.com/feed.xml"

    def test_empty_url_raises(self):
        """GIVEN empty URL WHEN validated THEN raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_url("")
        assert "cannot be empty" in str(exc_info.value)

    def test_missing_scheme_raises(self):
        """GIVEN URL without scheme WHEN validated THEN raises."""
        with pytest.raises(ValidationError) as exc_info:
            validate_url("example.com/feed.xml")
        assert "scheme" in str(exc_info.value)

    def test_invalid_scheme_raises(self):
        """GIVEN URL with disallowed scheme WHEN validated THEN raises."""
        with pytest.raises(ValidationError) as exc_info:
            validate_url("ftp://example.com/file")
        assert "not allowed" in str(exc_info.value)

    def test_custom_allowed_schemes(self):
        """GIVEN custom schemes list WHEN validating THEN allows those schemes."""
        result = validate_url("ftp://example.com/file", allowed_schemes=['ftp'])
        assert result == "ftp://example.com/file"

    def test_missing_host_raises(self):
        """GIVEN URL without host WHEN validated THEN raises."""
        with pytest.raises(ValidationError) as exc_info:
            validate_url("https:///path")
        assert "host" in str(exc_info.value)

    def test_null_byte_rejected(self):
        """GIVEN URL with null byte WHEN validated THEN raises."""
        with pytest.raises(ValidationError) as exc_info:
            validate_url("https://example\x00.com")
        assert "null bytes" in str(exc_info.value)


class TestValidatePositiveInteger:
    """Tests for validate_positive_integer function."""

    def test_valid_positive(self):
        """GIVEN positive integer string WHEN validated THEN returns int."""
        result = validate_positive_integer("42")
        assert result == 42

    def test_one_is_valid(self):
        """GIVEN '1' WHEN validated THEN returns 1."""
        result = validate_positive_integer("1")
        assert result == 1

    def test_zero_raises(self):
        """GIVEN '0' WHEN validated THEN raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_positive_integer("0")
        assert "positive" in str(exc_info.value)

    def test_negative_raises(self):
        """GIVEN negative value WHEN validated THEN raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_positive_integer("-5")
        assert "positive" in str(exc_info.value)

    def test_non_integer_raises(self):
        """GIVEN non-integer WHEN validated THEN raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_positive_integer("abc")
        assert "integer" in str(exc_info.value)

    def test_empty_raises(self):
        """GIVEN empty string WHEN validated THEN raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_positive_integer("")
        assert "cannot be empty" in str(exc_info.value)


class TestValidateWhisperModel:
    """Tests for validate_whisper_model function."""

    def test_valid_models(self):
        """GIVEN valid model names WHEN validated THEN returns lowercase."""
        for model in ['tiny', 'base', 'small', 'medium', 'large']:
            result = validate_whisper_model(model)
            assert result == model

    def test_case_insensitive(self):
        """GIVEN uppercase model WHEN validated THEN returns lowercase."""
        result = validate_whisper_model("BASE")
        assert result == "base"

    def test_strips_whitespace(self):
        """GIVEN model with whitespace WHEN validated THEN strips it."""
        result = validate_whisper_model("  base  ")
        assert result == "base"

    def test_invalid_model_raises(self):
        """GIVEN invalid model WHEN validated THEN raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_whisper_model("huge")
        assert "Invalid model" in str(exc_info.value)

    def test_empty_raises(self):
        """GIVEN empty string WHEN validated THEN raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_whisper_model("")
        assert "cannot be empty" in str(exc_info.value)
