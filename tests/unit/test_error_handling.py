"""
Unit tests for comprehensive error handling system.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import time
import openai
import requests

from src.utils.error_handling import (
    ErrorCategory,
    LLMError,
    ErrorHandler,
    handle_llm_error
)


class TestErrorCategory(unittest.TestCase):
    """Test ErrorCategory enum functionality."""
    
    def test_error_category_values(self):
        """Test that error categories have correct values."""
        self.assertEqual(ErrorCategory.AUTHENTICATION.value, "authentication")
        self.assertEqual(ErrorCategory.RATE_LIMIT.value, "rate_limit")
        self.assertEqual(ErrorCategory.NETWORK.value, "network")
        self.assertEqual(ErrorCategory.TIMEOUT.value, "timeout")
        self.assertEqual(ErrorCategory.CONTENT.value, "content")
        self.assertEqual(ErrorCategory.CONFIGURATION.value, "configuration")
        self.assertEqual(ErrorCategory.PROVIDER.value, "provider")
        self.assertEqual(ErrorCategory.UNKNOWN.value, "unknown")


class TestLLMError(unittest.TestCase):
    """Test LLMError exception functionality."""
    
    def test_llm_error_creation(self):
        """Test LLMError creation with all parameters."""
        original_error = ValueError("Test error")
        error = LLMError(
            message="Test message",
            category=ErrorCategory.NETWORK,
            provider="openai",
            original_error=original_error,
            retryable=True,
            retry_after=5
        )
        
        self.assertEqual(error.message, "Test message")
        self.assertEqual(error.category, ErrorCategory.NETWORK)
        self.assertEqual(error.provider, "openai")
        self.assertEqual(error.original_error, original_error)
        self.assertTrue(error.retryable)
        self.assertEqual(error.retry_after, 5)
    
    def test_llm_error_to_dict(self):
        """Test LLMError to_dict conversion."""
        original_error = ConnectionError("Connection failed")
        error = LLMError(
            message="Network error",
            category=ErrorCategory.NETWORK,
            provider="deepseek",
            original_error=original_error,
            retryable=True
        )
        
        result = error.to_dict()
        
        self.assertEqual(result['message'], "Network error")
        self.assertEqual(result['category'], "network")
        self.assertEqual(result['provider'], "deepseek")
        self.assertTrue(result['retryable'])
        self.assertIsNone(result['retry_after'])
        self.assertEqual(result['original_error'], "Connection failed")
    
    def test_llm_error_inheritance(self):
        """Test that LLMError inherits from Exception."""
        error = LLMError(
            message="Test",
            category=ErrorCategory.UNKNOWN,
            provider="test"
        )
        
        self.assertIsInstance(error, Exception)
        self.assertEqual(str(error), "Test")


class TestErrorHandler(unittest.TestCase):
    """Test ErrorHandler functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.handler = ErrorHandler(max_retries=2, initial_delay=0.1)
    
    def test_successful_execution(self):
        """Test successful execution without retries."""
        mock_func = Mock(return_value="success")
        
        result = self.handler.with_retry(
            mock_func, "test operation", "openai", arg1="test"
        )
        
        self.assertEqual(result, "success")
        mock_func.assert_called_once_with(arg1="test")
    
    def test_retry_on_retryable_error(self):
        """Test retry mechanism for retryable errors."""
        mock_func = Mock()
        mock_func.side_effect = [
            Exception("Rate limit exceeded"),
            "success"
        ]
        
        start_time = time.time()
        result = self.handler.with_retry(mock_func, "test operation", "openai")
        end_time = time.time()
        
        self.assertEqual(result, "success")
        self.assertEqual(mock_func.call_count, 2)
        # Should have delayed between retries
        self.assertGreater(end_time - start_time, 0.09)
    
    def test_max_retries_exceeded(self):
        """Test behavior when max retries are exceeded."""
        mock_func = Mock()
        mock_func.side_effect = Exception("Rate limit exceeded")
        
        with self.assertRaises(LLMError) as context:
            self.handler.with_retry(mock_func, "test operation", "openai")
        
        error = context.exception
        self.assertEqual(mock_func.call_count, 3)  # Initial + 2 retries
        self.assertEqual(error.category, ErrorCategory.RATE_LIMIT)
        self.assertTrue(error.retryable)
    
    def test_non_retryable_error(self):
        """Test that non-retryable errors are not retried."""
        mock_func = Mock()
        mock_func.side_effect = Exception("Invalid API key provided")
        
        with self.assertRaises(LLMError) as context:
            self.handler.with_retry(mock_func, "test operation", "openai")
        
        error = context.exception
        self.assertEqual(mock_func.call_count, 1)  # No retries for auth errors
        self.assertEqual(error.category, ErrorCategory.AUTHENTICATION)
        self.assertFalse(error.retryable)
    
    @patch('time.sleep')
    def test_exponential_backoff(self, mock_sleep):
        """Test exponential backoff timing."""
        handler = ErrorHandler(max_retries=3, initial_delay=1.0, backoff_factor=2.0)
        mock_func = Mock()
        mock_func.side_effect = Exception("Rate limit exceeded")
        
        with self.assertRaises(LLMError):
            handler.with_retry(mock_func, "test operation", "openai")
        
        # Should have slept with exponential backoff: 1s, 2s, 4s
        expected_calls = [
            unittest.mock.call(1.0),  # First retry
            unittest.mock.call(2.0),  # Second retry  
            unittest.mock.call(4.0)   # Third retry
        ]
        mock_sleep.assert_has_calls(expected_calls)
    
    def test_error_classification_openai(self):
        """Test OpenAI error classification."""
        # Authentication error
        auth_error = Exception("Invalid API key provided")
        result = self.handler._classify_error(auth_error, "openai")
        self.assertEqual(result['category'], ErrorCategory.AUTHENTICATION)
        self.assertFalse(result['retryable'])
        
        # Rate limit error
        rate_error = Exception("Rate limit exceeded for model")
        result = self.handler._classify_error(rate_error, "openai")
        self.assertEqual(result['category'], ErrorCategory.RATE_LIMIT)
        self.assertTrue(result['retryable'])
        
        # API error
        api_error = Exception("API server error 500")
        result = self.handler._classify_error(api_error, "openai")
        self.assertEqual(result['category'], ErrorCategory.PROVIDER)
        self.assertTrue(result['retryable'])
    
    def test_error_classification_network(self):
        """Test network error classification."""
        # Connection error
        conn_error = requests.ConnectionError("Connection failed")
        result = self.handler._classify_error(conn_error, "openai")
        self.assertEqual(result['category'], ErrorCategory.NETWORK)
        self.assertTrue(result['retryable'])
        
        # Timeout error
        timeout_error = requests.Timeout("Request timeout")
        result = self.handler._classify_error(timeout_error, "openai")
        self.assertEqual(result['category'], ErrorCategory.TIMEOUT)  # requests.Timeout is classified as timeout
        self.assertTrue(result['retryable'])
        
        # HTTP 500 error
        http_error = requests.HTTPError("Server error")
        http_error.response = Mock(status_code=500)
        result = self.handler._classify_error(http_error, "openai")
        self.assertEqual(result['category'], ErrorCategory.PROVIDER)
        self.assertTrue(result['retryable'])
        
        # HTTP 400 error
        http_error.response.status_code = 400
        result = self.handler._classify_error(http_error, "openai")
        self.assertEqual(result['category'], ErrorCategory.PROVIDER)
        self.assertFalse(result['retryable'])
    
    def test_unknown_error_classification(self):
        """Test classification of unknown error types."""
        unknown_error = ValueError("Some random error")
        result = self.handler._classify_error(unknown_error, "openai")
        
        self.assertEqual(result['category'], ErrorCategory.UNKNOWN)
        self.assertFalse(result['retryable'])


