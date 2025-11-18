"""
Unit tests for retry utilities.

Tests cover:
- Retry decorator with exponential backoff
- Transient vs permanent error detection
- Convenience decorators
"""

import pytest
import time
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add scripts to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from utils.retry import (
    retry,
    retry_with_backoff,
    retry_network,
    retry_download,
    retry_api,
    is_transient_error,
    TRANSIENT_EXCEPTIONS,
    TRANSIENT_HTTP_CODES,
    PERMANENT_HTTP_CODES,
)


class TestRetryDecorator:
    """Tests for the retry decorator."""

    def test_succeeds_first_try(self):
        """GIVEN function that succeeds WHEN called THEN returns result immediately."""
        call_count = 0

        @retry(max_retries=3)
        def successful():
            nonlocal call_count
            call_count += 1
            return "success"

        result = successful()

        assert result == "success"
        assert call_count == 1

    def test_retries_on_transient_error(self):
        """GIVEN transient error WHEN retrying THEN eventually succeeds."""
        call_count = 0

        @retry(max_retries=3, base_delay=0.01)
        def fails_twice():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Transient failure")
            return "success"

        result = fails_twice()

        assert result == "success"
        assert call_count == 3

    def test_raises_after_max_retries(self):
        """GIVEN persistent error WHEN all retries exhausted THEN raises."""
        call_count = 0

        @retry(max_retries=2, base_delay=0.01)
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Always fails")

        with pytest.raises(ConnectionError, match="Always fails"):
            always_fails()

        assert call_count == 3  # Initial + 2 retries

    def test_exponential_backoff(self):
        """GIVEN exponential backoff WHEN retrying THEN delays increase."""
        delays = []
        call_count = 0

        def track_delay(exc, attempt, delay):
            delays.append(delay)

        @retry(max_retries=3, base_delay=0.1, exponential_base=2.0, on_retry=track_delay)
        def fails_always():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("fail")

        with pytest.raises(ConnectionError):
            fails_always()

        # Expected delays: 0.1, 0.2, 0.4
        assert len(delays) == 3
        assert abs(delays[0] - 0.1) < 0.01
        assert abs(delays[1] - 0.2) < 0.01
        assert abs(delays[2] - 0.4) < 0.01

    def test_max_delay_cap(self):
        """GIVEN max_delay WHEN delay exceeds cap THEN uses cap."""
        delays = []

        def track_delay(exc, attempt, delay):
            delays.append(delay)

        @retry(max_retries=5, base_delay=10.0, max_delay=15.0, on_retry=track_delay)
        def fails():
            raise ConnectionError("fail")

        with pytest.raises(ConnectionError):
            fails()

        # All delays should be capped at 15.0
        assert all(d <= 15.0 for d in delays)

    def test_preserves_function_metadata(self):
        """GIVEN decorated function WHEN checking metadata THEN preserved."""
        @retry()
        def documented_function():
            """This is the docstring."""
            return "result"

        assert documented_function.__name__ == "documented_function"
        assert "docstring" in documented_function.__doc__


class TestIsTransientError:
    """Tests for is_transient_error function."""

    def test_connection_error_is_transient(self):
        """GIVEN ConnectionError WHEN checking THEN is transient."""
        assert is_transient_error(ConnectionError("reset")) is True

    def test_timeout_error_is_transient(self):
        """GIVEN TimeoutError WHEN checking THEN is transient."""
        assert is_transient_error(TimeoutError("timed out")) is True

    def test_connection_reset_is_transient(self):
        """GIVEN ConnectionResetError WHEN checking THEN is transient."""
        assert is_transient_error(ConnectionResetError("reset")) is True

    def test_value_error_not_transient(self):
        """GIVEN ValueError WHEN checking THEN not transient."""
        assert is_transient_error(ValueError("bad value")) is False

    def test_type_error_not_transient(self):
        """GIVEN TypeError WHEN checking THEN not transient."""
        assert is_transient_error(TypeError("wrong type")) is False

    def test_http_429_is_transient(self):
        """GIVEN HTTP 429 error WHEN checking THEN is transient."""
        mock_response = Mock()
        mock_response.status_code = 429
        error = Exception("rate limited")
        error.response = mock_response

        assert is_transient_error(error) is True

    def test_http_503_is_transient(self):
        """GIVEN HTTP 503 error WHEN checking THEN is transient."""
        mock_response = Mock()
        mock_response.status_code = 503
        error = Exception("service unavailable")
        error.response = mock_response

        assert is_transient_error(error) is True

    def test_http_404_not_transient(self):
        """GIVEN HTTP 404 error WHEN checking THEN not transient."""
        mock_response = Mock()
        mock_response.status_code = 404
        error = Exception("not found")
        error.response = mock_response

        assert is_transient_error(error) is False

    def test_http_403_not_transient(self):
        """GIVEN HTTP 403 error WHEN checking THEN not transient."""
        mock_response = Mock()
        mock_response.status_code = 403
        error = Exception("forbidden")
        error.response = mock_response

        assert is_transient_error(error) is False


