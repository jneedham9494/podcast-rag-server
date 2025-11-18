"""
Graceful shutdown utilities for multi-process orchestration.

Provides signal handling and worker coordination for clean shutdowns.
"""

import signal
import time
import os
import subprocess
from typing import Callable, Dict, List, Optional, Set
from loguru import logger


class GracefulShutdown:
    """
    Manages graceful shutdown with signal handling.

    Coordinates shutdown of child workers with configurable timeout.
    """

    def __init__(self, timeout: int = 30):
        """
        Initialize graceful shutdown handler.

        Args:
            timeout: Seconds to wait for workers before force kill (default: 30)
        """
        self.timeout = timeout
        self.should_shutdown = False
        self.worker_pids: Set[int] = set()
        self.cleanup_callbacks: List[Callable[[], None]] = []
        self._original_handlers: Dict[int, Callable] = {}

    def install_handlers(self) -> None:
        """
        Install signal handlers for SIGINT and SIGTERM.

        Call this at the start of your main process.
        """
        # Save original handlers
        self._original_handlers[signal.SIGINT] = signal.getsignal(signal.SIGINT)
        self._original_handlers[signal.SIGTERM] = signal.getsignal(signal.SIGTERM)

        # Install new handlers
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

        logger.info("Graceful shutdown handlers installed")

    def restore_handlers(self) -> None:
        """Restore original signal handlers."""
        for sig, handler in self._original_handlers.items():
            signal.signal(sig, handler)
        self._original_handlers.clear()

    def _handle_signal(self, signum: int, frame) -> None:
        """
        Handle shutdown signal.

        Args:
            signum: Signal number
            frame: Current stack frame
        """
        sig_name = signal.Signals(signum).name
        logger.warning(f"Received {sig_name}, initiating graceful shutdown...")
        self.should_shutdown = True

    def register_worker(self, pid: int) -> None:
        """
        Register a worker process for shutdown coordination.

        Args:
            pid: Process ID of the worker
        """
        self.worker_pids.add(pid)
        logger.debug(f"Registered worker PID {pid}")

    def unregister_worker(self, pid: int) -> None:
        """
        Unregister a worker process.

        Args:
            pid: Process ID to unregister
        """
        self.worker_pids.discard(pid)
        logger.debug(f"Unregistered worker PID {pid}")

    def add_cleanup_callback(self, callback: Callable[[], None]) -> None:
        """
        Add a cleanup callback to run during shutdown.

        Args:
            callback: Function to call during cleanup
        """
        self.cleanup_callbacks.append(callback)

    def shutdown_workers(self) -> int:
        """
        Send SIGTERM to all registered workers and wait for completion.

        Returns:
            Number of workers that had to be force killed
        """
        if not self.worker_pids:
            logger.info("No workers to shut down")
            return 0

        logger.info(f"Shutting down {len(self.worker_pids)} workers...")

        # Send SIGTERM to all workers
        for pid in list(self.worker_pids):
            try:
                os.kill(pid, signal.SIGTERM)
                logger.debug(f"Sent SIGTERM to worker {pid}")
            except ProcessLookupError:
                # Process already terminated
                self.worker_pids.discard(pid)
            except Exception as e:
                logger.warning(f"Failed to send SIGTERM to {pid}: {e}")

        # Wait for workers to terminate
        start_time = time.time()
        force_killed = 0

        while self.worker_pids and (time.time() - start_time) < self.timeout:
            for pid in list(self.worker_pids):
                try:
                    # Check if process is still running
                    result = os.waitpid(pid, os.WNOHANG)
                    if result[0] != 0:
                        # Process terminated
                        self.worker_pids.discard(pid)
                        logger.debug(f"Worker {pid} terminated gracefully")
                except ChildProcessError:
                    # Not our child process, check if it's still running
                    try:
                        os.kill(pid, 0)
                    except ProcessLookupError:
                        self.worker_pids.discard(pid)
                        logger.debug(f"Worker {pid} terminated")
                except Exception as e:
                    logger.warning(f"Error checking worker {pid}: {e}")
                    self.worker_pids.discard(pid)

            if self.worker_pids:
                time.sleep(0.5)

        # Force kill remaining workers
        for pid in list(self.worker_pids):
            try:
                logger.warning(f"Force killing worker {pid}")
                os.kill(pid, signal.SIGKILL)
                force_killed += 1
            except ProcessLookupError:
                pass
            except Exception as e:
                logger.error(f"Failed to kill worker {pid}: {e}")
            finally:
                self.worker_pids.discard(pid)

        if force_killed:
            logger.warning(f"Force killed {force_killed} workers")
        else:
            logger.info("All workers terminated gracefully")

        return force_killed

    def run_cleanup(self) -> None:
        """Run all registered cleanup callbacks."""
        for callback in self.cleanup_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Cleanup callback failed: {e}")

    def shutdown(self) -> None:
        """
        Perform full shutdown sequence.

        1. Signal workers to stop
        2. Wait for workers (with timeout)
        3. Force kill remaining workers
        4. Run cleanup callbacks
        """
        logger.info("Starting shutdown sequence...")

        # Shutdown workers
        self.shutdown_workers()

        # Run cleanup
        self.run_cleanup()

        # Restore signal handlers
        self.restore_handlers()

        logger.info("Shutdown complete")


