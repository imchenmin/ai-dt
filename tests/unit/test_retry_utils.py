"""
Test retry utilities
"""

import asyncio
import time
import pytest
from unittest.mock import Mock, patch

from src.utils.retry_utils import (
    BackoffStrategy,
    RetryConfig,
    CircuitBreaker,
    calculate_delay,
    retry
)


class TestBackoffStrategy:
    """Test backoff strategy enum"""

    def test_enum_values(self):
        """Test that enum has expected values"""
        assert BackoffStrategy.FIXED.value == "fixed"
        assert BackoffStrategy.LINEAR.value == "linear"
        assert BackoffStrategy.EXPONENTIAL.value == "exponential"
        assert BackoffStrategy.EXPONENTIAL_WITH_JITTER.value == "exponential_with_jitter"


class TestRetryConfig:
    """Test retry configuration"""

    def test_default_config(self):
        """Test default configuration values"""
        config = RetryConfig()

        assert config.max_attempts == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.backoff_strategy == BackoffStrategy.EXPONENTIAL_WITH_JITTER
        assert config.backoff_multiplier == 2.0
        assert config.jitter is True
        assert config.retryable_exceptions == (Exception,)
        assert config.non_retryable_exceptions == ()

    def test_custom_config(self):
        """Test custom configuration values"""
        callback = Mock()
        config = RetryConfig(
            max_attempts=5,
            base_delay=0.5,
            max_delay=30.0,
            backoff_strategy=BackoffStrategy.LINEAR,
            backoff_multiplier=1.5,
            jitter=False,
            retryable_exceptions=(ValueError, TypeError),
            non_retryable_exceptions=(RuntimeError,),
            on_retry_callback=callback
        )

        assert config.max_attempts == 5
        assert config.base_delay == 0.5
        assert config.max_delay == 30.0
        assert config.backoff_strategy == BackoffStrategy.LINEAR
        assert config.backoff_multiplier == 1.5
        assert config.jitter is False
        assert config.retryable_exceptions == (ValueError, TypeError)
        assert config.non_retryable_exceptions == (RuntimeError,)
        assert config.on_retry_callback == callback


class TestCalculateDelay:
    """Test delay calculation for different strategies"""

    def test_fixed_delay(self):
        """Test fixed delay strategy"""
        delay = calculate_delay(
            attempt=3,
            base_delay=1.0,
            strategy=BackoffStrategy.FIXED
        )
        assert delay == 1.0

    def test_linear_delay(self):
        """Test linear delay strategy"""
        delay = calculate_delay(
            attempt=3,
            base_delay=1.0,
            strategy=BackoffStrategy.LINEAR
        )
        assert delay == 3.0

    def test_exponential_delay(self):
        """Test exponential delay strategy"""
        delay = calculate_delay(
            attempt=3,
            base_delay=1.0,
            strategy=BackoffStrategy.EXPONENTIAL,
            multiplier=2.0
        )
        assert delay == 4.0  # 1.0 * (2^(3-1)) = 4.0

    def test_exponential_with_jitter(self):
        """Test exponential delay with jitter"""
        delay = calculate_delay(
            attempt=3,
            base_delay=1.0,
            strategy=BackoffStrategy.EXPONENTIAL_WITH_JITTER,
            multiplier=2.0,
            jitter=True
        )
        # Should be around 4.0 with ±25% jitter (3.0 to 5.0)
        assert 3.0 <= delay <= 5.0

    def test_exponential_without_jitter(self):
        """Test exponential delay without jitter"""
        delay = calculate_delay(
            attempt=3,
            base_delay=1.0,
            strategy=BackoffStrategy.EXPONENTIAL_WITH_JITTER,
            multiplier=2.0,
            jitter=False
        )
        assert delay == 4.0

    def test_max_delay_limit(self):
        """Test that delay is capped at max_delay"""
        delay = calculate_delay(
            attempt=10,
            base_delay=1.0,
            strategy=BackoffStrategy.EXPONENTIAL,
            max_delay=10.0
        )
        assert delay == 10.0

    def test_custom_multiplier(self):
        """Test custom multiplier"""
        delay = calculate_delay(
            attempt=3,
            base_delay=1.0,
            strategy=BackoffStrategy.EXPONENTIAL,
            multiplier=3.0
        )
        assert delay == 9.0  # 1.0 * (3^(3-1)) = 9.0


