"""
Input validation utilities for podcast archive system.

Provides validation functions to prevent:
- Path traversal attacks
- Invalid input formats
- Security vulnerabilities

All validation functions raise ValidationError on failure.
"""

import re
from pathlib import Path
from typing import Tuple, Optional
from urllib.parse import urlparse


class ValidationError(Exception):
    """Raised when input validation fails."""

    def __init__(self, message: str, field: str = "input"):
        self.message = message
        self.field = field
        super().__init__(f"{field}: {message}")


def validate_podcast_name(name: str) -> str:
    """
    Validate podcast name for safe use in file operations.

    Args:
        name: Podcast name to validate

    Returns:
        Sanitized podcast name

    Raises:
        ValidationError: If name is invalid or potentially malicious
    """
    if not name:
        raise ValidationError("Podcast name cannot be empty", "podcast_name")

    if not isinstance(name, str):
        raise ValidationError("Podcast name must be a string", "podcast_name")

    # Check for path traversal attempts
    if ".." in name:
        raise ValidationError(
            "Podcast name cannot contain '..' (path traversal attempt)",
            "podcast_name"
        )

    if "/" in name or "\\" in name:
        raise ValidationError(
            "Podcast name cannot contain path separators",
            "podcast_name"
        )

    # Check length
    if len(name) > 200:
        raise ValidationError(
            f"Podcast name too long ({len(name)} chars, max 200)",
            "podcast_name"
        )

    # Check for null bytes (security issue)
    if "\x00" in name:
        raise ValidationError(
            "Podcast name cannot contain null bytes",
            "podcast_name"
        )

    return name.strip()


def validate_episode_range(range_str: str) -> Tuple[int, int]:
    """
    Validate episode range format (start:end).

    Args:
        range_str: Range string like "0:100" or "50:150"

    Returns:
        Tuple of (start_index, end_index)

    Raises:
        ValidationError: If range format is invalid
    """
    if not range_str:
        raise ValidationError("Range cannot be empty", "episode_range")

    if ":" not in range_str:
        raise ValidationError(
            "Range must be in format 'start:end' (e.g., '0:100')",
            "episode_range"
        )

    parts = range_str.split(":")
    if len(parts) != 2:
        raise ValidationError(
            "Range must have exactly two parts separated by ':'",
            "episode_range"
        )

    try:
        start = int(parts[0])
        end = int(parts[1])
    except ValueError:
        raise ValidationError(
            "Range values must be integers",
            "episode_range"
        )

    if start < 0:
        raise ValidationError(
            f"Start index cannot be negative (got {start})",
            "episode_range"
        )

    if end < 0:
        raise ValidationError(
            f"End index cannot be negative (got {end})",
            "episode_range"
        )

    if start >= end:
        raise ValidationError(
            f"Start index ({start}) must be less than end index ({end})",
            "episode_range"
        )

    if end - start > 10000:
        raise ValidationError(
            f"Range too large ({end - start} episodes, max 10000)",
            "episode_range"
        )

    return start, end


def validate_file_path(
    path: str,
    base_dir: Optional[Path] = None,
    must_exist: bool = False,
    allow_absolute: bool = False
) -> Path:
    """
    Validate file path for safe use in file operations.

    Args:
        path: File path to validate
        base_dir: If provided, path must be within this directory
        must_exist: If True, path must exist
        allow_absolute: If False, reject absolute paths

    Returns:
        Resolved Path object

    Raises:
        ValidationError: If path is invalid or unsafe
    """
    if not path:
        raise ValidationError("Path cannot be empty", "file_path")

    if not isinstance(path, str):
        raise ValidationError("Path must be a string", "file_path")

    # Check for null bytes
    if "\x00" in path:
        raise ValidationError(
            "Path cannot contain null bytes",
            "file_path"
        )

    # Convert to Path object
    try:
        file_path = Path(path)
    except Exception as e:
        raise ValidationError(f"Invalid path format: {e}", "file_path")

    # Check for absolute paths if not allowed
    if not allow_absolute and file_path.is_absolute():
        raise ValidationError(
            "Absolute paths not allowed",
            "file_path"
        )

    # Resolve the path to handle .. and .
    try:
        if base_dir:
            # Resolve relative to base_dir
            resolved = (base_dir / file_path).resolve()
            base_resolved = base_dir.resolve()

            # Ensure resolved path is within base_dir
            try:
                resolved.relative_to(base_resolved)
            except ValueError:
                raise ValidationError(
                    f"Path escapes base directory (path traversal attempt)",
                    "file_path"
                )
        else:
            resolved = file_path.resolve()
    except Exception as e:
        raise ValidationError(f"Failed to resolve path: {e}", "file_path")

    # Check existence if required
    if must_exist and not resolved.exists():
        raise ValidationError(
            f"Path does not exist: {resolved}",
            "file_path"
        )

    return resolved


def validate_url(url: str, allowed_schemes: Optional[list] = None) -> str:
    """
    Validate URL format and scheme.

    Args:
        url: URL to validate
        allowed_schemes: List of allowed schemes (default: ['http', 'https'])

    Returns:
        Validated URL string

    Raises:
        ValidationError: If URL is invalid
    """
    if not url:
        raise ValidationError("URL cannot be empty", "url")

    if allowed_schemes is None:
        allowed_schemes = ['http', 'https']

    try:
        parsed = urlparse(url)
    except Exception as e:
        raise ValidationError(f"Invalid URL format: {e}", "url")

    if not parsed.scheme:
        raise ValidationError("URL must include scheme (e.g., https://)", "url")

    if parsed.scheme not in allowed_schemes:
        raise ValidationError(
            f"URL scheme '{parsed.scheme}' not allowed. Allowed: {allowed_schemes}",
            "url"
        )

    if not parsed.netloc:
        raise ValidationError("URL must include host", "url")

    # Check for potentially dangerous characters
    if "\x00" in url:
        raise ValidationError("URL cannot contain null bytes", "url")

    return url


def validate_positive_integer(value: str, field_name: str = "value") -> int:
    """
    Validate that a string represents a positive integer.

    Args:
        value: String value to validate
        field_name: Name of field for error messages

    Returns:
        Validated integer

    Raises:
        ValidationError: If value is not a positive integer
    """
    if not value:
        raise ValidationError(f"{field_name} cannot be empty", field_name)

    try:
        int_value = int(value)
    except ValueError:
        raise ValidationError(
            f"{field_name} must be an integer (got '{value}')",
            field_name
        )

    if int_value < 1:
        raise ValidationError(
            f"{field_name} must be positive (got {int_value})",
            field_name
        )

    return int_value


def validate_whisper_model(model: str) -> str:
    """
    Validate Whisper model name.

    Args:
        model: Model name to validate

    Returns:
        Validated model name

    Raises:
        ValidationError: If model name is invalid
    """
    valid_models = ['tiny', 'base', 'small', 'medium', 'large']

    if not model:
        raise ValidationError("Model name cannot be empty", "whisper_model")

    model_lower = model.lower().strip()

    if model_lower not in valid_models:
        raise ValidationError(
            f"Invalid model '{model}'. Valid models: {valid_models}",
            "whisper_model"
        )

    return model_lower