# Global shutdown handler instance
_shutdown_handler: Optional[GracefulShutdown] = None


def get_shutdown_handler(timeout: int = 30) -> GracefulShutdown:
    """
    Get or create the global shutdown handler.

    Args:
        timeout: Shutdown timeout in seconds

    Returns:
        GracefulShutdown instance
    """
    global _shutdown_handler
    if _shutdown_handler is None:
        _shutdown_handler = GracefulShutdown(timeout)
    return _shutdown_handler


def should_shutdown() -> bool:
    """
    Check if shutdown has been requested.

    Use this in worker loops to check for shutdown.

    Returns:
        True if shutdown requested
    """
    handler = get_shutdown_handler()
    return handler.should_shutdown


def request_shutdown() -> None:
    """
    Request a graceful shutdown.

    Use this to trigger shutdown programmatically.
    """
    handler = get_shutdown_handler()
    handler.should_shutdown = True


class WorkerProcess:
    """
    Context manager for worker processes.

    Automatically registers/unregisters with shutdown handler.
    """

    def __init__(
        self,
        command: List[str],
        shutdown_handler: Optional[GracefulShutdown] = None
    ):
        """
        Initialize worker process.

        Args:
            command: Command to run as subprocess
            shutdown_handler: Shutdown handler to register with
        """
        self.command = command
        self.shutdown_handler = shutdown_handler or get_shutdown_handler()
        self.process: Optional[subprocess.Popen] = None

    def __enter__(self) -> subprocess.Popen:
        """Start the worker process."""
        self.process = subprocess.Popen(
            self.command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        self.shutdown_handler.register_worker(self.process.pid)
        logger.debug(f"Started worker process {self.process.pid}: {' '.join(self.command)}")
        return self.process

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Cleanup worker process."""
        if self.process and self.process.pid:
            self.shutdown_handler.unregister_worker(self.process.pid)
            if self.process.poll() is None:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()


def cleanup_lock_files(lock_dir: str = "episodes") -> None:
    """
    Cleanup lock files on shutdown.

    Args:
        lock_dir: Directory containing lock files
    """
    import glob
    lock_pattern = os.path.join(lock_dir, "**", "*.lock")
    lock_files = glob.glob(lock_pattern, recursive=True)

    for lock_file in lock_files:
        try:
            os.remove(lock_file)
            logger.debug(f"Removed lock file: {lock_file}")
        except Exception as e:
            logger.warning(f"Failed to remove lock file {lock_file}: {e}")

    if lock_files:
        logger.info(f"Cleaned up {len(lock_files)} lock files")