class TestHandleLLMError(unittest.TestCase):
    """Test handle_llm_error function."""
    
    @patch('src.utils.error_handling.logger')
    def test_handle_llm_error_openai(self, mock_logger):
        """Test handling OpenAI errors."""
        error = Exception("Rate limit exceeded for model")
        
        result = handle_llm_error(error, "openai", "test generation")
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error_category'], "rate_limit")
        self.assertEqual(result['provider'], "openai")
        self.assertTrue(result['retryable'])
        self.assertEqual(result['test_code'], '')
        self.assertEqual(result['usage'], {})
        
        # Should have logged the error
        mock_logger.error.assert_called_once()
    
    @patch('src.utils.error_handling.logger')
    def test_handle_llm_error_network(self, mock_logger):
        """Test handling network errors."""
        error = requests.ConnectionError("Connection failed")
        
        result = handle_llm_error(error, "deepseek", "test generation")
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error_category'], "network")
        self.assertEqual(result['provider'], "deepseek")
        self.assertTrue(result['retryable'])
    
    @patch('src.utils.error_handling.logger')
    def test_handle_llm_error_unknown(self, mock_logger):
        """Test handling unknown errors."""
        error = ValueError("Unexpected error")
        
        result = handle_llm_error(error, "anthropic", "test generation")
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error_category'], "unknown")
        self.assertEqual(result['provider'], "anthropic")
        self.assertFalse(result['retryable'])


if __name__ == '__main__':
    unittest.main()