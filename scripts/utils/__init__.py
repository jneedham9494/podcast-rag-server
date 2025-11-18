"""
Shared utilities for podcast archive system.
"""

from .validators import (
    validate_podcast_name,
    validate_episode_range,
    validate_file_path,
    validate_url,
    ValidationError,
)

from .retry import (
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

from .shutdown import (
    GracefulShutdown,
    get_shutdown_handler,
    should_shutdown,
    request_shutdown,
    WorkerProcess,
    cleanup_lock_files,
)

__all__ = [
    # Validators
    'validate_podcast_name',
    'validate_episode_range',
    'validate_file_path',
    'validate_url',
    'ValidationError',
    # Retry utilities
    'retry',
    'retry_with_backoff',
    'retry_network',
    'retry_download',
    'retry_api',
    'is_transient_error',
    'TRANSIENT_EXCEPTIONS',
    'TRANSIENT_HTTP_CODES',
    'PERMANENT_HTTP_CODES',
    # Shutdown utilities
    'GracefulShutdown',
    'get_shutdown_handler',
    'should_shutdown',
    'request_shutdown',
    'WorkerProcess',
    'cleanup_lock_files',
]