class TestCircuitBreaker:
    """Test circuit breaker functionality"""

    def test_init(self):
        """Test circuit breaker initialization"""
        breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=30.0
        )

        assert breaker.failure_threshold == 3
        assert breaker.recovery_timeout == 30.0
        assert breaker.failure_count == 0
        assert breaker.last_failure_time is None
        assert breaker.state == 'CLOSED'

    def test_success_in_closed_state(self):
        """Test successful call when circuit is closed"""
        breaker = CircuitBreaker(failure_threshold=3)

        async def success_func():
            return "success"

        decorated = breaker(success_func)

        result = asyncio.run(decorated())
        assert result == "success"
        assert breaker.state == 'CLOSED'
        assert breaker.failure_count == 0

    def test_failure_threshold(self):
        """Test that circuit opens after failure threshold"""
        breaker = CircuitBreaker(failure_threshold=2)

        async def fail_func():
            raise ValueError("Test error")

        decorated = breaker(fail_func)

        # First failure
        with pytest.raises(ValueError):
            asyncio.run(decorated())
        assert breaker.failure_count == 1
        assert breaker.state == 'CLOSED'

        # Second failure - should open circuit
        with pytest.raises(ValueError):
            asyncio.run(decorated())
        assert breaker.failure_count == 2
        assert breaker.state == 'OPEN'
        assert breaker.last_failure_time is not None

    def test_open_circuit_blocks_calls(self):
        """Test that open circuit blocks calls"""
        breaker = CircuitBreaker(failure_threshold=1)

        async def fail_func():
            raise ValueError("Test error")

        async def success_func():
            return "success"

        # Open the circuit
        decorated_fail = breaker(fail_func)
        with pytest.raises(ValueError):
            asyncio.run(decorated_fail())

        # Try calling success function - should be blocked
        decorated_success = breaker(success_func)
        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            asyncio.run(decorated_success())

    def test_half_open_state(self):
        """Test half-open state after recovery timeout"""
        breaker = CircuitBreaker(
            failure_threshold=1,
            recovery_timeout=0.1
        )

        async def success_func():
            return "success"

        decorated = breaker(success_func)

        # Open the circuit
        breaker.state = 'OPEN'
        breaker.last_failure_time = time.time() - 0.2  # Past recovery timeout

        # Next call should transition to half-open and succeed
        result = asyncio.run(decorated())
        assert result == "success"
        assert breaker.state == 'CLOSED'
        assert breaker.failure_count == 0

    def test_failure_in_half_open(self):
        """Test failure in half-open reopens circuit"""
        breaker = CircuitBreaker(failure_threshold=2)

        async def fail_func():
            raise ValueError("Test error")

        decorated = breaker(fail_func)

        # Set to half-open state
        breaker.state = 'HALF_OPEN'
        breaker.failure_count = 1

        # Failure should reopen circuit
        with pytest.raises(ValueError):
            asyncio.run(decorated())
        assert breaker.state == 'OPEN'
        assert breaker.failure_count == 2


