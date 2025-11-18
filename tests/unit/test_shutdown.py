"""
Unit tests for graceful shutdown utilities.

Tests cover:
- Signal handler installation
- Worker registration/unregistration
- Shutdown flag management
- Cleanup callbacks
"""

import pytest
import signal
import sys
from pathlib import Path

# Add scripts to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from utils.shutdown import (
    GracefulShutdown,
    get_shutdown_handler,
    should_shutdown,
    request_shutdown,
)


class TestGracefulShutdown:
    """Tests for GracefulShutdown class."""

    def test_init_default_timeout(self):
        """GIVEN new handler WHEN created THEN has default timeout."""
        handler = GracefulShutdown()
        assert handler.timeout == 30

    def test_init_custom_timeout(self):
        """GIVEN custom timeout WHEN creating handler THEN uses it."""
        handler = GracefulShutdown(timeout=60)
        assert handler.timeout == 60

    def test_should_shutdown_initially_false(self):
        """GIVEN new handler WHEN checking THEN should_shutdown is False."""
        handler = GracefulShutdown()
        assert handler.should_shutdown is False

    def test_register_worker(self):
        """GIVEN handler WHEN registering worker THEN tracks PID."""
        handler = GracefulShutdown()
        handler.register_worker(12345)

        assert 12345 in handler.worker_pids

    def test_unregister_worker(self):
        """GIVEN registered worker WHEN unregistering THEN removes PID."""
        handler = GracefulShutdown()
        handler.register_worker(12345)
        handler.unregister_worker(12345)

        assert 12345 not in handler.worker_pids

    def test_unregister_nonexistent_worker(self):
        """GIVEN no worker WHEN unregistering THEN no error."""
        handler = GracefulShutdown()
        handler.unregister_worker(99999)  # Should not raise

    def test_add_cleanup_callback(self):
        """GIVEN callback WHEN adding THEN stored for later."""
        handler = GracefulShutdown()
        callback_called = []

        def my_callback():
            callback_called.append(True)

        handler.add_cleanup_callback(my_callback)
        handler.run_cleanup()

        assert len(callback_called) == 1

    def test_multiple_cleanup_callbacks(self):
        """GIVEN multiple callbacks WHEN running cleanup THEN all called."""
        handler = GracefulShutdown()
        results = []

        handler.add_cleanup_callback(lambda: results.append(1))
        handler.add_cleanup_callback(lambda: results.append(2))
        handler.add_cleanup_callback(lambda: results.append(3))

        handler.run_cleanup()

        assert results == [1, 2, 3]

    def test_cleanup_callback_error_handled(self):
        """GIVEN failing callback WHEN running cleanup THEN continues."""
        handler = GracefulShutdown()
        results = []

        handler.add_cleanup_callback(lambda: results.append(1))
        handler.add_cleanup_callback(lambda: (_ for _ in ()).throw(RuntimeError("fail")))
        handler.add_cleanup_callback(lambda: results.append(3))

        # Should not raise, should continue with other callbacks
        handler.run_cleanup()

        assert 1 in results
        assert 3 in results

    def test_shutdown_workers_no_workers(self):
        """GIVEN no workers WHEN shutting down THEN returns 0."""
        handler = GracefulShutdown()
        force_killed = handler.shutdown_workers()
        assert force_killed == 0


class TestSignalHandlers:
    """Tests for signal handler management."""

    def test_install_handlers(self):
        """GIVEN handler WHEN installing THEN saves original handlers."""
        handler = GracefulShutdown()
        handler.install_handlers()

        assert signal.SIGINT in handler._original_handlers
        assert signal.SIGTERM in handler._original_handlers

        # Cleanup
        handler.restore_handlers()

    def test_restore_handlers(self):
        """GIVEN installed handlers WHEN restoring THEN clears saved."""
        handler = GracefulShutdown()
        handler.install_handlers()
        handler.restore_handlers()

        assert len(handler._original_handlers) == 0


class TestModuleFunctions:
    """Tests for module-level functions."""

    def test_get_shutdown_handler_returns_singleton(self):
        """GIVEN multiple calls WHEN getting handler THEN returns same instance."""
        # Note: This test may interfere with other tests using global handler
        handler1 = get_shutdown_handler()
        handler2 = get_shutdown_handler()

        assert handler1 is handler2

    def test_should_shutdown_uses_global_handler(self):
        """GIVEN global handler WHEN checking should_shutdown THEN uses it."""
        handler = get_shutdown_handler()
        handler.should_shutdown = False

        assert should_shutdown() is False

        handler.should_shutdown = True
        assert should_shutdown() is True

        # Reset for other tests
        handler.should_shutdown = False

    def test_request_shutdown_sets_flag(self):
        """GIVEN handler WHEN requesting shutdown THEN sets flag."""
        handler = get_shutdown_handler()
        handler.should_shutdown = False

        request_shutdown()

        assert handler.should_shutdown is True

        # Reset for other tests
        handler.should_shutdown = False


class TestModuleImports:
    """Tests for module imports."""

    def test_can_import_from_utils(self):
        """GIVEN shutdown module WHEN importing from utils THEN succeeds."""
        from scripts.utils import (
            GracefulShutdown,
            get_shutdown_handler,
            should_shutdown,
            request_shutdown,
            WorkerProcess,
            cleanup_lock_files,
        )

        assert GracefulShutdown is not None
        assert callable(get_shutdown_handler)
        assert callable(should_shutdown)
        assert callable(request_shutdown)
        assert WorkerProcess is not None
        assert callable(cleanup_lock_files)
