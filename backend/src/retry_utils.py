"""
Retry utilities for handling transient failures in API calls.

This module provides decorator-based retry logic with exponential backoff
for handling transient network and API errors.
"""

import asyncio
import functools
import time
from typing import Callable, TypeVar, Any, Type, Tuple
import aiohttp

T = TypeVar("T")


class RetryConfig:
    """Configuration for retry behavior"""

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 10.0,
        exponential_base: float = 2.0,
        retry_exceptions: Tuple[Type[Exception], ...] = (
            asyncio.TimeoutError,
            aiohttp.ClientError,
        ),
    ):
        """
        Initialize retry configuration.

        Args:
            max_attempts: Maximum number of retry attempts (default: 3)
            base_delay: Initial delay between retries in seconds (default: 1.0)
            max_delay: Maximum delay between retries in seconds (default: 10.0)
            exponential_base: Base for exponential backoff calculation (default: 2.0)
            retry_exceptions: Tuple of exception types to retry on
        """
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.retry_exceptions = retry_exceptions


def async_retry(config: RetryConfig = None):
    """
    Decorator to add retry logic with exponential backoff to async functions.

    Usage:
        @async_retry(RetryConfig(max_attempts=3))
        async def my_api_call():
            ...

    Args:
        config: RetryConfig instance. If None, uses default config.
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(1, config.max_attempts + 1):
                try:
                    return await func(*args, **kwargs)

                except config.retry_exceptions as e:
                    last_exception = e
                    exception_name = type(e).__name__

                    if attempt == config.max_attempts:
                        # Last attempt - raise the error
                        print(
                            f"⚠️ Retry failed after {config.max_attempts} attempts: {exception_name}"
                        )
                        raise

                    # Calculate delay with exponential backoff
                    delay = min(
                        config.base_delay * (config.exponential_base ** (attempt - 1)),
                        config.max_delay,
                    )

                    print(
                        f"⚠️ Attempt {attempt}/{config.max_attempts} failed with {exception_name}. "
                        f"Retrying in {delay:.1f}s..."
                    )

                    await asyncio.sleep(delay)

                except Exception as e:
                    # Non-retryable exception - raise immediately
                    exception_name = type(e).__name__
                    print(f"❌ Non-retryable error: {exception_name}")
                    raise

            # Should never reach here, but just in case
            if last_exception:
                raise last_exception

        return wrapper

    return decorator


class CircuitBreaker:
    """
    Circuit breaker pattern implementation to prevent cascading failures.

    States:
        - CLOSED: Normal operation, requests pass through
        - OPEN: Failure threshold exceeded, requests fail immediately
        - HALF_OPEN: Testing if service recovered, limited requests allowed
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        success_threshold: int = 2,
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Time in seconds before attempting recovery
            success_threshold: Number of successes needed to close circuit
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold

        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def should_allow_request(self) -> bool:
        """Check if request should be allowed based on circuit state"""
        if self.state == "CLOSED":
            return True

        if self.state == "OPEN":
            # Check if recovery timeout has elapsed
            if (
                self.last_failure_time
                and time.time() - self.last_failure_time >= self.recovery_timeout
            ):
                self.state = "HALF_OPEN"
                self.success_count = 0
                print("🔄 Circuit breaker transitioning to HALF_OPEN state")
                return True
            return False

        if self.state == "HALF_OPEN":
            # Allow limited requests to test recovery
            return True

        return False

    def record_success(self):
        """Record a successful request"""
        if self.state == "HALF_OPEN":
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = "CLOSED"
                self.failure_count = 0
                print("✅ Circuit breaker closed - service recovered")
        elif self.state == "CLOSED":
            # Reset failure count on success
            self.failure_count = 0

    def record_failure(self):
        """Record a failed request"""
        self.last_failure_time = time.time()

        if self.state == "HALF_OPEN":
            # Failed during recovery - reopen circuit
            self.state = "OPEN"
            self.failure_count = self.failure_threshold
            print("❌ Circuit breaker reopened - service still failing")
        else:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                print(
                    f"⚠️ Circuit breaker opened after {self.failure_count} failures"
                )


def circuit_breaker(breaker: CircuitBreaker):
    """
    Decorator to add circuit breaker pattern to async functions.

    Usage:
        my_breaker = CircuitBreaker()

        @circuit_breaker(my_breaker)
        async def my_api_call():
            ...

    Args:
        breaker: CircuitBreaker instance
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if not breaker.should_allow_request():
                raise Exception(
                    f"Circuit breaker is OPEN - service temporarily unavailable"
                )

            try:
                result = await func(*args, **kwargs)
                breaker.record_success()
                return result
            except Exception as e:
                breaker.record_failure()
                raise

        return wrapper

    return decorator


# Example usage configurations

# Conservative retry - fewer attempts, faster failure
CONSERVATIVE_RETRY = RetryConfig(
    max_attempts=2,
    base_delay=0.5,
    max_delay=5.0,
)

# Standard retry - balanced approach
STANDARD_RETRY = RetryConfig(
    max_attempts=3,
    base_delay=1.0,
    max_delay=10.0,
)

# Aggressive retry - more attempts, longer delays
AGGRESSIVE_RETRY = RetryConfig(
    max_attempts=5,
    base_delay=1.0,
    max_delay=30.0,
)

# Streaming-specific retry - retry only initial connection
STREAMING_RETRY = RetryConfig(
    max_attempts=2,
    base_delay=0.5,
    max_delay=3.0,
    retry_exceptions=(aiohttp.ClientConnectionError,),  # Don't retry timeouts mid-stream
)