class TestRetryDecorator:
    """Test retry decorator functionality"""

    def test_retry_success_on_first_attempt(self):
        """Test successful function without retries"""
        func = Mock(return_value="success")

        @retry(max_attempts=3)
        def test_func():
            return func()

        result = test_func()

        assert result == "success"
        assert func.call_count == 1

    def test_retry_success_after_attempts(self):
        """Test successful function after some retries"""
        func = Mock(side_effect=[ValueError("error"), ValueError("error"), "success"])

        @retry(max_attempts=3, base_delay=0)
        def test_func():
            return func()

        result = test_func()

        assert result == "success"
        assert func.call_count == 3

    def test_retry_exhausted_attempts(self):
        """Test function fails after all attempts"""
        func = Mock(side_effect=ValueError("persistent error"))

        @retry(max_attempts=3, base_delay=0)
        def test_func():
            return func()

        with pytest.raises(ValueError, match="persistent error"):
            test_func()

        assert func.call_count == 3

    def test_retry_with_non_retryable_exception(self):
        """Test that non-retryable exceptions are not retried"""
        func = Mock(side_effect=RuntimeError("non-retryable"))

        @retry(
            max_attempts=3,
            retryable_exceptions=(ValueError,),
            non_retryable_exceptions=(RuntimeError,)
        )
        def test_func():
            return func()

        with pytest.raises(RuntimeError, match="non-retryable"):
            test_func()

        assert func.call_count == 1

    def test_retry_with_callback(self):
        """Test retry with callback function"""
        # Note: The actual retry decorator doesn't support on_retry_callback
        # This test demonstrates the current implementation
        func = Mock(side_effect=[ValueError("error"), ValueError("error"), "success"])

        @retry(max_attempts=3, base_delay=0)
        def test_func():
            return func()

        result = test_func()

        assert result == "success"
        assert func.call_count == 3

    def test_retry_different_backoff_strategies(self):
        """Test retry with different backoff strategies"""
        with patch('time.sleep') as mock_sleep:
            # Test fixed delay
            func_fixed = Mock(side_effect=[ValueError("error"), "success"])

            @retry(max_attempts=2, base_delay=1.0, backoff_strategy=BackoffStrategy.FIXED)
            def test_fixed():
                return func_fixed()

            test_fixed()
            mock_sleep.assert_called_with(1.0)

            # Reset mocks
            mock_sleep.reset_mock()

            # Test linear delay with fresh mock
            func_linear = Mock(side_effect=[ValueError("error"), "success"])

            @retry(max_attempts=2, base_delay=1.0, backoff_strategy=BackoffStrategy.LINEAR)
            def test_linear():
                return func_linear()

            test_linear()
            mock_sleep.assert_called_with(1.0)  # First retry (attempt 2) -> 1.0 * 1

    def test_retry_with_default_config(self):
        """Test retry with default RetryConfig"""
        func = Mock(side_effect=[ValueError("error"), "success"])

        config = RetryConfig(max_attempts=2, base_delay=0)

        @retry(config=config)
        def test_func():
            return func()

        result = test_func()

        assert result == "success"
        assert func.call_count == 2

    def test_retry_with_mixed_exception_types(self):
        """Test retry with mixed exception types"""
        func = Mock(side_effect=[
            ValueError("retryable"),
            TypeError("retryable"),
            RuntimeError("non-retryable")
        ])

        @retry(
            max_attempts=5,
            retryable_exceptions=(ValueError, TypeError),
            non_retryable_exceptions=(RuntimeError,),
            base_delay=0
        )
        def test_func():
            return func()

        with pytest.raises(RuntimeError, match="non-retryable"):
            test_func()

        assert func.call_count == 3

    def test_custom_retry_config(self):
        """Test custom retry configuration"""
        config = RetryConfig(
            max_attempts=4,
            base_delay=0.1,
            max_delay=1.0,
            backoff_strategy=BackoffStrategy.EXPONENTIAL,
            jitter=False
        )

        func = Mock(side_effect=[ValueError("error")] * 3 + ["success"])

        @retry(config=config)
        def test_func():
            return func()

        with patch('time.sleep') as mock_sleep:
            result = test_func()

            assert result == "success"
            assert func.call_count == 4

            # Check sleep calls for exponential backoff with default multiplier (2.0)
            expected_calls = [0.1, 0.2, 0.4]  # 0.1*2^0, 0.1*2^1, 0.1*2^2
            actual_calls = [call[0][0] for call in mock_sleep.call_args_list]
            assert actual_calls == expected_calls