class TestRetryWithBackoff:
    """Tests for retry_with_backoff function."""

    def test_calls_function_with_args(self):
        """GIVEN function and args WHEN calling THEN passes arguments."""
        def add(a, b):
            return a + b

        result = retry_with_backoff(add, args=(2, 3))

        assert result == 5

    def test_calls_function_with_kwargs(self):
        """GIVEN function and kwargs WHEN calling THEN passes keyword arguments."""
        def greet(name, greeting="Hello"):
            return f"{greeting}, {name}!"

        result = retry_with_backoff(greet, args=("World",), kwargs={"greeting": "Hi"})

        assert result == "Hi, World!"

    def test_retries_on_failure(self):
        """GIVEN failing function WHEN retrying THEN eventually succeeds."""
        call_count = 0

        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("flaky")
            return "ok"

        result = retry_with_backoff(flaky, max_retries=3, base_delay=0.01)

        assert result == "ok"
        assert call_count == 2


class TestConvenienceDecorators:
    """Tests for convenience retry decorators."""

    def test_retry_network_works(self):
        """GIVEN retry_network decorator WHEN applied THEN works correctly."""
        @retry_network
        def network_call():
            return "ok"

        assert network_call() == "ok"

    def test_retry_download_works(self):
        """GIVEN retry_download decorator WHEN applied THEN works correctly."""
        @retry_download
        def download():
            return "data"

        assert download() == "data"

    def test_retry_api_works(self):
        """GIVEN retry_api decorator WHEN applied THEN works correctly."""
        @retry_api
        def api_call():
            return {"status": "ok"}

        assert api_call() == {"status": "ok"}


class TestConstants:
    """Tests for module constants."""

    def test_transient_exceptions_contains_expected(self):
        """GIVEN TRANSIENT_EXCEPTIONS WHEN checking THEN has expected types."""
        assert ConnectionError in TRANSIENT_EXCEPTIONS
        assert TimeoutError in TRANSIENT_EXCEPTIONS
        assert ConnectionResetError in TRANSIENT_EXCEPTIONS

    def test_transient_http_codes_contains_expected(self):
        """GIVEN TRANSIENT_HTTP_CODES WHEN checking THEN has expected codes."""
        assert 429 in TRANSIENT_HTTP_CODES  # Too Many Requests
        assert 500 in TRANSIENT_HTTP_CODES  # Internal Server Error
        assert 503 in TRANSIENT_HTTP_CODES  # Service Unavailable

    def test_permanent_http_codes_contains_expected(self):
        """GIVEN PERMANENT_HTTP_CODES WHEN checking THEN has expected codes."""
        assert 400 in PERMANENT_HTTP_CODES  # Bad Request
        assert 403 in PERMANENT_HTTP_CODES  # Forbidden
        assert 404 in PERMANENT_HTTP_CODES  # Not Found


class TestModuleImports:
    """Tests for module imports."""

    def test_can_import_from_utils(self):
        """GIVEN retry module WHEN importing from utils THEN succeeds."""
        from scripts.utils import retry, retry_network, is_transient_error

        assert callable(retry)
        assert callable(retry_network)
        assert callable(is_transient_error)
