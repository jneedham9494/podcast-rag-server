"""
Retry utilities with exponential backoff for network operations.
"""

import time
import functools
from typing import Any, Callable, Tuple, Type, TypeVar, Union
from loguru import logger

# Type variable for generic return type
T = TypeVar('T')

# Exceptions that indicate transient errors (should retry)
TRANSIENT_EXCEPTIONS: Tuple[Type[Exception], ...] = (
    ConnectionError,
    TimeoutError,
    ConnectionResetError,
    BrokenPipeError,
)

# HTTP status codes that indicate transient errors
TRANSIENT_HTTP_CODES: Tuple[int, ...] = (
    408,  # Request Timeout
    429,  # Too Many Requests
    500,  # Internal Server Error
    502,  # Bad Gateway
    503,  # Service Unavailable
    504,  # Gateway Timeout
)

# HTTP status codes that should NOT retry (permanent failures)
PERMANENT_HTTP_CODES: Tuple[int, ...] = (
    400,  # Bad Request
    401,  # Unauthorized
    403,  # Forbidden
    404,  # Not Found
    410,  # Gone
    422,  # Unprocessable Entity
)


def is_transient_error(exception: Exception) -> bool:
    """
    Check if an exception represents a transient error that should be retried.

    Args:
        exception: The exception to check

    Returns:
        True if the error is transient and should be retried
    """
    # Check for transient exception types
    if isinstance(exception, TRANSIENT_EXCEPTIONS):
        return True

    # Check for HTTP errors with transient status codes
    # Works with requests.HTTPError and similar
    if hasattr(exception, 'response') and hasattr(exception.response, 'status_code'):
        status_code = exception.response.status_code
        if status_code in TRANSIENT_HTTP_CODES:
            return True
        if status_code in PERMANENT_HTTP_CODES:
            return False

    # Check for OSError with specific error numbers (network-related)
    if isinstance(exception, OSError):
        import errno
        transient_errnos = (
            errno.ECONNRESET,
            errno.ECONNREFUSED,
            errno.ETIMEDOUT,
            errno.EHOSTUNREACH,
            errno.ENETUNREACH,
        )
        if hasattr(exception, 'errno') and exception.errno in transient_errnos:
            return True

    return False


def retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = TRANSIENT_EXCEPTIONS,
    on_retry: Union[Callable[[Exception, int, float], None], None] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator that retries a function with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        base_delay: Initial delay between retries in seconds (default: 1.0)
        max_delay: Maximum delay between retries in seconds (default: 60.0)
        exponential_base: Base for exponential backoff (default: 2.0)
        exceptions: Tuple of exception types to retry on
        on_retry: Optional callback called on each retry with (exception, attempt, delay)

    Returns:
        Decorated function that retries on specified exceptions

    Example:
        @retry(max_retries=3, base_delay=1.0)
        def download_file(url: str) -> bytes:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.content
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception: Exception = Exception("No exception")

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    # Check if it's actually a transient error
                    if not is_transient_error(e) and hasattr(e, 'response'):
                        # Permanent HTTP error - don't retry
                        logger.warning(
                            f"{func.__name__}: Permanent error (not retrying): {e}"
                        )
                        raise

                    if attempt < max_retries:
                        # Calculate delay with exponential backoff
                        delay = min(
                            base_delay * (exponential_base ** attempt),
                            max_delay
                        )

                        logger.warning(
                            f"{func.__name__}: Attempt {attempt + 1}/{max_retries + 1} "
                            f"failed with {type(e).__name__}: {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )

                        # Call optional callback
                        if on_retry:
                            on_retry(e, attempt + 1, delay)

                        time.sleep(delay)
                    else:
                        logger.error(
                            f"{func.__name__}: All {max_retries + 1} attempts failed. "
                            f"Last error: {e}"
                        )

            # All retries exhausted
            raise last_exception

        return wrapper
    return decorator


def retry_with_backoff(
    func: Callable[..., T],
    args: Tuple[Any, ...] = (),
    kwargs: dict = None,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
) -> T:
    """
    Retry a function call with exponential backoff (non-decorator version).

    Args:
        func: Function to call
        args: Positional arguments for the function
        kwargs: Keyword arguments for the function
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds

    Returns:
        Result of the function call

    Raises:
        The last exception if all retries fail

    Example:
        result = retry_with_backoff(
            requests.get,
            args=('https://api.example.com/data',),
            kwargs={'timeout': 30},
            max_retries=3
        )
    """
    if kwargs is None:
        kwargs = {}

    @retry(
        max_retries=max_retries,
        base_delay=base_delay,
        max_delay=max_delay
    )
    def wrapped() -> T:
        return func(*args, **kwargs)

    return wrapped()


# Convenience decorators for common use cases
def retry_network(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator for network operations with sensible defaults.

    Retries 3 times with 1s, 2s, 4s delays.
    """
    return retry(
        max_retries=3,
        base_delay=1.0,
        exponential_base=2.0
    )(func)


def retry_download(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator for download operations with longer timeouts.

    Retries 5 times with 2s, 4s, 8s, 16s, 32s delays.
    """
    return retry(
        max_retries=5,
        base_delay=2.0,
        max_delay=60.0,
        exponential_base=2.0
    )(func)


def retry_api(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator for API calls with shorter initial delay.

    Retries 3 times with 0.5s, 1s, 2s delays.
    """
    return retry(
        max_retries=3,
        base_delay=0.5,
        max_delay=10.0,
        exponential_base=2.0
    )(func)
