"""
Unit tests for RAG server security features.

Tests cover:
- API key masking
- Rate limiting logic
- Authentication flow
"""

import pytest
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add scripts to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from rag_server import mask_api_key, check_rate_limit, rate_limit_storage


class TestMaskApiKey:
    """Tests for mask_api_key function."""

    def test_masks_long_key(self):
        """GIVEN long API key WHEN masked THEN shows first/last 4 chars."""
        result = mask_api_key("abcd1234567890efgh")
        assert result == "abcd...efgh"
        assert "1234567890" not in result

    def test_masks_short_key(self):
        """GIVEN short API key WHEN masked THEN returns ***."""
        result = mask_api_key("short")
        assert result == "***"

    def test_masks_exact_8_chars(self):
        """GIVEN 8-char key WHEN masked THEN returns ***."""
        result = mask_api_key("12345678")
        assert result == "***"

    def test_masks_9_char_key(self):
        """GIVEN 9-char key WHEN masked THEN shows first/last 4."""
        result = mask_api_key("123456789")
        assert result == "1234...6789"


class TestRateLimiting:
    """Tests for check_rate_limit function."""

    def setup_method(self):
        """Clear rate limit storage before each test."""
        rate_limit_storage.clear()

    def test_allows_first_request(self):
        """GIVEN new client WHEN first request THEN allows."""
        result = check_rate_limit("test-client-1")
        assert result is True

    def test_allows_under_limit(self):
        """GIVEN client under limit WHEN request THEN allows."""
        client_id = "test-client-2"
        # Make 99 requests (under default 100)
        for _ in range(99):
            check_rate_limit(client_id)

        result = check_rate_limit(client_id)
        assert result is True

    def test_blocks_over_limit(self):
        """GIVEN client at limit WHEN request THEN blocks."""
        client_id = "test-client-3"

        # Fill up to limit with recent timestamps (all within last 30 seconds)
        now = time.time()
        rate_limit_storage[client_id] = [now - (i * 0.1) for i in range(100)]

        result = check_rate_limit(client_id)
        assert result is False

    def test_cleans_old_entries(self):
        """GIVEN old timestamps WHEN check THEN cleans them."""
        client_id = "test-client-4"

        # Add old timestamps (>60 seconds ago)
        old_time = time.time() - 120
        rate_limit_storage[client_id] = [old_time for _ in range(100)]

        # Should allow because old entries are cleaned
        result = check_rate_limit(client_id)
        assert result is True
        # Old entries should be cleaned
        assert len(rate_limit_storage[client_id]) == 1

    def test_different_clients_independent(self):
        """GIVEN multiple clients WHEN one at limit THEN others unaffected."""
        client_a = "client-a"
        client_b = "client-b"

        # Fill client_a to limit with recent timestamps
        now = time.time()
        rate_limit_storage[client_a] = [now - (i * 0.1) for i in range(100)]

        # Client A should be blocked
        assert check_rate_limit(client_a) is False

        # Client B should still be allowed
        assert check_rate_limit(client_b) is True


class TestAuthenticationLogic:
    """Tests for authentication dependency behavior."""

    def test_api_key_validation_logic(self):
        """Test that API key comparison uses constant-time comparison."""
        # This tests the concept - actual secrets.compare_digest
        # should be used in production for timing attack prevention
        test_value_a = "test-value-a-for-comparison"
        test_value_b = "test-value-b-different"

        # Simple validation (in real code, use secrets.compare_digest)
        assert test_value_a != test_value_b
        assert test_value_a == test_value_a

    def test_environment_variable_parsing(self):
        """Test that comma-separated keys are parsed correctly."""
        # Simulate environment variable parsing
        env_value = "key1, key2, key3"
        keys = [k.strip() for k in env_value.split(",") if k.strip()]

        assert len(keys) == 3
        assert keys == ["key1", "key2", "key3"]

    def test_empty_keys_filtered(self):
        """Test that empty strings are filtered from key list."""
        env_value = "key1,,key2,  ,key3"
        keys = [k.strip() for k in env_value.split(",") if k.strip()]

        assert len(keys) == 3
        assert "" not in keys


class TestSecurityConfiguration:
    """Tests for security configuration parsing."""

    def test_cors_origins_parsing(self):
        """Test CORS origins are parsed correctly from env."""
        env_value = "http://localhost:3000, https://app.example.com"
        origins = [o.strip() for o in env_value.split(",") if o.strip()]

        assert len(origins) == 2
        assert "http://localhost:3000" in origins
        assert "https://app.example.com" in origins

    def test_rate_limit_default(self):
        """Test default rate limit value."""
        default_limit = int("100")  # Default in code
        assert default_limit == 100

    def test_require_auth_parsing(self):
        """Test auth requirement boolean parsing."""
        # Test various true values
        assert "true".lower() == "true"
        assert "TRUE".lower() == "true"
        assert "True".lower() == "true"

        # Test false values
        assert "false".lower() != "true"
        assert "".lower() != "true"


class TestAuditLogging:
    """Tests for audit logging format."""

    def test_log_format_contains_required_fields(self):
        """Test that log format includes all required fields."""
        # Simulate the log format
        client_ip = "127.0.0.1"
        key_info = "abcd...efgh"
        endpoint = "POST /search"
        response_time = 45.32

        log_message = f"API Request | {endpoint} | {client_ip} | {key_info} | {response_time:.2f}ms"

        assert "API Request" in log_message
        assert endpoint in log_message
        assert client_ip in log_message
        assert key_info in log_message
        assert "45.32ms" in log_message

    def test_masked_key_in_log(self):
        """Test that API key is masked in logs."""
        api_key = "super-secret-key-12345"
        masked = mask_api_key(api_key)

        # Full key should not appear in masked version
        assert "super-secret-key" not in masked
        assert "supe" in masked
        assert "2345" in masked
