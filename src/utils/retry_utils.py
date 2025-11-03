"""
Retry utilities with exponential backoff for resilient operations.
"""

import asyncio
import random
import time
from functools import wraps
from typing import (
    Any, Callable, Dict, List, Optional, Type, Union,
    TypeVar, Tuple, Awaitable
)
from dataclasses import dataclass
from enum import Enum

from src.utils.logging_utils import get_logger

logger = get_logger(__name__)

T = TypeVar('T')
R = TypeVar('R')


class BackoffStrategy(Enum):
    """Backoff strategies for retry"""
    FIXED = "fixed"
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    EXPONENTIAL_WITH_JITTER = "exponential_with_jitter"


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_strategy: BackoffStrategy = BackoffStrategy.EXPONENTIAL_WITH_JITTER
    backoff_multiplier: float = 2.0
    jitter: bool = True
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,)
    non_retryable_exceptions: Tuple[Type[Exception], ...] = ()
    on_retry_callback: Optional[Callable[[Exception, int], None]] = None


class CircuitBreaker:
    """Circuit breaker for preventing cascade failures"""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN

        self.logger = get_logger(self.__class__.__name__)

    def __call__(self, func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        """Decorator implementation"""

        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            if self.state == 'OPEN':
                if self._should_attempt_reset():
                    self.state = 'HALF_OPEN'
                    self.logger.info("Circuit breaker entering HALF_OPEN state")
                else:
                    raise Exception("Circuit breaker is OPEN")

            try:
                result = await func(*args, **kwargs)
                self._on_success()
                return result
            except self.expected_exception as e:
                self._on_failure()
                raise

        return wrapper

    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit breaker"""
        return (
            self.last_failure_time and
            time.time() - self.last_failure_time >= self.recovery_timeout
        )

    def _on_success(self):
        """Handle successful call"""
        if self.state == 'HALF_OPEN':
            self.state = 'CLOSED'
            self.logger.info("Circuit breaker reset to CLOSED state")
        self.failure_count = 0

    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'
            self.logger.warning(
                f"Circuit breaker opened after {self.failure_count} failures"
            )


def calculate_delay(
    attempt: int,
    base_delay: float,
    strategy: BackoffStrategy,
    multiplier: float = 2.0,
    max_delay: float = 60.0,
    jitter: bool = True
) -> float:
    """Calculate delay for a given attempt"""

    if strategy == BackoffStrategy.FIXED:
        delay = base_delay
    elif strategy == BackoffStrategy.LINEAR:
        delay = base_delay * attempt
    elif strategy == BackoffStrategy.EXPONENTIAL:
        delay = base_delay * (multiplier ** (attempt - 1))
    elif strategy == BackoffStrategy.EXPONENTIAL_WITH_JITTER:
        exponential_delay = base_delay * (multiplier ** (attempt - 1))
        if jitter:
            # Add jitter: ±25% of the delay
            jitter_range = exponential_delay * 0.25
            delay = exponential_delay + random.uniform(-jitter_range, jitter_range)
        else:
            delay = exponential_delay
    else:
        delay = base_delay

    return min(delay, max_delay)


def retry(
    config: Optional[RetryConfig] = None,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_strategy: BackoffStrategy = BackoffStrategy.EXPONENTIAL_WITH_JITTER,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    non_retryable_exceptions: Tuple[Type[Exception], ...] = ()
):
    """Retry decorator for both sync and async functions"""

    if config is None:
        config = RetryConfig(
            max_attempts=max_attempts,
            base_delay=base_delay,
            max_delay=max_delay,
            backoff_strategy=backoff_strategy,
            retryable_exceptions=retryable_exceptions,
            non_retryable_exceptions=non_retryable_exceptions
        )

    def decorator(func: Callable[..., Union[T, Awaitable[T]]]) -> Callable[..., Union[T, Awaitable[T]]]:
        """Decorator implementation"""

        if asyncio.iscoroutinefunction(func):
            return _async_retry_decorator(func, config)
        else:
            return _sync_retry_decorator(func, config)

    return decorator


def _async_retry_decorator(
    func: Callable[..., Awaitable[T]],
    config: RetryConfig
) -> Callable[..., Awaitable[T]]:
    """Async retry decorator implementation"""

    @wraps(func)
    async def wrapper(*args, **kwargs) -> T:
        last_exception = None

        for attempt in range(1, config.max_attempts + 1):
            try:
                return await func(*args, **kwargs)
            except config.non_retryable_exceptions as e:
                # Don't retry on non-retryable exceptions
                logger.error(f"Non-retryable exception in {func.__name__}: {e}")
                raise
            except config.retryable_exceptions as e:
                last_exception = e

                if attempt == config.max_attempts:
                    logger.error(
                        f"Function {func.__name__} failed after {config.max_attempts} attempts. "
                        f"Last error: {e}"
                    )
                    raise

                # Calculate delay
                delay = calculate_delay(
                    attempt=attempt,
                    base_delay=config.base_delay,
                    strategy=config.backoff_strategy,
                    multiplier=config.backoff_multiplier,
                    max_delay=config.max_delay,
                    jitter=config.jitter
                )

                # Log retry attempt
                logger.warning(
                    f"Attempt {attempt}/{config.max_attempts} failed for {func.__name__}: {e}. "
                    f"Retrying in {delay:.2f}s..."
                )

                # Call retry callback if provided
                if config.on_retry_callback:
                    config.on_retry_callback(e, attempt)

                # Wait before retry
                await asyncio.sleep(delay)

        # This should never be reached
        raise last_exception

    return wrapper


def _sync_retry_decorator(
    func: Callable[..., T],
    config: RetryConfig
) -> Callable[..., T]:
    """Sync retry decorator implementation"""

    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        last_exception = None

        for attempt in range(1, config.max_attempts + 1):
            try:
                return func(*args, **kwargs)
            except config.non_retryable_exceptions as e:
                # Don't retry on non-retryable exceptions
                logger.error(f"Non-retryable exception in {func.__name__}: {e}")
                raise
            except config.retryable_exceptions as e:
                last_exception = e

                if attempt == config.max_attempts:
                    logger.error(
                        f"Function {func.__name__} failed after {config.max_attempts} attempts. "
                        f"Last error: {e}"
                    )
                    raise

                # Calculate delay
                delay = calculate_delay(
                    attempt=attempt,
                    base_delay=config.base_delay,
                    strategy=config.backoff_strategy,
                    multiplier=config.backoff_multiplier,
                    max_delay=config.max_delay,
                    jitter=config.jitter
                )

                # Log retry attempt
                logger.warning(
                    f"Attempt {attempt}/{config.max_attempts} failed for {func.__name__}: {e}. "
                    f"Retrying in {delay:.2f}s..."
                )

                # Call retry callback if provided
                if config.on_retry_callback:
                    config.on_retry_callback(e, attempt)

                # Wait before retry
                time.sleep(delay)

        # This should never be reached
        raise last_exception

    return wrapper


# Predefined retry configurations for common use cases
API_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    base_delay=1.0,
    max_delay=30.0,
    backoff_strategy=BackoffStrategy.EXPONENTIAL_WITH_JITTER,
    retryable_exceptions=(
        ConnectionError,
        TimeoutError,
        # Add API-specific exceptions here
    ),
    non_retryable_exceptions=(
        ValueError,
        PermissionError,
    )
)

LLM_RETRY_CONFIG = RetryConfig(
    max_attempts=5,
    base_delay=2.0,
    max_delay=60.0,
    backoff_strategy=BackoffStrategy.EXPONENTIAL_WITH_JITTER,
    retryable_exceptions=(
        ConnectionError,
        TimeoutError,
        # Add LLM-specific exceptions here
    )
)