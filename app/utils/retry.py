"""Retry utilities for handling transient failures in API calls and service operations."""

import time
import functools
import logging
from typing import Tuple, Type

logger = logging.getLogger(__name__)


class MaxRetriesExceeded(Exception):
    """Raised when all retry attempts are exhausted."""
    pass


def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0,
          exceptions: Tuple[Type[Exception], ...] = (Exception,)):
    """
    Decorator that retries a function on failure with exponential backoff.

    Args:
        max_attempts: Total number of attempts (1 = no retry).
        delay:        Initial wait time in seconds before the first retry.
        backoff:      Multiplier applied to `delay` after each retry.
        exceptions:   Exception types that trigger a retry.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exc = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt < max_attempts:
                        logger.warning(
                            "[retry] %s attempt %d/%d failed: %s — retrying in %.1fs",
                            func.__name__, attempt, max_attempts, exc, current_delay,
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            "[retry] %s exhausted after %d attempts: %s",
                            func.__name__, max_attempts, exc,
                        )
            raise MaxRetriesExceeded(
                f"{func.__name__} failed after {max_attempts} attempts: {last_exc}"
            ) from last_exc
        return wrapper
    return decorator


def retry_call(fn, *args, max_attempts: int = 3, delay: float = 1.0,
               backoff: float = 2.0,
               exceptions: Tuple[Type[Exception], ...] = (Exception,),
               **kwargs):
    """
    Call a callable with retry/backoff without using the decorator.
    Useful for retrying lambdas or third-party callables.
    """
    current_delay = delay
    last_exc = None
    for attempt in range(1, max_attempts + 1):
        try:
            return fn(*args, **kwargs)
        except exceptions as exc:
            last_exc = exc
            if attempt < max_attempts:
                logger.warning(
                    "[retry_call] attempt %d/%d failed: %s — retrying in %.1fs",
                    attempt, max_attempts, exc, current_delay,
                )
                time.sleep(current_delay)
                current_delay *= backoff
    raise MaxRetriesExceeded(
        f"Function failed after {max_attempts} attempts: {last_exc}"
    ) from last_exc
