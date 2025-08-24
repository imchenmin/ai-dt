"""
Unit tests for LLM client error handling integration.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import openai
import requests

from src.generator.llm_client import LLMClient
from src.utils.error_handling import LLMError, ErrorCategory


class TestLLMClientErrorHandling(unittest.TestCase):
    """Test LLM client error handling integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = LLMClient(provider="openai", api_key="test_key", max_retries=2)
        
    @patch('src.generator.llm_client.OpenAI')
    def test_client_initialization_with_retry_config(self, mock_openai):
        """Test LLMClient initialization with retry configuration."""
        client = LLMClient(
            provider="openai", 
            api_key="test_key",
            max_retries=5,
            retry_delay=2.0
        )
        
        self.assertEqual(client.max_retries, 5)
        self.assertEqual(client.retry_delay, 2.0)
        self.assertIsNotNone(client.error_handler)
        self.assertEqual(client.error_handler.max_retries, 5)
        self.assertEqual(client.error_handler.initial_delay, 2.0)
    
    @patch('src.generator.llm_client.OpenAI')
    @patch('src.utils.prompt_templates.PromptTemplates.get_system_prompt')
    @patch('src.utils.error_handling.ErrorHandler.with_retry')
    def test_generate_test_success(self, mock_with_retry, mock_get_prompt, mock_openai):
        """Test successful test generation."""
        mock_get_prompt.return_value = "System prompt"
        
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Test code"))]
        mock_response.usage = Mock(prompt_tokens=100, completion_tokens=50, total_tokens=150)
        
        mock_client_instance = Mock()
        mock_client_instance.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client_instance
        
        # Mock the error handler to return the successful response directly
        mock_with_retry.return_value = {
            'success': True,
            'test_code': 'Test code',
            'usage': {'prompt_tokens': 100, 'completion_tokens': 50, 'total_tokens': 150},
            'model': 'gpt-3.5-turbo'
        }
        
        result = self.client.generate_test("Test prompt", language="c")
        
        self.assertTrue(result['success'])
        self.assertEqual(result['test_code'], "Test code")
        self.assertEqual(result['usage']['prompt_tokens'], 100)
        self.assertEqual(result['model'], "gpt-3.5-turbo")
    
    @patch('src.generator.llm_client.OpenAI')
    @patch('src.utils.prompt_templates.PromptTemplates.get_system_prompt')
    @patch('src.utils.error_handling.ErrorHandler.with_retry')
    def test_generate_test_with_retry_handler(self, mock_with_retry, mock_get_prompt, mock_openai):
        """Test that generate_test uses the error handler."""
        mock_get_prompt.return_value = "System prompt"
        
        # Mock successful response from error handler
        mock_with_retry.return_value = {
            'success': True,
            'test_code': 'Test code',
            'usage': {'prompt_tokens': 100, 'completion_tokens': 50},
            'model': 'gpt-3.5-turbo'
        }
        
        result = self.client.generate_test("Test prompt", language="c")
        
        self.assertTrue(result['success'])
        mock_with_retry.assert_called_once()
        
        # Verify the call includes all expected parameters
        call_args = mock_with_retry.call_args
        self.assertEqual(call_args[0][1], "test generation")  # operation_name
        self.assertEqual(call_args[0][2], "openai")  # provider
        self.assertEqual(call_args[1]['prompt'], "Test prompt")
        self.assertEqual(call_args[1]['language'], "c")
    
    @patch('src.generator.llm_client.OpenAI')
    @patch('src.utils.error_handling.ErrorHandler.with_retry')
    def test_generate_test_llm_error(self, mock_with_retry, mock_openai):
        """Test handling of LLMError from error handler."""
        # Mock LLMError from error handler
        llm_error = LLMError(
            message="Rate limit exceeded",
            category=ErrorCategory.RATE_LIMIT,
            provider="openai",
            retryable=True
        )
        mock_with_retry.side_effect = llm_error
        
        result = self.client.generate_test("Test prompt")
        
        # LLMError.to_dict() format (no 'success' key)
        self.assertEqual(result['category'], "rate_limit")
        self.assertEqual(result['provider'], "openai")
        self.assertTrue(result['retryable'])
        self.assertEqual(result['message'], "Rate limit exceeded")
    
    @patch('src.generator.llm_client.OpenAI')
    @patch('src.utils.error_handling.ErrorHandler.with_retry')
    def test_generate_test_unexpected_error(self, mock_with_retry, mock_openai):
        """Test handling of unexpected errors."""
        # Mock unexpected error from error handler
        mock_with_retry.side_effect = ValueError("Unexpected error")
        
        result = self.client.generate_test("Test prompt")
        
        # handle_llm_error() format (with 'success' key)
        self.assertFalse(result['success'])
        self.assertIn("Unexpected error", result['error'])
        self.assertEqual(result['error_category'], "unknown")
        self.assertEqual(result['provider'], "openai")
        self.assertFalse(result['retryable'])
    
    @patch('src.generator.llm_client.OpenAI')
    @patch('src.utils.prompt_templates.PromptTemplates.get_system_prompt')
    def test_direct_openai_error(self, mock_get_prompt, mock_openai):
        """Test direct OpenAI API error (without retry wrapper)."""
        mock_get_prompt.return_value = "System prompt"
        
        # Mock OpenAI client to raise error directly
        mock_client_instance = Mock()
        mock_client_instance.chat.completions.create.side_effect = Exception("Rate limit exceeded for model")
        mock_openai.return_value = mock_client_instance
        
        # Create client with 0 retries to test direct error handling
        client = LLMClient(provider="openai", api_key="test_key", max_retries=0)
        
        result = client.generate_test("Test prompt")
        
        # LLMError converted to dict doesn't have 'success' key, check error category instead
        self.assertEqual(result['category'], "rate_limit")
        self.assertTrue(result['retryable'])
        self.assertIn("Rate limit", result['message'])
    
    def test_deepseek_provider_error_handling(self):
        """Test error handling for DeepSeek provider."""
        client = LLMClient(provider="deepseek", api_key="test_key", max_retries=0)
        
        # Mock the client instance to raise error (DeepSeek uses OpenAI-compatible API)
        mock_client_instance = Mock()
        mock_client_instance.chat.completions.create.side_effect = Exception("Invalid API key provided")
        client.client = mock_client_instance
        
        result = client.generate_test("Test prompt")
        
        # LLMError converted to dict doesn't have 'success' key, check error category instead
        self.assertEqual(result['category'], "authentication")
        self.assertEqual(result['provider'], "deepseek")
        self.assertFalse(result['retryable'])
        self.assertIn("Authentication failed", result['message'])
    
    def test_unsupported_provider(self):
        """Test error handling for unsupported provider."""
        client = LLMClient(provider="invalid", api_key="test_key")
        
        result = client.generate_test("Test prompt")
        
        self.assertFalse(result['success'])
        self.assertIn("Unsupported provider", result['error'])
        # The error gets classified as authentication because it contains "invalid"
        self.assertEqual(result['error_category'], "authentication")
        self.assertFalse(result['retryable'])


if __name__ == '__main__':
    unittest.main()